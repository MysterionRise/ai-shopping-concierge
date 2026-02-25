import asyncio
import json
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.safety_constraint import OVERRIDE_REFUSAL, check_override_attempt
from app.config import settings
from app.core.rate_limit import limiter
from app.dependencies import get_db_session, verify_user_ownership
from app.memory.background_extractor import schedule_extraction
from app.memory.constraint_store import get_user_constraints
from app.models.conversation import Conversation, Message
from app.models.user import User

logger = structlog.get_logger()

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    user_id: str = Field(..., pattern=r"^[0-9a-fA-F-]{36}$")
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    intent: str
    safety_violations: list[dict] = []
    product_count: int = 0
    products: list[dict] = []


async def _load_user_context(
    db: AsyncSession, user_id: str
) -> tuple[User | None, dict[str, Any], list[str], list[str], bool]:
    """Load user profile, constraints, and preferences from the database.

    Returns (user, user_profile, hard_constraints, soft_preferences, memory_enabled).
    """
    user_profile: dict[str, Any] = {}
    hard_constraints: list[str] = []
    soft_preferences: list[str] = []
    memory_enabled = True
    user: User | None = None

    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user_profile = {
                "display_name": user.display_name,
                "skin_type": user.skin_type,
                "skin_concerns": user.skin_concerns or [],
            }
            hard_constraints, soft_preferences = get_user_constraints(user)
            memory_enabled = user.memory_enabled
    except Exception as e:
        logger.warning("Could not load user profile", error=str(e))

    return user, user_profile, hard_constraints, soft_preferences, memory_enabled


def _build_initial_state(
    message: str,
    user_id: str,
    conversation_id: str,
    user_profile: dict[str, Any],
    hard_constraints: list[str],
    soft_preferences: list[str],
    memory_enabled: bool,
) -> dict[str, Any]:
    """Build the initial LangGraph state dict."""
    return {
        "messages": [HumanMessage(content=message)],
        "user_id": user_id,
        "conversation_id": conversation_id,
        "user_profile": user_profile,
        "hard_constraints": hard_constraints,
        "soft_preferences": soft_preferences,
        "current_intent": "",
        "product_results": [],
        "safety_check_passed": True,
        "safety_violations": [],
        "memory_context": [],
        "active_constraints": [],
        "memory_notifications": [],
        "memory_enabled": memory_enabled,
        "persona_scores": {},
        "error": None,
    }


async def _persist_conversation(
    db: AsyncSession,
    user: User | None,
    conversation_id: str,
    thread_id: str,
    user_message: str,
    assistant_response: str,
    intent: str = "general_chat",
) -> str | None:
    """Persist user and assistant messages to the conversations table.

    Args:
        conversation_id: The DB primary key UUID of the conversation.
        thread_id: The LangGraph thread_id used for checkpointing.

    Returns:
        The conversation DB id (str) if persisted, else None.
    """
    if not assistant_response or not assistant_response.strip():
        logger.warning("Skipping persistence of empty assistant response")
        return None

    try:
        if user:
            # Look up by conversation DB id first
            conv_result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = conv_result.scalar_one_or_none()

            if not conversation:
                # Fall back: check by langgraph_thread_id for backward compat
                conv_result = await db.execute(
                    select(Conversation).where(Conversation.langgraph_thread_id == thread_id)
                )
                conversation = conv_result.scalar_one_or_none()

            if not conversation:
                conversation = Conversation(
                    user_id=user.id,
                    langgraph_thread_id=thread_id,
                    title=user_message[:100],
                )
                db.add(conversation)
                await db.flush()

            db.add(
                Message(
                    conversation_id=conversation.id,
                    role="user",
                    content=user_message,
                )
            )
            db.add(
                Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=assistant_response,
                    agent_name=intent,
                )
            )
            await db.commit()
            return str(conversation.id)
    except Exception as e:
        logger.warning("Failed to persist conversation", error=str(e))
    return None


