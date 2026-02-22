import json

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.dependencies import get_redis
from app.persona.monitor import PersonaMonitor

logger = structlog.get_logger()

router = APIRouter(prefix="/persona", tags=["persona"])


def _get_monitor(request: Request) -> PersonaMonitor:
    """Return the shared PersonaMonitor from app lifespan state."""
    monitor: PersonaMonitor | None = getattr(request.app.state, "persona_monitor", None)
    if monitor is None:
        raise RuntimeError("PersonaMonitor not initialized")
    return monitor


@router.get("/scores")
async def get_scores(
    conversation_id: str,
    message_id: str,
    request: Request,
):
    monitor = _get_monitor(request)
    return await monitor.get_scores(conversation_id, message_id)


@router.get("/history")
async def get_history(
    conversation_id: str,
    request: Request,
):
    monitor = _get_monitor(request)
    return await monitor.get_history(conversation_id)


@router.get("/alerts")
async def get_alerts(
    conversation_id: str,
    request: Request,
):
    monitor = _get_monitor(request)
    return await monitor.get_alerts(conversation_id)


@router.get("/stream")
async def persona_stream(conversation_id: str, redis=Depends(get_redis)):
    """SSE stream for real-time persona score updates."""

    async def event_stream():
        pubsub = redis.pubsub()
        channel = f"persona:{conversation_id}"

        try:
            await pubsub.subscribe(channel)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    yield f"data: {data}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
