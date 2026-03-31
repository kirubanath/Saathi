"""Full loop integration tests using in-memory DB and mock storage."""
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import Base
from db.models import User, Video, WatchHistory, RecallQueue
from engine.loop import run_video_complete_loop, run_quiz_submit


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _seed_all(db):
    """Seed Priya, Rahul, and all videos."""
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
        # Minimal artifacts for other videos used in recommendations
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


# --- Journey 1: Priya (AS) + vid_001 ---

def test_journey1_priya_video_complete(db):
    _seed_all(db)
    storage = _mock_storage()

    with patch("engine.loop.get_storage_client", return_value=storage), \
         patch("engine.recommender.get_storage_client", return_value=storage):
        result = run_video_complete_loop(db, "priya", "vid_001", 1.0)

    # Classification: AS, aspiration, warming_up
    assert result.classification.content_type == "aspiration"
    assert result.classification.user_type == "AS"
    assert result.classification.show_quiz is True

    # Watch bump applied
    assert result.watch_update is not None

    # Recap generated with 2 bullets (vid_001 only has 2 active concepts)
    assert result.recap is not None
    assert len(result.recap.bullets) == 2

    # Questions returned (quiz path)
    assert result.questions is not None
    assert len(result.questions) == 2

    # No recommendation yet (quiz path, user must submit)
    assert result.recommendation is None


def test_journey1_priya_quiz_submit(db):
    _seed_all(db)
    storage = _mock_storage()

    with patch("engine.loop.get_storage_client", return_value=storage), \
         patch("engine.recommender.get_storage_client", return_value=storage):
        loop_result = run_video_complete_loop(db, "priya", "vid_001", 1.0)

        # Submit quiz: both correct
        answers = [q.correct_index for q in loop_result.questions]
        quiz_result = run_quiz_submit(
            db, "priya", "vid_001", loop_result.questions, answers
        )

    # All correct
    assert all(r.correct for r in quiz_result.eval_results)

    # Knowledge updated
    assert quiz_result.quiz_update is not None

    # Progress message generated (AS user)
    assert quiz_result.progress_message is not None
    assert len(quiz_result.progress_message) > 0

    # Recommendation returned
    assert quiz_result.recommendation is not None
    # Slot 1 should be vid_002 (next in series)
    assert quiz_result.recommendation.slot1 is not None
    assert quiz_result.recommendation.slot1["video_id"] == "vid_002"

    # Recalls scheduled (AS warming_up)
    assert quiz_result.recalls_scheduled > 0


# --- Journey 2: Rahul (IS) + vid_001 ---

def test_journey2_rahul_no_quiz(db):
    _seed_all(db)
    storage = _mock_storage()

    with patch("engine.loop.get_storage_client", return_value=storage), \
         patch("engine.recommender.get_storage_client", return_value=storage):
        result = run_video_complete_loop(db, "rahul", "vid_001", 1.0)

    # Classification: IS, aspiration
    assert result.classification.user_type == "IS"
    assert result.classification.show_quiz is False

    # Recap generated (IS-toned, 2 bullets)
    assert result.recap is not None
    assert len(result.recap.bullets) == 2
    assert all(b.tone == "IS" for b in result.recap.bullets)

    # No questions (IS path)
    assert result.questions is None

    # Recommendation returned directly (no-quiz path)
    assert result.recommendation is not None


# --- Journey: utility video ---

def test_utility_video_no_learning_loop(db):
    _seed_all(db)
    storage = _mock_storage()

    with patch("engine.loop.get_storage_client", return_value=storage), \
         patch("engine.recommender.get_storage_client", return_value=storage):
        result = run_video_complete_loop(db, "rahul", "vid_008", 1.0)

    # No recap, no quiz, no recall
    assert result.classification.content_type == "utility"
    assert result.recap is None
    assert result.questions is None
    assert result.watch_update is None

    # Recommendation still returned
    assert result.recommendation is not None


# --- Watch bump verification ---

def test_watch_bump_applied_for_all_user_types(db):
    _seed_all(db)
    storage = _mock_storage()

    with patch("engine.loop.get_storage_client", return_value=storage), \
         patch("engine.recommender.get_storage_client", return_value=storage):
        # IS user also gets watch bump for aspiration
        result = run_video_complete_loop(db, "rahul", "vid_001", 1.0)

    assert result.watch_update is not None
    assert "body_language" in result.watch_update.delta


# --- Quiz submit for IS user should not happen, but verify progress message guard ---

def test_quiz_submit_no_progress_for_is_user(db):
    """If run_quiz_submit were called for an IS user, no progress message."""
    _seed_all(db)
    storage = _mock_storage()

    with patch("engine.loop.get_storage_client", return_value=storage), \
         patch("engine.recommender.get_storage_client", return_value=storage):
        # Force a quiz path for testing (IS users normally don't reach this)
        from engine.quiz_engine import Question
        questions = [
            Question(concept="body_language", difficulty="easy",
                     question="test?", options=["a", "b", "c", "d"], correct_index=0)
        ]
        quiz_result = run_quiz_submit(db, "rahul", "vid_001", questions, [0])

    assert quiz_result.progress_message is None
    assert quiz_result.recalls_scheduled == 0
