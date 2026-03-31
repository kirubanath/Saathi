from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from db.models import User, RecallQueue
from db.operations import schedule_recall, get_due_recalls, update_recall, get_video
from engine.evaluator import EvalResult
from storage.base import get_storage_client


@dataclass
class RecallEntry:
    concept_key: str
    source_video_id: str
    due_at: datetime
    interval_hours: float


@dataclass
class RecallUpdate:
    new_due_at: datetime
    new_interval: float
    status: str


@dataclass
class RecallItem:
    recall_id: int
    concept_key: str
    source_video_id: str
    question: dict
    due_at: datetime
    interval_hours: float


def _base_interval(score: float) -> float:
    if score < 0.4:
        return 18.0
    if score <= 0.6:
        return 30.0
    return 48.0


def schedule_recalls(
    db: Session,
    user: User,
    quiz_results: list[EvalResult],
    source_video_id: str,
    category: str,
    as_of: datetime | None = None,
) -> list[RecallEntry]:
    """Schedule recalls for AS users (warming_up + established) only."""
    if user.user_type != "AS" or user.maturity not in ("warming_up", "established"):
        return []

    now = as_of or datetime.now(timezone.utc)
    knowledge = (user.knowledge_state or {}).get(category, {})
    entries = []

    for result in quiz_results:
        concept_key = f"{category}/{result.concept}"
        score = knowledge.get(result.concept, 0.0)
        interval = _base_interval(score)
        due_at = now + timedelta(hours=interval)

        schedule_recall(
            db, user.user_id, concept_key, source_video_id, due_at, interval
        )
        entries.append(
            RecallEntry(
                concept_key=concept_key,
                source_video_id=source_video_id,
                due_at=due_at,
                interval_hours=interval,
            )
        )

    return entries


def process_recall_result(
    db: Session,
    recall: RecallQueue,
    correct: bool,
) -> RecallUpdate:
    """Adjust interval based on recall result."""
    if correct:
        new_interval = recall.interval_hours * 2
    else:
        new_interval = max(12.0, recall.interval_hours / 2)

    new_due_at = datetime.now(timezone.utc) + timedelta(hours=new_interval)
    status = "completed" if correct else "pending"

    update_recall(db, recall.id, new_due_at, new_interval, status)

    return RecallUpdate(
        new_due_at=new_due_at,
        new_interval=new_interval,
        status=status,
    )


def get_pending_recalls(
    db: Session,
    user_id: str,
    as_of: datetime | None = None,
) -> list[RecallItem]:
    """Get due recalls with a different question than the original quiz."""
    now = as_of or datetime.now(timezone.utc)
    due_recalls = get_due_recalls(db, user_id, now)

    if not due_recalls:
        return []

    storage = get_storage_client()
    items = []

    for recall in due_recalls:
        category, concept = recall.concept_key.split("/", 1)

        # Load questions for this video/concept
        key = f"videos/{recall.source_video_id}/questions.json"
        try:
            questions_data = storage.get_json(key)
        except Exception:
            continue

        concept_questions = questions_data.get(concept)
        if not concept_questions:
            continue

        # Pick a different difficulty than original quiz for variety
        # Prefer medium, then easy, then hard
        for difficulty in ("medium", "easy", "hard"):
            q = concept_questions.get(difficulty)
            if q:
                items.append(
                    RecallItem(
                        recall_id=recall.id,
                        concept_key=recall.concept_key,
                        source_video_id=recall.source_video_id,
                        question=q,
                        due_at=recall.due_at,
                        interval_hours=recall.interval_hours,
                    )
                )
                break

    # Rank by due_at (most overdue first)
    items.sort(key=lambda x: x.due_at)
    return items
