from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import Base
import db.models  # registers all models with Base
from db.models import User, Video, RecallQueue
from db.operations import (
    get_user,
    update_knowledge_state,
    add_watch_history,
    get_due_recalls,
    schedule_recall,
    update_recall,
    get_video,
    get_videos_by_category,
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


def _make_user(db, user_id="u1", user_type="AS", maturity="warming_up", knowledge_state=None):
    user = User(
        user_id=user_id,
        user_type=user_type,
        maturity=maturity,
        knowledge_state=knowledge_state or {},
    )
    db.add(user)
    db.commit()
    return user


def _make_video(db, video_id="vid_001", category="career_and_jobs", content_type="aspiration"):
    video = Video(
        video_id=video_id,
        title="Test Video",
        series_id="series_001",
        series_position=1,
        content_type=content_type,
        category=category,
    )
    db.add(video)
    db.commit()
    return video


# --- get_user ---

def test_get_user_returns_none_for_missing(db):
    assert get_user(db, "nonexistent") is None


def test_get_user_returns_user(db):
    _make_user(db, user_id="u1", user_type="IS")
    user = get_user(db, "u1")
    assert user is not None
    assert user.user_type == "IS"


# --- update_knowledge_state ---

def test_update_knowledge_state_creates_nested_key(db):
    _make_user(db, user_id="u1")
    update_knowledge_state(db, "u1", "career_and_jobs", "body_language", 0.5)
    user = get_user(db, "u1")
    assert user.knowledge_state["career_and_jobs"]["body_language"] == 0.5


def test_update_knowledge_state_preserves_other_keys(db):
    _make_user(db, user_id="u1", knowledge_state={"career_and_jobs": {"voice_modulation": 0.7}})
    update_knowledge_state(db, "u1", "career_and_jobs", "body_language", 0.4)
    user = get_user(db, "u1")
    assert user.knowledge_state["career_and_jobs"]["voice_modulation"] == 0.7
    assert user.knowledge_state["career_and_jobs"]["body_language"] == 0.4


# --- add_watch_history ---

def test_add_watch_history_creates_entry(db):
    _make_user(db, user_id="u1")
    _make_video(db, video_id="vid_001")
    entry = add_watch_history(db, "u1", "vid_001", "career_and_jobs", 1.0, {"body_language": 0.8})
    assert entry.id is not None
    assert entry.user_id == "u1"
    assert entry.video_id == "vid_001"
    assert entry.category == "career_and_jobs"
    assert entry.completion_rate == 1.0
    assert entry.quiz_scores == {"body_language": 0.8}


def test_add_watch_history_increments_total_videos_watched(db):
    _make_user(db, user_id="u1")
    _make_video(db, video_id="vid_001")
    user = get_user(db, "u1")
    user.total_videos_watched = 2
    db.commit()
    add_watch_history(db, "u1", "vid_001", "career_and_jobs", 1.0, {})
    user = get_user(db, "u1")
    assert user.total_videos_watched == 3


# --- get_due_recalls ---

def test_get_due_recalls_empty_when_none(db):
    _make_user(db, user_id="u1")
    result = get_due_recalls(db, "u1", datetime.now(timezone.utc))
    assert result == []


def test_schedule_recall_and_get_due(db):
    _make_user(db, user_id="u1")
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    schedule_recall(db, "u1", "career_and_jobs/body_language", "vid_001", past, 24.0)
    result = get_due_recalls(db, "u1", datetime.now(timezone.utc))
    assert len(result) == 1
    assert result[0].concept_key == "career_and_jobs/body_language"


def test_get_due_recalls_excludes_future(db):
    _make_user(db, user_id="u1")
    future = datetime.now(timezone.utc) + timedelta(hours=24)
    schedule_recall(db, "u1", "career_and_jobs/body_language", "vid_001", future, 24.0)
    result = get_due_recalls(db, "u1", datetime.now(timezone.utc))
    assert result == []


def test_get_due_recalls_excludes_completed_status(db):
    _make_user(db, user_id="u1")
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    entry = schedule_recall(db, "u1", "career_and_jobs/body_language", "vid_001", past, 24.0)
    future = datetime.now(timezone.utc) + timedelta(hours=48)
    update_recall(db, entry.id, future, 48.0, "completed")
    result = get_due_recalls(db, "u1", datetime.now(timezone.utc))
    assert result == []


# --- update_recall ---

def test_update_recall_updates_fields(db):
    _make_user(db, user_id="u1")
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    entry = schedule_recall(db, "u1", "career_and_jobs/body_language", "vid_001", past, 24.0)
    new_due = datetime.now(timezone.utc) + timedelta(hours=48)
    updated = update_recall(db, entry.id, new_due, 48.0, "completed")
    assert updated.interval_hours == 48.0
    assert updated.status == "completed"


# --- get_video ---

def test_get_video_returns_none_for_missing(db):
    assert get_video(db, "bad_id") is None


def test_get_video_returns_video(db):
    _make_video(db, video_id="vid_001", category="career_and_jobs")
    video = get_video(db, "vid_001")
    assert video is not None
    assert video.category == "career_and_jobs"


# --- get_videos_by_category ---

def test_get_videos_by_category_returns_matching(db):
    _make_video(db, video_id="vid_001", category="career_and_jobs")
    _make_video(db, video_id="vid_002", category="career_and_jobs")
    _make_video(db, video_id="vid_006", category="english_speaking")
    result = get_videos_by_category(db, "career_and_jobs")
    assert len(result) == 2
    assert all(v.category == "career_and_jobs" for v in result)
