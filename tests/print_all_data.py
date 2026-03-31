"""Print all prompts, user data, video data, and MinIO artifacts as JSON.

Run from project root:
    .venv/bin/python tests/print_all_data.py
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.taxonomy import CONCEPTS
from data.seed_users import SEED_USERS
from data.seed_db import VIDEOS
from llm.prompts import (
    CONCEPT_EXTRACTION_SYSTEM,
    RECAP_GENERATION_SYSTEM,
    QUESTION_GENERATION_SYSTEM,
    build_concept_extraction_prompt,
    build_recap_generation_prompt,
    build_question_generation_prompt,
)


def section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def dump(data):
    print(json.dumps(data, indent=2, default=str))


def main():
    # ---------------------------------------------------------------
    # 1. Taxonomy
    # ---------------------------------------------------------------
    section("TAXONOMY (config/taxonomy.py)")
    dump(CONCEPTS)

    # ---------------------------------------------------------------
    # 2. Seed users
    # ---------------------------------------------------------------
    section("SEED USERS (data/seed_users.py)")
    dump(SEED_USERS)

    # ---------------------------------------------------------------
    # 3. Video catalog
    # ---------------------------------------------------------------
    section("VIDEO CATALOG (data/seed_db.py)")
    dump(VIDEOS)

    # ---------------------------------------------------------------
    # 4. Prompt: Concept Extraction
    # ---------------------------------------------------------------
    section("PROMPT: CONCEPT EXTRACTION")

    print("--- SYSTEM ---")
    print(CONCEPT_EXTRACTION_SYSTEM)

    sample_transcript = "Sample transcript text here."
    sample_concepts = CONCEPTS["career_and_jobs"]

    print("\n--- USER (career_and_jobs example) ---")
    print(build_concept_extraction_prompt(sample_transcript, sample_concepts))

    # ---------------------------------------------------------------
    # 5. Prompt: Recap Generation
    # ---------------------------------------------------------------
    section("PROMPT: RECAP GENERATION")

    print("--- SYSTEM ---")
    print(RECAP_GENERATION_SYSTEM)

    print("\n--- USER (handling_nervousness, score=0.85 example) ---")
    print(build_recap_generation_prompt(sample_transcript, "handling_nervousness", 0.85))

    # ---------------------------------------------------------------
    # 6. Prompt: Question Generation
    # ---------------------------------------------------------------
    section("PROMPT: QUESTION GENERATION")

    print("--- SYSTEM ---")
    print(QUESTION_GENERATION_SYSTEM)

    print("\n--- USER (handling_nervousness example) ---")
    print(build_question_generation_prompt(sample_transcript, "handling_nervousness"))

    # ---------------------------------------------------------------
    # 7. MinIO artifacts (if available)
    # ---------------------------------------------------------------
    section("MINIO ARTIFACTS")

    try:
        from storage.base import get_storage_client
        storage = get_storage_client()

        for vid_id in ["vid_001", "vid_002", "vid_003", "vid_004", "vid_005", "vid_006", "vid_007"]:
            keys = storage.list_keys(f"videos/{vid_id}/")
            if not keys:
                print(f"{vid_id}: no artifacts")
                continue

            print(f"\n--- {vid_id} ---")
            for key in sorted(keys):
                data = storage.get_json(key)
                print(f"\n  {key}:")
                print(json.dumps(data, indent=4))

        # Confirm no artifacts for non-aspiration videos
        print("\n--- Non-aspiration videos (should be empty) ---")
        for vid_id in ["vid_008", "vid_009", "vid_010", "vid_011", "vid_012", "vid_013", "vid_014", "vid_015"]:
            keys = storage.list_keys(f"videos/{vid_id}/")
            status = "NO artifacts (correct)" if not keys else f"HAS artifacts: {keys}"
            print(f"  {vid_id}: {status}")

    except Exception as e:
        print(f"Could not connect to MinIO: {e}")
        print("Skipping artifact dump. Make sure MinIO is running.")

    # ---------------------------------------------------------------
    # 8. DB state (if available)
    # ---------------------------------------------------------------
    section("DATABASE STATE")

    try:
        from db.base import SessionLocal
        from db.models import User, Video, WatchHistory, RecallQueue

        db = SessionLocal()

        print("--- Users ---")
        for u in db.query(User).all():
            dump({
                "user_id": u.user_id,
                "user_type": u.user_type,
                "maturity": u.maturity,
                "total_videos_watched": u.total_videos_watched,
                "knowledge_state": u.knowledge_state,
                "first_seen": u.first_seen,
                "last_updated": u.last_updated,
            })

        print("\n--- Videos ---")
        for v in db.query(Video).all():
            dump({
                "video_id": v.video_id,
                "title": v.title,
                "content_type": v.content_type,
                "category": v.category,
                "series_id": v.series_id,
                "series_position": v.series_position,
                "preprocessed": v.preprocessed,
            })

        print("\n--- Watch History ---")
        for w in db.query(WatchHistory).all():
            dump({
                "id": w.id,
                "user_id": w.user_id,
                "video_id": w.video_id,
                "category": w.category,
                "completion_rate": w.completion_rate,
                "quiz_scores": w.quiz_scores,
                "watched_at": w.watched_at,
            })

        print("\n--- Recall Queue ---")
        recalls = db.query(RecallQueue).all()
        if recalls:
            for r in recalls:
                dump({
                    "id": r.id,
                    "user_id": r.user_id,
                    "concept_key": r.concept_key,
                    "source_video_id": r.source_video_id,
                    "due_at": r.due_at,
                    "interval_hours": r.interval_hours,
                    "status": r.status,
                })
        else:
            print("  (empty - recall entries are created during journeys)")

        db.close()

    except Exception as e:
        print(f"Could not read database: {e}")


if __name__ == "__main__":
    main()