@router.post("/chat")
@limiter.limit(lambda: settings.rate_limit_chat)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
    verify_user_ownership(request, chat_request.user_id)
    logger.info("Chat request", user_id=chat_request.user_id, message=chat_request.message[:100])

    conversation_id = chat_request.conversation_id or str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    if check_override_attempt(chat_request.message):
        return ChatResponse(
            response=OVERRIDE_REFUSAL,
            conversation_id=conversation_id,
            intent="safety_override_blocked",
        )

    user, user_profile, hard_constraints, soft_preferences, memory_enabled = (
        await _load_user_context(db, chat_request.user_id)
    )

    graph = request.app.state.graph

    initial_state = _build_initial_state(
        message=chat_request.message,
        user_id=chat_request.user_id,
        conversation_id=conversation_id,
        user_profile=user_profile,
        hard_constraints=hard_constraints,
        soft_preferences=soft_preferences,
        memory_enabled=memory_enabled,
    )

    graph_result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": thread_id}},
    )

    ai_messages = [m for m in graph_result["messages"] if hasattr(m, "type") and m.type == "ai"]
    response_text = ai_messages[-1].content if ai_messages else "I'm not sure how to respond."

    persisted_id = await _persist_conversation(
        db,
        user,
        conversation_id,
        thread_id,
        chat_request.message,
        response_text,
        intent=graph_result.get("current_intent", "general_chat"),
    )
    # Use the DB conversation id if available, otherwise fall back to request id
    resolved_conversation_id = persisted_id or conversation_id

    # Fire-and-forget persona evaluation
    persona_monitor = getattr(request.app.state, "persona_monitor", None)
    if persona_monitor:
        message_id = str(uuid.uuid4())
        try:
            await persona_monitor.evaluate_async(
                chat_request.message, response_text, resolved_conversation_id, message_id
            )
        except Exception as e:
            logger.warning("Persona evaluation failed", error=str(e))

    product_results = graph_result.get("product_results", [])
    return ChatResponse(
        response=response_text,
        conversation_id=resolved_conversation_id,
        intent=graph_result.get("current_intent", "general_chat"),
        safety_violations=graph_result.get("safety_violations", []),
        product_count=len(product_results),
        products=product_results,
    )


