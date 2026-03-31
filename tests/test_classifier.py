import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import Base
from db.models import User, Video
from engine.classifier import classify


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _make_user(db, user_id="priya", user_type="AS", maturity="warming_up"):
    user = User(user_id=user_id, user_type=user_type, maturity=maturity, knowledge_state={})
    db.add(user)
    db.commit()
    return user


def _make_video(db, video_id="vid_001", content_type="aspiration", category="career_and_jobs"):
    video = Video(
        video_id=video_id, title="Test", content_type=content_type,
        category=category, series_id="s1", series_position=1,
    )
    db.add(video)
    db.commit()
    return video


def test_as_user_aspiration_full_loop(db):
    user = _make_user(db, user_type="AS", maturity="warming_up")
    video = _make_video(db, content_type="aspiration")
    result = classify(user, video)
    assert result.content_type == "aspiration"
    assert result.user_type == "AS"
    assert result.show_recap is True
    assert result.show_quiz is True
    assert result.show_recall is True
    assert result.max_bullets == 3


def test_as_new_user_no_recall(db):
    user = _make_user(db, user_type="AS", maturity="new")
    video = _make_video(db, content_type="aspiration")
    result = classify(user, video)
    assert result.show_quiz is True
    assert result.show_recall is False


def test_is_user_aspiration_recap_only(db):
    user = _make_user(db, user_type="IS", maturity="new")
    video = _make_video(db, content_type="aspiration")
    result = classify(user, video)
    assert result.show_recap is True
    assert result.show_quiz is False
    assert result.show_recall is False
    assert result.max_bullets == 2


def test_converting_user_aspiration(db):
    user = _make_user(db, user_type="converting", maturity="warming_up")
    video = _make_video(db, content_type="aspiration")
    result = classify(user, video)
    assert result.show_recap is True
    assert result.show_quiz is True
    assert result.show_recall is False
    assert result.max_bullets == 2
    assert result.difficulty_cap == "medium"


def test_utility_content_no_learning_loop(db):
    user = _make_user(db, user_type="AS", maturity="warming_up")
    video = _make_video(db, video_id="vid_008", content_type="utility", category="sarkari_kaam")
    result = classify(user, video)
    assert result.content_type == "utility"
    assert result.show_recap is False
    assert result.show_quiz is False
    assert result.show_recall is False


def test_entertainment_content_no_learning_loop(db):
    user = _make_user(db, user_type="AS", maturity="warming_up")
    video = _make_video(db, video_id="vid_010", content_type="entertainment", category="cricket")
    result = classify(user, video)
    assert result.content_type == "entertainment"
    assert result.show_recap is False
    assert result.show_quiz is False
    assert result.show_recall is False


def test_reasoning_populated(db):
    user = _make_user(db, user_type="AS", maturity="warming_up")
    video = _make_video(db, content_type="aspiration")
    result = classify(user, video)
    assert len(result.reasoning) >= 4
