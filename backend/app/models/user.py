from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    skin_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    skin_concerns: Mapped[list | None] = mapped_column(JSONB, default=list)
    allergies: Mapped[list | None] = mapped_column(JSONB, default=list)
    preferences: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    conversations = relationship("Conversation", back_populates="user", lazy="selectin")
