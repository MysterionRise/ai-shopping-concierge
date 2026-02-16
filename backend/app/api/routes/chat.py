import json
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, WebSocket
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import get_compiled_graph
from app.agents.safety_constraint import OVERRIDE_REFUSAL, check_override_attempt
from app.dependencies import get_db_session
from app.memory.constraint_store import get_hard_constraints, get_soft_preferences
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


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
    logger.info("Chat request", user_id=request.user_id, message=request.message[:100])

    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Check for safety override attempts
    if check_override_attempt(request.message):
        return ChatResponse(
            response=OVERRIDE_REFUSAL,
            conversation_id=conversation_id,
            intent="safety_override_blocked",
        )

    # Load user profile and constraints
    user_profile: dict[str, Any] = {}
    hard_constraints = []
    soft_preferences = []

    try:
        result = await db.execute(select(User).where(User.id == request.user_id))
        user = result.scalar_one_or_none()
        if user:
            user_profile = {
                "display_name": user.display_name,
                "skin_type": user.skin_type,
                "skin_concerns": user.skin_concerns or [],
            }
            hard_constraints = await get_hard_constraints(db, request.user_id)
            soft_preferences = await get_soft_preferences(db, request.user_id)
    except Exception as e:
        logger.warning("Could not load user profile", error=str(e))

    graph = get_compiled_graph()

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
        "persona_scores": {},
        "error": None,
    }

    result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": conversation_id}},
    )

    ai_messages = [m for m in result["messages"] if hasattr(m, "type") and m.type == "ai"]
    response_text = ai_messages[-1].content if ai_messages else "I'm not sure how to respond."

    return ChatResponse(
        response=response_text,
        conversation_id=conversation_id,
        intent=result.get("current_intent", "general_chat"),
        safety_violations=result.get("safety_violations", []),
        product_count=len(result.get("product_results", [])),
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
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
    hard_constraints = []
    soft_preferences = []

    try:
        result = await db.execute(select(User).where(User.id == request.user_id))
        user = result.scalar_one_or_none()
        if user:
            user_profile = {
                "display_name": user.display_name,
                "skin_type": user.skin_type,
                "skin_concerns": user.skin_concerns or [],
            }
            hard_constraints = await get_hard_constraints(db, request.user_id)
            soft_preferences = await get_soft_preferences(db, request.user_id)
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
        "persona_scores": {},
        "error": None,
    }

    async def event_stream():
        graph = get_compiled_graph()
        try:
            async for event in graph.astream_events(
                initial_state,
                config={"configurable": {"thread_id": conversation_id}},
                version="v2",
            ):
                kind = event.get("event", "")
                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.websocket("/chat/ws")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "info", "message": "WebSocket connected — streaming TBD"})
    await websocket.close()
