"""
Seed script: creates users, watch history, and all 15 videos in saathi.db.
After seeding, copies saathi.db to saathi_seed.db as an immutable snapshot.

Run from the project root:
    python data/seed_db.py
"""

import shutil
from datetime import datetime, timezone

from db.base import Base, SessionLocal, engine
from db.models import User, Video, WatchHistory
from data.seed_users import SEED_USERS
from config.settings import settings


VIDEOS = [
    # Career & Jobs — Interview Confidence (series_cj_001)
    {
        "video_id": "vid_001",
        "title": "Body Language in Interviews",
        "content_type": "aspiration",
        "category": "career_and_jobs",
        "series_id": "series_cj_001",
        "series_position": 1,
        "preprocessed": False,
    },
    {
        "video_id": "vid_002",
        "title": "Answering Questions with Structure",
        "content_type": "aspiration",
        "category": "career_and_jobs",
        "series_id": "series_cj_001",
        "series_position": 2,
        "preprocessed": False,
    },
    {
        "video_id": "vid_003",
        "title": "Voice and Confidence Under Pressure",
        "content_type": "aspiration",
        "category": "career_and_jobs",
        "series_id": "series_cj_001",
        "series_position": 3,
        "preprocessed": False,
    },
    # Career & Jobs — Career Foundations (series_cj_002)
    {
        "video_id": "vid_004",
        "title": "Resume Tips That Actually Work",
        "content_type": "aspiration",
        "category": "career_and_jobs",
        "series_id": "series_cj_002",
        "series_position": 1,
        "preprocessed": False,
    },
    {
        "video_id": "vid_005",
        "title": "Salary Negotiation for Freshers",
        "content_type": "aspiration",
        "category": "career_and_jobs",
        "series_id": "series_cj_002",
        "series_position": 2,
        "preprocessed": False,
    },
    # English Speaking — Spoken English Basics (series_es_001)
    {
        "video_id": "vid_006",
        "title": "Pronunciation That Gets You Heard",
        "content_type": "aspiration",
        "category": "english_speaking",
        "series_id": "series_es_001",
        "series_position": 1,
        "preprocessed": False,
    },
    {
        "video_id": "vid_007",
        "title": "Everyday Vocabulary for Conversations",
        "content_type": "aspiration",
        "category": "english_speaking",
        "series_id": "series_es_001",
        "series_position": 2,
        "preprocessed": False,
    },
    # Sarkari Kaam — Government Documents (series_sk_001)
    {
        "video_id": "vid_008",
        "title": "How to Get Your PAN Card",
        "content_type": "utility",
        "category": "sarkari_kaam",
        "series_id": "series_sk_001",
        "series_position": 1,
        "preprocessed": False,
    },
    {
        "video_id": "vid_009",
        "title": "How to Link Aadhaar to Your Phone",
        "content_type": "utility",
        "category": "sarkari_kaam",
        "series_id": "series_sk_001",
        "series_position": 2,
        "preprocessed": False,
    },
    # Cricket — Cricket Basics (series_cr_001)
    {
        "video_id": "vid_010",
        "title": "How T20 Scoring Works",
        "content_type": "entertainment",
        "category": "cricket",
        "series_id": "series_cr_001",
        "series_position": 1,
        "preprocessed": False,
    },
    {
        "video_id": "vid_011",
        "title": "Great Catches That Changed Matches",
        "content_type": "entertainment",
        "category": "cricket",
        "series_id": "series_cr_001",
        "series_position": 2,
        "preprocessed": False,
    },
    # Sarkari Kaam — Voter Services (series_sk_002)
    {
        "video_id": "vid_012",
        "title": "How to Register as a Voter",
        "content_type": "utility",
        "category": "sarkari_kaam",
        "series_id": "series_sk_002",
        "series_position": 1,
        "preprocessed": False,
    },
    {
        "video_id": "vid_013",
        "title": "How to Check Your Voter Status",
        "content_type": "utility",
        "category": "sarkari_kaam",
        "series_id": "series_sk_002",
        "series_position": 2,
        "preprocessed": False,
    },
    # Mobile Tricks — Phone Basics (series_mt_001)
    {
        "video_id": "vid_014",
        "title": "How to Manage Mobile Data Settings",
        "content_type": "utility",
        "category": "mobile_tricks",
        "series_id": "series_mt_001",
        "series_position": 1,
        "preprocessed": False,
    },
    {
        "video_id": "vid_015",
        "title": "WhatsApp Tips Everyone Should Know",
        "content_type": "utility",
        "category": "mobile_tricks",
        "series_id": "series_mt_001",
        "series_position": 2,
        "preprocessed": False,
    },
]


def _db_path_from_url(url: str) -> str:
    """Extract the file path from a sqlite:/// URL."""
    return url.replace("sqlite:///", "")


def seed():
    print("Dropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        print("Seeding videos...")
        for v in VIDEOS:
            db.add(Video(**v))
        db.commit()
        print(f"  {len(VIDEOS)} videos inserted.")

        print("Seeding users and watch history...")
        for user_data in SEED_USERS:
            user = User(
                user_id=user_data["user_id"],
                user_type=user_data["user_type"],
                maturity=user_data["maturity"],
                total_videos_watched=user_data["total_videos_watched"],
                knowledge_state=user_data["knowledge_state"],
                first_seen=now,
                last_updated=now,
            )
            db.add(user)
            db.flush()

            for entry in user_data["watch_history"]:
                db.add(
                    WatchHistory(
                        user_id=user_data["user_id"],
                        video_id=entry["video_id"],
                        category=entry["category"],
                        completion_rate=entry["completion_rate"],
                        quiz_scores=entry["quiz_scores"],
                        watched_at=now,
                    )
                )

        db.commit()
        print(f"  {len(SEED_USERS)} users inserted.")

    finally:
        db.close()

    db_path = _db_path_from_url(settings.DATABASE_URL)
    seed_path = _db_path_from_url(settings.SEED_DB_PATH)
    shutil.copy2(db_path, seed_path)
    print(f"Snapshot saved: {db_path} -> {seed_path}")
    print("Seeding complete.")


if __name__ == "__main__":
    seed()
