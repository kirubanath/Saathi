from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import Base
from db.models import User, RecallQueue
from db.operations import schedule_recall
from engine.evaluator import EvalResult
from engine.recall_scheduler import (
    schedule_recalls,
    process_recall_result,
    _base_interval,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _make_user(db, user_id="priya", user_type="AS", maturity="warming_up", knowledge_state=None):
    user = User(
        user_id=user_id, user_type=user_type, maturity=maturity,
        knowledge_state=knowledge_state or {},
    )
    db.add(user)
    db.commit()
    return user


# --- base interval ---

def test_base_interval_low_score():
    assert _base_interval(0.2) == 18.0

def test_base_interval_mid_score():
    assert _base_interval(0.5) == 30.0

def test_base_interval_high_score():
    assert _base_interval(0.7) == 48.0

def test_base_interval_boundary_04():
    assert _base_interval(0.4) == 30.0

def test_base_interval_boundary_06():
    assert _base_interval(0.6) == 30.0


# --- schedule_recalls ---

def test_schedule_recalls_as_warming_up(db):
    user = _make_user(db, user_type="AS", maturity="warming_up", knowledge_state={
        "career_and_jobs": {"body_language": 0.3}
    })
    results = [EvalResult(concept="body_language", correct=True, score=1.0)]
    now = datetime.now(timezone.utc)
    entries = schedule_recalls(db, user, results, "vid_001", "career_and_jobs", as_of=now)

    assert len(entries) == 1
    assert entries[0].concept_key == "career_and_jobs/body_language"
    assert entries[0].interval_hours == 18.0  # score 0.3 < 0.4


def test_schedule_recalls_is_user_skipped(db):
    user = _make_user(db, user_type="IS", maturity="new")
    results = [EvalResult(concept="body_language", correct=True, score=1.0)]
    entries = schedule_recalls(db, user, results, "vid_001", "career_and_jobs")
    assert entries == []


def test_schedule_recalls_as_new_skipped(db):
    user = _make_user(db, user_type="AS", maturity="new")
    results = [EvalResult(concept="body_language", correct=True, score=1.0)]
    entries = schedule_recalls(db, user, results, "vid_001", "career_and_jobs")
    assert entries == []


# --- process_recall_result ---

def test_correct_recall_doubles_interval(db):
    _make_user(db, user_id="priya")
    now = datetime.now(timezone.utc)
    recall = RecallQueue(
        user_id="priya",
        concept_key="career_and_jobs/body_language",
        source_video_id="vid_001",
        due_at=now - timedelta(hours=1),
        interval_hours=18.0,
        status="pending",
    )
    db.add(recall)
    db.commit()

    update = process_recall_result(db, recall, correct=True)
    assert update.new_interval == 36.0
    assert update.status == "completed"


def test_wrong_recall_halves_interval(db):
    _make_user(db, user_id="priya")
    now = datetime.now(timezone.utc)
    recall = RecallQueue(
        user_id="priya",
        concept_key="career_and_jobs/body_language",
        source_video_id="vid_001",
        due_at=now - timedelta(hours=1),
        interval_hours=30.0,
        status="pending",
    )
    db.add(recall)
    db.commit()

    update = process_recall_result(db, recall, correct=False)
    assert update.new_interval == 15.0
    assert update.status == "pending"


def test_wrong_recall_min_12_hours(db):
    _make_user(db, user_id="priya")
    now = datetime.now(timezone.utc)
    recall = RecallQueue(
        user_id="priya",
        concept_key="career_and_jobs/body_language",
        source_video_id="vid_001",
        due_at=now - timedelta(hours=1),
        interval_hours=18.0,
        status="pending",
    )
    db.add(recall)
    db.commit()

    update = process_recall_result(db, recall, correct=False)
    # 18 / 2 = 9, but min is 12
    assert update.new_interval == 12.0
