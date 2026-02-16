import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db_session
from app.models.conversation import Conversation, Message

logger = structlog.get_logger()

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    langgraph_thread_id: str
    title: str | None
    created_at: str

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    agent_name: str | None
    created_at: str

    model_config = {"from_attributes": True}


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    )
    result = await db.execute(stmt)
    conversations = result.scalars().all()

    return [
        ConversationResponse(
            id=str(c.id),
            user_id=str(c.user_id),
            langgraph_thread_id=c.langgraph_thread_id,
            title=c.title,
            created_at=c.created_at.isoformat() if c.created_at else "",
        )
        for c in conversations
    ]


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    return [
        MessageResponse(
            id=str(m.id),
            role=m.role,
            content=m.content,
            agent_name=m.agent_name,
            created_at=m.created_at.isoformat() if m.created_at else "",
        )
        for m in messages
    ]
