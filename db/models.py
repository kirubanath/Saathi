from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    user_type: Mapped[str] = mapped_column(String, default="IS")
    maturity: Mapped[str] = mapped_column(String, default="new")
    knowledge_state: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    watch_history: Mapped[list["WatchHistory"]] = relationship(back_populates="user")
    recall_queue: Mapped[list["RecallQueue"]] = relationship(back_populates="user")


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    series_id: Mapped[str] = mapped_column(String, nullable=False)
    series_name: Mapped[str] = mapped_column(String, nullable=False)
    series_position: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    concept_ids: Mapped[list] = mapped_column(JSON, default=list)
    preprocessing_done: Mapped[bool] = mapped_column(Boolean, default=False)

    watch_history: Mapped[list["WatchHistory"]] = relationship(back_populates="video")
    recall_queue: Mapped[list["RecallQueue"]] = relationship(back_populates="video")


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    video_id: Mapped[str] = mapped_column(String, ForeignKey("videos.id"), nullable=False)
    watched_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completion_rate: Mapped[float] = mapped_column(Float, default=1.0)
    quiz_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    concepts_quizzed: Mapped[list] = mapped_column(JSON, default=list)

    user: Mapped["User"] = relationship(back_populates="watch_history")
    video: Mapped["Video"] = relationship(back_populates="watch_history")


class RecallQueue(Base):
    __tablename__ = "recall_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    video_id: Mapped[str] = mapped_column(String, ForeignKey("videos.id"), nullable=False)
    concept: Mapped[str] = mapped_column(String, nullable=False)
    question_id: Mapped[str] = mapped_column(String, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="recall_queue")
    video: Mapped["Video"] = relationship(back_populates="recall_queue")