@router.post("/chat/stream")
@limiter.limit(lambda: settings.rate_limit_chat)
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """SSE streaming endpoint for chat responses."""
    verify_user_ownership(request, chat_request.user_id)

    if check_override_attempt(chat_request.message):

        async def override_stream():
            yield f"data: {json.dumps({'type': 'token', 'content': OVERRIDE_REFUSAL})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(override_stream(), media_type="text/event-stream")

    conversation_id = chat_request.conversation_id or str(uuid.uuid4())
    thread_id = str(uuid.uuid4())

    user, user_profile, hard_constraints, soft_preferences, memory_enabled = (
        await _load_user_context(db, chat_request.user_id)
    )

    initial_state = _build_initial_state(
        message=chat_request.message,
        user_id=chat_request.user_id,
        conversation_id=conversation_id,
        user_profile=user_profile,
        hard_constraints=hard_constraints,
        soft_preferences=soft_preferences,
        memory_enabled=memory_enabled,
    )

    async def event_stream():
        graph = request.app.state.graph
        config = {"configurable": {"thread_id": thread_id}}
        last_model_content = ""
        stream_errored = False
        product_results: list[dict] = []
        safety_violations: list[dict] = []
        current_intent = "general_chat"
        try:
            async with asyncio.timeout(settings.llm_timeout_seconds):
                async for event in graph.astream_events(
                    initial_state,
                    config=config,
                    version="v2",
                ):
                    if await request.is_disconnected():
                        logger.info(
                            "Client disconnected during stream",
                            conversation_id=conversation_id,
                        )
                        return

                    kind = event.get("event", "")
                    metadata = event.get("metadata", {})
                    node = metadata.get("langgraph_node", "")

                    # Capture intent from triage_router node
                    if kind == "on_chain_end" and node == "triage_router":
                        output = event.get("data", {}).get("output", {})
                        if isinstance(output, dict) and output.get("current_intent"):
                            current_intent = output["current_intent"]

                    # Capture product results from product_discovery node
                    if kind == "on_chain_end" and node == "product_discovery":
                        output = event.get("data", {}).get("output", {})
                        if isinstance(output, dict):
                            product_results = output.get("product_results", [])

                    # Capture safety violations from safety nodes
                    if kind == "on_chain_end" and node in (
                        "safety_pre_filter",
                        "safety_post_validate",
                    ):
                        output = event.get("data", {}).get("output", {})
                        if isinstance(output, dict):
                            violations = output.get("safety_violations", [])
                            if violations:
                                safety_violations = violations

                    # Only stream tokens from the response_synth node
                    is_response = node == "response_synth"
                    if kind == "on_chat_model_stream" and is_response:
                        chunk = event.get("data", {}).get("chunk")
                        if chunk and hasattr(chunk, "content") and chunk.content:
                            last_model_content += chunk.content
                            evt = json.dumps({"type": "token", "content": chunk.content})
                            yield f"data: {evt}\n\n"
                    elif kind == "on_chat_model_end" and is_response:
                        if not last_model_content:
                            output = event.get("data", {}).get("output")
                            if output and hasattr(output, "content") and output.content:
                                content = (
                                    output.content
                                    if isinstance(output.content, str)
                                    else str(output.content)
                                )
                                last_model_content = content
                                evt = json.dumps({"type": "token", "content": content})
                                yield f"data: {evt}\n\n"

            # Emit product results after text streaming completes
            if product_results:
                evt = json.dumps({"type": "products", "products": product_results})
                yield f"data: {evt}\n\n"

        except TimeoutError:
            stream_errored = True
            logger.warning("LLM timeout during stream", conversation_id=conversation_id)
            msg = "Response timed out. Please try again."
            evt = json.dumps({"type": "error", "content": msg})
            yield f"data: {evt}\n\n"
        except Exception as e:
            stream_errored = True
            logger.error("Stream error", error=str(e), conversation_id=conversation_id)
            error_payload = json.dumps(
                {"type": "error", "content": "An error occurred. Please try again."}
            )
            yield f"data: {error_payload}\n\n"

        done_payload: dict[str, Any] = {
            "type": "done",
            "conversation_id": conversation_id,
            "intent": current_intent,
        }
        if safety_violations:
            done_payload["safety_violations"] = safety_violations
        yield f"data: {json.dumps(done_payload)}\n\n"

        # Only persist complete, non-errored responses
        if last_model_content and last_model_content.strip() and not stream_errored:
            persisted_id = await _persist_conversation(
                db,
                user,
                conversation_id,
                thread_id,
                chat_request.message,
                last_model_content,
            )
            if persisted_id:
                conversation_id_for_eval = persisted_id
            else:
                conversation_id_for_eval = conversation_id
        else:
            conversation_id_for_eval = conversation_id

        # Fire-and-forget persona evaluation
        persona_monitor = getattr(request.app.state, "persona_monitor", None)
        if persona_monitor and last_model_content and not stream_errored:
            message_id = str(uuid.uuid4())
            try:
                await persona_monitor.evaluate_async(
                    chat_request.message,
                    last_model_content,
                    conversation_id_for_eval,
                    message_id,
                )
            except Exception as e:
                logger.warning("Persona evaluation failed", error=str(e))

        # Schedule background memory extraction
        store = getattr(request.app.state, "store", None)
        stream_messages = [
            {"role": "user", "content": chat_request.message},
        ]
        if last_model_content and not stream_errored:
            stream_messages.append({"role": "assistant", "content": last_model_content})
        schedule_extraction(
            conversation_id,
            chat_request.user_id,
            stream_messages,
            store,
            delay_seconds=30,
            memory_enabled=memory_enabled,
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
