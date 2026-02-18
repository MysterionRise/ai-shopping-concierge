from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PersonaScore(TimestampMixin, Base):
    __tablename__ = "persona_scores"

    conversation_id: Mapped[str] = mapped_column(String(255), nullable=False)
    message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    sycophancy: Mapped[float] = mapped_column(Float, default=0.0)
    hallucination: Mapped[float] = mapped_column(Float, default=0.0)
    over_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    safety_bypass: Mapped[float] = mapped_column(Float, default=0.0)
    sales_pressure: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
