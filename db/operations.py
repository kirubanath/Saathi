from datetime import datetime, timezone
from sqlalchemy.orm import Session
from db.models import User, WatchHistory, RecallQueue, Video


def get_user(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def update_knowledge_state(
    db: Session, user_id: str, category: str, concept: str, new_score: float
) -> None:
    user = db.get(User, user_id)
    # Reassign a new dict so SQLAlchemy detects the change
    state = {k: dict(v) for k, v in (user.knowledge_state or {}).items()}
    state.setdefault(category, {})[concept] = new_score
    user.knowledge_state = state
    user.last_updated = datetime.now(timezone.utc)
    db.commit()


def add_watch_history(
    db: Session,
    user_id: str,
    video_id: str,
    category: str,
    completion_rate: float,
    quiz_scores: dict,
) -> WatchHistory:
    existing = (
        db.query(WatchHistory)
        .filter_by(user_id=user_id, video_id=video_id)
        .first()
    )
    if existing:
        existing.completion_rate = completion_rate
        existing.quiz_scores = quiz_scores
        existing.watched_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    entry = WatchHistory(
        user_id=user_id,
        video_id=video_id,
        category=category,
        completion_rate=completion_rate,
        quiz_scores=quiz_scores,
    )
    db.add(entry)
    user = db.get(User, user_id)
    user.total_videos_watched = (user.total_videos_watched or 0) + 1
    user.last_updated = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)
    return entry


def get_due_recalls(db: Session, user_id: str, as_of: datetime) -> list[RecallQueue]:
    return (
        db.query(RecallQueue)
        .filter(
            RecallQueue.user_id == user_id,
            RecallQueue.status == "pending",
            RecallQueue.due_at <= as_of,
        )
        .all()
    )


def schedule_recall(
    db: Session,
    user_id: str,
    concept_key: str,
    source_video_id: str,
    due_at: datetime,
    interval_hours: float,
) -> RecallQueue:
    existing = (
        db.query(RecallQueue)
        .filter_by(user_id=user_id, concept_key=concept_key, status="pending")
        .first()
    )
    if existing:
        existing.source_video_id = source_video_id
        existing.due_at = due_at
        existing.interval_hours = interval_hours
        db.commit()
        db.refresh(existing)
        return existing

    entry = RecallQueue(
        user_id=user_id,
        concept_key=concept_key,
        source_video_id=source_video_id,
        due_at=due_at,
        interval_hours=interval_hours,
        status="pending",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_recall(
    db: Session,
    recall_id: int,
    new_due_at: datetime,
    new_interval: float,
    status: str,
) -> RecallQueue:
    entry = db.get(RecallQueue, recall_id)
    entry.due_at = new_due_at
    entry.interval_hours = new_interval
    entry.status = status
    db.commit()
    db.refresh(entry)
    return entry


def get_video(db: Session, video_id: str) -> Video | None:
    return db.get(Video, video_id)


def get_videos_by_category(db: Session, category: str) -> list[Video]:
    return db.query(Video).filter(Video.category == category).all()
