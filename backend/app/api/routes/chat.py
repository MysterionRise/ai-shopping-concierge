import asyncio
import json
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.safety_constraint import OVERRIDE_REFUSAL, check_override_attempt
from app.config import settings
from app.dependencies import get_db_session
from app.memory.constraint_store import get_user_constraints
from app.models.conversation import Conversation, Message
from app.models.user import User

logger = structlog.get_logger()

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    user_id: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    intent: str
    safety_violations: list[dict] = []
    product_count: int = 0
    products: list[dict] = []


@router.post("/chat")
async def chat(
    request: ChatRequest,
    raw_request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
    logger.info("Chat request", user_id=request.user_id, message=request.message[:100])

    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Check for safety override attempts (only when context suggests override)
    if check_override_attempt(request.message):
        return ChatResponse(
            response=OVERRIDE_REFUSAL,
            conversation_id=conversation_id,
            intent="safety_override_blocked",
        )

    # Load user profile and constraints in a single query
    user_profile: dict[str, Any] = {}
    hard_constraints: list[str] = []
    soft_preferences: list[str] = []
    user: User | None = None

    try:
        result = await db.execute(select(User).where(User.id == request.user_id))
        user = result.scalar_one_or_none()
        if user:
            user_profile = {
                "display_name": user.display_name,
                "skin_type": user.skin_type,
                "skin_concerns": user.skin_concerns or [],
            }
            hard_constraints, soft_preferences = get_user_constraints(user)
    except Exception as e:
        logger.warning("Could not load user profile", error=str(e))

    graph = raw_request.app.state.graph

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "user_id": request.user_id,
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
        "persona_scores": {},
        "error": None,
    }

    graph_result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": conversation_id}},
    )

    ai_messages = [m for m in graph_result["messages"] if hasattr(m, "type") and m.type == "ai"]
    response_text = ai_messages[-1].content if ai_messages else "I'm not sure how to respond."

    # Persist conversation and messages to DB
    try:
        if user:
            # Find or create conversation
            conv_result = await db.execute(
                select(Conversation).where(Conversation.langgraph_thread_id == conversation_id)
            )
            conversation = conv_result.scalar_one_or_none()
            if not conversation:
                conversation = Conversation(
                    user_id=user.id,
                    langgraph_thread_id=conversation_id,
                    title=request.message[:100],
                )
                db.add(conversation)
                await db.flush()

            # Save user message
            db.add(
                Message(
                    conversation_id=conversation.id,
                    role="user",
                    content=request.message,
                )
            )
            # Save assistant message
            db.add(
                Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=response_text,
                    agent_name=graph_result.get("current_intent", "general_chat"),
                )
            )
            await db.commit()
    except Exception as e:
        logger.warning("Failed to persist conversation", error=str(e))

    product_results = graph_result.get("product_results", [])
    return ChatResponse(
        response=response_text,
        conversation_id=conversation_id,
        intent=graph_result.get("current_intent", "general_chat"),
        safety_violations=graph_result.get("safety_violations", []),
        product_count=len(product_results),
        products=product_results,
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    raw_request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """SSE streaming endpoint for chat responses."""

    if check_override_attempt(request.message):

        async def override_stream():
            yield f"data: {json.dumps({'type': 'token', 'content': OVERRIDE_REFUSAL})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(override_stream(), media_type="text/event-stream")

    conversation_id = request.conversation_id or str(uuid.uuid4())

    user_profile: dict[str, Any] = {}
    hard_constraints: list[str] = []
    soft_preferences: list[str] = []

    try:
        result = await db.execute(select(User).where(User.id == request.user_id))
        user = result.scalar_one_or_none()
        if user:
            user_profile = {
                "display_name": user.display_name,
                "skin_type": user.skin_type,
                "skin_concerns": user.skin_concerns or [],
            }
            hard_constraints, soft_preferences = get_user_constraints(user)
    except Exception as e:
        logger.debug("Could not load user profile for streaming", error=str(e))

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "user_id": request.user_id,
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
        "persona_scores": {},
        "error": None,
    }

    async def event_stream():
        graph = raw_request.app.state.graph
        config = {"configurable": {"thread_id": conversation_id}}
        last_model_content = ""
        product_results: list[dict] = []
        try:
            async with asyncio.timeout(settings.llm_timeout_seconds):
                async for event in graph.astream_events(
                    initial_state,
                    config=config,
                    version="v2",
                ):
                    if await raw_request.is_disconnected():
                        logger.info(
                            "Client disconnected during stream",
                            conversation_id=conversation_id,
                        )
                        return

                    kind = event.get("event", "")
                    metadata = event.get("metadata", {})
                    node = metadata.get("langgraph_node", "")

                    # Capture product results from product_discovery node
                    if kind == "on_chain_end" and node == "product_discovery":
                        output = event.get("data", {}).get("output", {})
                        if isinstance(output, dict):
                            product_results = output.get("product_results", [])

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
                                evt = json.dumps({"type": "token", "content": content})
                                yield f"data: {evt}\n\n"

            # Emit product results after text streaming completes
            if product_results:
                evt = json.dumps({"type": "products", "products": product_results})
                yield f"data: {evt}\n\n"

        except TimeoutError:
            logger.warning("LLM timeout during stream", conversation_id=conversation_id)
            msg = "Response timed out. Please try again."
            evt = json.dumps({"type": "error", "content": msg})
            yield f"data: {evt}\n\n"
        except Exception as e:
            logger.error("Stream error", error=str(e), conversation_id=conversation_id)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
