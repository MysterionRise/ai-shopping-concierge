import uuid

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PersonaScore(Base):
    __tablename__ = "persona_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    sycophancy: Mapped[float] = mapped_column(Float, default=0.0)
    hallucination: Mapped[float] = mapped_column(Float, default=0.0)
    over_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    safety_bypass: Mapped[float] = mapped_column(Float, default=0.0)
    sales_pressure: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
