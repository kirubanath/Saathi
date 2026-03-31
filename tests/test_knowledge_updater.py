import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import Base
from db.models import User, Video
from engine.knowledge_updater import update_from_watch, update_from_quiz, update_from_recall
from engine.evaluator import EvalResult


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _make_user(db, user_id="priya", knowledge_state=None):
    user = User(
        user_id=user_id, user_type="AS", maturity="warming_up",
        knowledge_state=knowledge_state or {},
    )
    db.add(user)
    db.commit()
    return user


# --- update_from_watch ---

def test_watch_update_basic(db):
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.3, "handling_nervousness": 0.2}
    })
    concept_profile = {"body_language": 0.85, "handling_nervousness": 0.7}
    result = update_from_watch(db, user, "career_and_jobs", concept_profile, 1.0)

    # body_language: min(0.8, 0.3 + 0.1 * 1.0 * 0.85) = min(0.8, 0.385) = 0.385
    assert abs(result.updated_state["body_language"] - 0.385) < 0.001
    # handling_nervousness: min(0.8, 0.2 + 0.1 * 1.0 * 0.7) = min(0.8, 0.27) = 0.27
    assert abs(result.updated_state["handling_nervousness"] - 0.27) < 0.001


def test_watch_update_caps_at_08(db):
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.78}
    })
    concept_profile = {"body_language": 0.9}
    result = update_from_watch(db, user, "career_and_jobs", concept_profile, 1.0)

    # min(0.8, 0.78 + 0.1 * 1.0 * 0.9) = min(0.8, 0.87) = 0.8
    assert result.updated_state["body_language"] == 0.8


def test_watch_update_completion_rate_scales(db):
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.0}
    })
    concept_profile = {"body_language": 1.0}
    result = update_from_watch(db, user, "career_and_jobs", concept_profile, 0.5)

    # min(0.8, 0.0 + 0.1 * 0.5 * 1.0) = 0.05
    assert abs(result.updated_state["body_language"] - 0.05) < 0.001


def test_watch_update_new_concept(db):
    user = _make_user(db, knowledge_state={})
    concept_profile = {"body_language": 0.85}
    result = update_from_watch(db, user, "career_and_jobs", concept_profile, 1.0)

    # min(0.8, 0.0 + 0.1 * 1.0 * 0.85) = 0.085
    assert abs(result.updated_state["body_language"] - 0.085) < 0.001


def test_watch_update_persists_to_db(db):
    user = _make_user(db, knowledge_state={})
    concept_profile = {"body_language": 0.85}
    update_from_watch(db, user, "career_and_jobs", concept_profile, 1.0)

    db.refresh(user)
    assert abs(user.knowledge_state["career_and_jobs"]["body_language"] - 0.085) < 0.001


# --- update_from_quiz ---

def test_quiz_update_correct(db):
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.385}
    })
    results = [EvalResult(concept="body_language", correct=True, score=1.0)]
    update = update_from_quiz(db, user, "career_and_jobs", results)

    # 0.385 + 0.3 * (1.0 - 0.385) = 0.385 + 0.1845 = 0.5695
    assert abs(update.updated_state["body_language"] - 0.5695) < 0.001


def test_quiz_update_incorrect(db):
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.385}
    })
    results = [EvalResult(concept="body_language", correct=False, score=0.0)]
    update = update_from_quiz(db, user, "career_and_jobs", results)

    # 0.385 + 0.3 * (0.0 - 0.385) = 0.385 - 0.1155 = 0.2695
    assert abs(update.updated_state["body_language"] - 0.2695) < 0.001


def test_quiz_update_uses_alpha_03(db):
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.5}
    })
    results = [EvalResult(concept="body_language", correct=True, score=1.0)]
    update = update_from_quiz(db, user, "career_and_jobs", results)

    # 0.5 + 0.3 * (1.0 - 0.5) = 0.5 + 0.15 = 0.65
    assert abs(update.updated_state["body_language"] - 0.65) < 0.001


def test_quiz_update_delta_tracked(db):
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.3}
    })
    results = [EvalResult(concept="body_language", correct=True, score=1.0)]
    update = update_from_quiz(db, user, "career_and_jobs", results)

    assert update.delta["body_language"]["before"] == 0.3
    assert abs(update.delta["body_language"]["after"] - 0.51) < 0.001


# --- update_from_recall ---

def test_recall_update_correct(db):
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.5}
    })
    update = update_from_recall(db, user, "career_and_jobs/body_language", 1.0)

    # 0.5 + 0.15 * (1.0 - 0.5) = 0.5 + 0.075 = 0.575
    assert abs(update.updated_state["body_language"] - 0.575) < 0.001


def test_recall_update_uses_alpha_015(db):
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.4}
    })
    update = update_from_recall(db, user, "career_and_jobs/body_language", 0.0)

    # 0.4 + 0.15 * (0.0 - 0.4) = 0.4 - 0.06 = 0.34
    assert abs(update.updated_state["body_language"] - 0.34) < 0.001


def test_scores_never_exceed_1(db):
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.95}
    })
    results = [EvalResult(concept="body_language", correct=True, score=1.0)]
    update = update_from_quiz(db, user, "career_and_jobs", results)
    assert update.updated_state["body_language"] <= 1.0


def test_scores_never_below_0(db):
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.05}
    })
    results = [EvalResult(concept="body_language", correct=False, score=0.0)]
    update = update_from_quiz(db, user, "career_and_jobs", results)
    assert update.updated_state["body_language"] >= 0.0
