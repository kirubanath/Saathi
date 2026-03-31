from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_type: Mapped[str] = mapped_column(String, default="IS")
    maturity: Mapped[str] = mapped_column(String, default="new")
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_videos_watched: Mapped[int] = mapped_column(Integer, default=0)
    knowledge_state: Mapped[dict] = mapped_column(JSON, default=dict)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    watch_history: Mapped[list["WatchHistory"]] = relationship(back_populates="user")
    recall_queue: Mapped[list["RecallQueue"]] = relationship(back_populates="user")


class Video(Base):
    __tablename__ = "videos"

    video_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    series_id: Mapped[str | None] = mapped_column(String, nullable=True)
    series_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    preprocessed: Mapped[bool] = mapped_column(Boolean, default=False)

    watch_history: Mapped[list["WatchHistory"]] = relationship(back_populates="video")


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id"), nullable=False)
    video_id: Mapped[str] = mapped_column(String, ForeignKey("videos.video_id"), nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    completion_rate: Mapped[float] = mapped_column(Float, default=1.0)
    quiz_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    watched_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="watch_history")
    video: Mapped["Video"] = relationship(back_populates="watch_history")


class RecallQueue(Base):
    __tablename__ = "recall_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.user_id"), nullable=False)
    concept_key: Mapped[str] = mapped_column(String, nullable=False)
    source_video_id: Mapped[str] = mapped_column(String, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval_hours: Mapped[float] = mapped_column(Float, default=24.0)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="recall_queue")
