import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import Base
from db.models import User, Video, WatchHistory
from db.operations import add_watch_history
from engine.recommender import recommend, _build_candidate_pool, _is_series_completed


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


def _seed_videos(db):
    """Seed a minimal set of videos for recommender testing."""
    videos = [
        Video(video_id="vid_001", title="V1", content_type="aspiration",
              category="career_and_jobs", series_id="series_cj_001", series_position=1),
        Video(video_id="vid_002", title="V2", content_type="aspiration",
              category="career_and_jobs", series_id="series_cj_001", series_position=2),
        Video(video_id="vid_003", title="V3", content_type="aspiration",
              category="career_and_jobs", series_id="series_cj_001", series_position=3),
        Video(video_id="vid_004", title="V4", content_type="aspiration",
              category="career_and_jobs", series_id="series_cj_002", series_position=1),
        Video(video_id="vid_005", title="V5", content_type="aspiration",
              category="career_and_jobs", series_id="series_cj_002", series_position=2),
        Video(video_id="vid_006", title="V6", content_type="aspiration",
              category="english_speaking", series_id="series_es_001", series_position=1),
        Video(video_id="vid_008", title="V8", content_type="utility",
              category="sarkari_kaam", series_id="series_sk_001", series_position=1),
        Video(video_id="vid_009", title="V9", content_type="utility",
              category="sarkari_kaam", series_id="series_sk_001", series_position=2),
        Video(video_id="vid_010", title="V10", content_type="entertainment",
              category="cricket", series_id="series_cr_001", series_position=1),
    ]
    for v in videos:
        db.add(v)
    db.commit()
    return videos


def _mock_storage():
    """Create a mock storage client that returns concept profiles."""
    mock = MagicMock()
    profiles = {
        "videos/vid_001/concept_profile.json": {"body_language": 0.85, "handling_nervousness": 0.7},
        "videos/vid_002/concept_profile.json": {"answering_structure": 0.8, "voice_modulation": 0.6},
        "videos/vid_003/concept_profile.json": {"voice_modulation": 0.75, "handling_nervousness": 0.65},
        "videos/vid_004/concept_profile.json": {"preparation": 0.9, "answering_structure": 0.5},
        "videos/vid_005/concept_profile.json": {"answering_structure": 0.7, "handling_nervousness": 0.4},
        "videos/vid_006/concept_profile.json": {"pronunciation": 0.8, "fluency": 0.7},
    }
    mock.get_json.side_effect = lambda key: profiles.get(key, {})
    return mock


def test_slot1_returns_next_in_series(db):
    _seed_videos(db)
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.3, "handling_nervousness": 0.2}
    })
    vid = db.query(Video).get("vid_001")

    with patch("engine.recommender.get_storage_client", return_value=_mock_storage()):
        result = recommend(db, user, vid)

    assert result.slot1 is not None
    assert result.slot1["video_id"] == "vid_002"


def test_slot1_empty_when_series_complete(db):
    _seed_videos(db)
    user = _make_user(db)
    # Watch all 3 episodes of series_cj_001
    add_watch_history(db, "priya", "vid_001", "career_and_jobs", 1.0, {})
    add_watch_history(db, "priya", "vid_002", "career_and_jobs", 1.0, {})
    add_watch_history(db, "priya", "vid_003", "career_and_jobs", 1.0, {})

    vid = db.query(Video).get("vid_003")  # Last in series

    with patch("engine.recommender.get_storage_client", return_value=_mock_storage()):
        result = recommend(db, user, vid)

    assert result.slot1 is None


def test_slot2_excludes_current_series(db):
    _seed_videos(db)
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.3}
    })
    vid = db.query(Video).get("vid_001")

    with patch("engine.recommender.get_storage_client", return_value=_mock_storage()):
        result = recommend(db, user, vid)

    # Slot 2 should NOT be from series_cj_001
    assert result.slot2 is not None
    assert result.slot2.get("series_id") != "series_cj_001"


def test_slot1_and_slot2_different_series(db):
    _seed_videos(db)
    user = _make_user(db, knowledge_state={
        "career_and_jobs": {"body_language": 0.3}
    })
    vid = db.query(Video).get("vid_001")

    with patch("engine.recommender.get_storage_client", return_value=_mock_storage()):
        result = recommend(db, user, vid)

    if result.slot1 and result.slot2:
        assert result.slot1["video_id"] != result.slot2["video_id"]


def test_pool_never_started_series_contributes_ep1(db):
    _seed_videos(db)
    all_videos = db.query(Video).all()

    pool = _build_candidate_pool(
        all_videos, [], set(),
        exclude_series_id="series_cj_001",
        current_content_type="aspiration",
        reasoning=[],
    )

    # series_cj_002 never started, should contribute vid_004 (ep 1)
    cj002_candidates = [c for c in pool if c.series_id == "series_cj_002"]
    assert len(cj002_candidates) == 1
    assert cj002_candidates[0].video.video_id == "vid_004"


def test_pool_mid_series_contributes_next_unwatched(db):
    _seed_videos(db)
    all_videos = db.query(Video).all()
    watched_ids = {"vid_004"}  # Watched ep 1 of series_cj_002

    pool = _build_candidate_pool(
        all_videos, [], watched_ids,
        exclude_series_id="series_cj_001",
        current_content_type="aspiration",
        reasoning=[],
    )

    cj002_candidates = [c for c in pool if c.series_id == "series_cj_002"]
    assert len(cj002_candidates) == 1
    assert cj002_candidates[0].video.video_id == "vid_005"


def test_pool_completed_utility_excluded(db):
    _seed_videos(db)
    all_videos = db.query(Video).all()
    watched_ids = {"vid_008", "vid_009"}  # All of series_sk_001

    pool = _build_candidate_pool(
        all_videos, [], watched_ids,
        exclude_series_id="series_cj_001",
        current_content_type="utility",
        reasoning=[],
    )

    sk001_candidates = [c for c in pool if c.series_id == "series_sk_001"]
    assert len(sk001_candidates) == 0


def test_pool_completed_aspiration_reenters_with_revisit(db):
    from datetime import datetime, timezone
    _seed_videos(db)
    all_videos = db.query(Video).all()

    now = datetime.now(timezone.utc)
    watch_history = [
        WatchHistory(user_id="priya", video_id="vid_004", category="career_and_jobs",
                     completion_rate=1.0, quiz_scores={"preparation": 0.8}, watched_at=now),
        WatchHistory(user_id="priya", video_id="vid_005", category="career_and_jobs",
                     completion_rate=1.0, quiz_scores={"answering_structure": 0.6}, watched_at=now),
    ]
    watched_ids = {"vid_004", "vid_005"}

    pool = _build_candidate_pool(
        all_videos, watch_history, watched_ids,
        exclude_series_id="series_cj_001",
        current_content_type="aspiration",
        reasoning=[],
    )

    cj002_candidates = [c for c in pool if c.series_id == "series_cj_002"]
    assert len(cj002_candidates) == 1
    assert cj002_candidates[0].is_revisit is True
    assert cj002_candidates[0].video.video_id == "vid_004"  # Re-enters as ep 1
