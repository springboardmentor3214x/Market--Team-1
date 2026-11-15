"""Database models: User and ResearchHistory (one user -> many history entries)."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    history: Mapped[list["ResearchHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ResearchHistory(Base):
    __tablename__ = "research_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    query: Mapped[str] = mapped_column(Text)
    market: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    analysis_period: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    user: Mapped["User"] = relationship(back_populates="history")
