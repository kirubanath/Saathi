"""API endpoint tests using FastAPI TestClient with in-memory DB and mock storage."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.app import app
from db.base import Base, get_db
from db.models import User, Video, RecallQueue


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(db_engine, db_session):
    def override_get_db():
        session = sessionmaker(bind=db_engine)()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _seed_all(db):
    priya = User(
        user_id="priya", user_type="AS", maturity="warming_up",
        total_videos_watched=8,
        knowledge_state={
            "career_and_jobs": {
                "body_language": 0.3,
                "answering_structure": 0.25,
                "voice_modulation": 0.7,
            }
        },
    )
    rahul = User(
        user_id="rahul", user_type="IS", maturity="new",
        total_videos_watched=2, knowledge_state={},
    )
    db.add_all([priya, rahul])

    videos = [
        Video(video_id="vid_001", title="Body Language in Interviews",
              content_type="aspiration", category="career_and_jobs",
              series_id="series_cj_001", series_position=1, preprocessed=True),
        Video(video_id="vid_002", title="Answering Questions with Structure",
              content_type="aspiration", category="career_and_jobs",
              series_id="series_cj_001", series_position=2, preprocessed=True),
        Video(video_id="vid_003", title="Voice and Confidence Under Pressure",
              content_type="aspiration", category="career_and_jobs",
              series_id="series_cj_001", series_position=3, preprocessed=True),
        Video(video_id="vid_004", title="Resume Tips That Actually Work",
              content_type="aspiration", category="career_and_jobs",
              series_id="series_cj_002", series_position=1, preprocessed=True),
        Video(video_id="vid_006", title="Pronunciation That Gets You Heard",
              content_type="aspiration", category="english_speaking",
              series_id="series_es_001", series_position=1, preprocessed=True),
        Video(video_id="vid_008", title="How to Get Your PAN Card",
              content_type="utility", category="sarkari_kaam",
              series_id="series_sk_001", series_position=1),
        Video(video_id="vid_009", title="How to Link Aadhaar to Your Phone",
              content_type="utility", category="sarkari_kaam",
              series_id="series_sk_001", series_position=2),
        Video(video_id="vid_010", title="How T20 Scoring Works",
              content_type="entertainment", category="cricket",
              series_id="series_cr_001", series_position=1),
    ]
    db.add_all(videos)
    db.commit()


def _mock_storage():
    mock = MagicMock()
    artifacts = {
        "videos/vid_001/concept_profile.json": {
            "body_language": 0.85,
            "handling_nervousness": 0.7,
            "voice_modulation": 0.15,
            "answering_structure": 0.1,
            "preparation": 0.05,
        },
        "videos/vid_001/recap_bullets.json": {
            "body_language": {
                "IS": "The video explains how body language creates first impressions in interviews.",
                "AS": "Your body language is a skill you can build. This video shows how posture and eye contact signal confidence.",
            },
            "handling_nervousness": {
                "IS": "The video covers breathing techniques to manage interview nervousness.",
                "AS": "Learning to manage nervousness is part of your growth. Deep breathing and preparation are your tools.",
            },
        },
        "videos/vid_001/questions.json": {
            "body_language": {
                "easy": {
                    "question": "What did the video say about maintaining eye contact?",
                    "options": ["Avoid it", "Keep it steady", "Look down", "Close eyes"],
                    "correct_index": 1,
                },
                "medium": {
                    "question": "How does posture affect an interviewer's perception?",
                    "options": ["No effect", "Signals confidence", "Signals boredom", "Signals anger"],
                    "correct_index": 1,
                },
                "hard": {
                    "question": "How do body language and verbal cues work together?",
                    "options": ["They conflict", "They reinforce", "No relation", "Only verbal matters"],
                    "correct_index": 1,
                },
            },
            "handling_nervousness": {
                "easy": {
                    "question": "What breathing technique was recommended?",
                    "options": ["Hold breath", "Deep slow breaths", "Fast breaths", "No technique"],
                    "correct_index": 1,
                },
                "medium": {
                    "question": "Why does preparation reduce nervousness?",
                    "options": ["It does not", "Builds familiarity", "Makes you tired", "Wastes time"],
                    "correct_index": 1,
                },
                "hard": {
                    "question": "How does controlled nervousness improve performance?",
                    "options": ["It does not", "Sharpens focus", "Causes mistakes", "Slows thinking"],
                    "correct_index": 1,
                },
            },
        },
        "videos/vid_004/concept_profile.json": {
            "preparation": 0.9, "answering_structure": 0.5,
            "body_language": 0.1, "voice_modulation": 0.1, "handling_nervousness": 0.1,
        },
        "videos/vid_006/concept_profile.json": {
            "pronunciation": 0.8, "fluency": 0.7, "vocabulary": 0.2, "grammar": 0.1,
        },
    }
    mock.get_json.side_effect = lambda key: artifacts.get(key, {})
    return mock


# --- Health check ---

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- Journey 1: Priya (AS) full flow via HTTP ---

def test_journey1_session_start_no_recalls(client, db_session):
    _seed_all(db_session)
    storage = _mock_storage()

    with patch("engine.recall_scheduler.get_storage_client", return_value=storage):
        resp = client.post("/session/start", json={"user_id": "priya"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["recalls"] == []
    assert data["milestones"] == []


def test_journey1_video_complete(client, db_session):
    _seed_all(db_session)
    storage = _mock_storage()

    with patch("engine.loop.get_storage_client", return_value=storage), \
         patch("engine.recommender.get_storage_client", return_value=storage):
        resp = client.post("/video/complete", json={
            "user_id": "priya",
            "video_id": "vid_001",
            "completion_rate": 1.0,
        })

    assert resp.status_code == 200
    data = resp.json()

    # Classification
    assert data["classification"]["content_type"] == "aspiration"
    assert data["classification"]["user_type"] == "AS"
    assert data["classification"]["show_quiz"] is True

    # Recap present
    assert data["recap"] is not None
    assert len(data["recap"]) == 2

    # Questions present (quiz path)
    assert data["questions"] is not None
    assert len(data["questions"]) == 2

    # No recommendation yet (quiz path)
    assert data["recommendation"] is None


def test_journey1_full_flow(client, db_session):
    """Full Journey 1: session/start -> video/complete -> quiz/submit, verify DB state."""
    _seed_all(db_session)
    storage = _mock_storage()

    with patch("engine.loop.get_storage_client", return_value=storage), \
         patch("engine.recommender.get_storage_client", return_value=storage), \
         patch("engine.recall_scheduler.get_storage_client", return_value=storage):

        # Step 1: Session start (no recalls)
        resp = client.post("/session/start", json={"user_id": "priya"})
        assert resp.status_code == 200
        assert resp.json()["recalls"] == []

        # Step 2: Video complete
        resp = client.post("/video/complete", json={
            "user_id": "priya",
            "video_id": "vid_001",
            "completion_rate": 1.0,
        })
        assert resp.status_code == 200
        vc_data = resp.json()
        questions = vc_data["questions"]
        assert len(questions) == 2

        # Step 3: Quiz submit (all correct)
        answers = [
            {"concept": q["concept"], "answer_index": q["correct_index"]}
            for q in questions
        ]
        resp = client.post("/quiz/submit", json={
            "user_id": "priya",
            "video_id": "vid_001",
            "questions": questions,
            "answers": answers,
        })
        assert resp.status_code == 200
        qs_data = resp.json()

        # All correct
        assert all(r["correct"] for r in qs_data["results"])

        # Progress message present (AS user)
        assert qs_data["progress_message"] is not None

        # Recommendation returned
        assert qs_data["recommendation"] is not None
        assert qs_data["recommendation"]["slot1"] is not None
        assert qs_data["recommendation"]["slot1"]["video_id"] == "vid_002"

        # Recalls scheduled (AS warming_up)
        assert qs_data["recalls_scheduled"] > 0

        # Verify DB state: knowledge updated
        user = db_session.get(User, "priya")
        db_session.refresh(user)
        knowledge = user.knowledge_state.get("career_and_jobs", {})
        # body_language should have increased from 0.3 (watch bump + quiz correct)
        assert knowledge.get("body_language", 0) > 0.3

        # Verify DB state: recall entries created
        recalls = db_session.query(RecallQueue).filter_by(user_id="priya").all()
        assert len(recalls) > 0


# --- Journey 2: Rahul (IS) + vid_001 ---

def test_journey2_rahul_no_quiz(client, db_session):
    _seed_all(db_session)
    storage = _mock_storage()

    with patch("engine.loop.get_storage_client", return_value=storage), \
         patch("engine.recommender.get_storage_client", return_value=storage):
        resp = client.post("/video/complete", json={
            "user_id": "rahul",
            "video_id": "vid_001",
            "completion_rate": 1.0,
        })

    assert resp.status_code == 200
    data = resp.json()

    # IS classification
    assert data["classification"]["user_type"] == "IS"
    assert data["classification"]["show_quiz"] is False

    # Recap present (IS-toned)
    assert data["recap"] is not None
    assert len(data["recap"]) == 2
    assert all(b["tone"] == "IS" for b in data["recap"])

    # No questions
    assert data["questions"] is None

    # Recommendation returned directly (no-quiz path)
    assert data["recommendation"] is not None


# --- Utility video path ---

def test_utility_video_path(client, db_session):
    _seed_all(db_session)
    storage = _mock_storage()

    with patch("engine.loop.get_storage_client", return_value=storage), \
         patch("engine.recommender.get_storage_client", return_value=storage):
        resp = client.post("/video/complete", json={
            "user_id": "rahul",
            "video_id": "vid_008",
            "completion_rate": 1.0,
        })

    assert resp.status_code == 200
    data = resp.json()

    # Utility content
    assert data["classification"]["content_type"] == "utility"

    # No recap, no questions
    assert data["recap"] is None
    assert data["questions"] is None

    # Recommendation present
    assert data["recommendation"] is not None


# --- Error cases ---

def test_unknown_user_returns_404(client, db_session):
    resp = client.post("/session/start", json={"user_id": "unknown"})
    assert resp.status_code == 404


def test_unknown_video_returns_error(client, db_session):
    _seed_all(db_session)
    resp = client.post("/video/complete", json={
        "user_id": "priya",
        "video_id": "nonexistent",
        "completion_rate": 1.0,
    })
    # Engine will fail when trying to get a nonexistent video
    assert resp.status_code >= 400


# --- Recall answer ---

def test_recall_answer(client, db_session):
    """Test recall answer endpoint with a pre-seeded recall entry."""
    _seed_all(db_session)
    storage = _mock_storage()

    # Seed a recall entry
    now = datetime.now(timezone.utc)
    recall = RecallQueue(
        user_id="priya",
        concept_key="career_and_jobs/body_language",
        source_video_id="vid_001",
        due_at=now - timedelta(hours=1),
        interval_hours=18.0,
        status="pending",
    )
    db_session.add(recall)
    db_session.commit()
    db_session.refresh(recall)

    with patch("api.routes.get_storage_client", return_value=storage):
        resp = client.post("/recall/answer", json={
            "user_id": "priya",
            "recall_id": recall.id,
            "answer_index": 1,  # correct (medium question correct_index=1)
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is True
    assert data["next_interval_hours"] == 36.0  # 18 * 2
    assert data["new_score"] > 0.3  # was 0.3, should increase


def test_recall_answer_incorrect(client, db_session):
    _seed_all(db_session)
    storage = _mock_storage()

    now = datetime.now(timezone.utc)
    recall = RecallQueue(
        user_id="priya",
        concept_key="career_and_jobs/body_language",
        source_video_id="vid_001",
        due_at=now - timedelta(hours=1),
        interval_hours=18.0,
        status="pending",
    )
    db_session.add(recall)
    db_session.commit()
    db_session.refresh(recall)

    with patch("api.routes.get_storage_client", return_value=storage):
        resp = client.post("/recall/answer", json={
            "user_id": "priya",
            "recall_id": recall.id,
            "answer_index": 0,  # incorrect
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is False
    assert data["next_interval_hours"] == 12.0  # max(12, 18/2=9) = 12


# --- Session start with recalls ---

def test_session_start_with_recalls(client, db_session):
    _seed_all(db_session)
    storage = _mock_storage()

    now = datetime.now(timezone.utc)
    recall = RecallQueue(
        user_id="priya",
        concept_key="career_and_jobs/body_language",
        source_video_id="vid_001",
        due_at=now - timedelta(hours=1),
        interval_hours=18.0,
        status="pending",
    )
    db_session.add(recall)
    db_session.commit()

    with patch("engine.recall_scheduler.get_storage_client", return_value=storage):
        resp = client.post("/session/start", json={
            "user_id": "priya",
            "simulated_time": now.isoformat(),
        })

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["recalls"]) == 1
    assert data["recalls"][0]["concept_key"] == "career_and_jobs/body_language"
    assert data["recalls"][0]["question"] is not None
