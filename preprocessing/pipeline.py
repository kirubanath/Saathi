"""Orchestrates the full preprocessing pipeline for aspiration videos.

Flow: load transcript -> concept extraction -> filtering -> recap/questions -> store in MinIO -> mark preprocessed in DB.
"""

import os

from config.taxonomy import CONCEPTS
from db.base import SessionLocal
from db.operations import get_video
from preprocessing.concept_extractor import extract_concepts
from preprocessing.recap_generator import generate_recaps
from preprocessing.question_generator import generate_questions
from storage.base import get_storage_client

MIN_COVERAGE = 0.3

# Maps series_id to the transcript subdirectory name
SERIES_DIR = {
    "series_cj_001": "aspiration/career_and_jobs/interview_confidence",
    "series_cj_002": "aspiration/career_and_jobs/career_foundations",
    "series_es_001": "aspiration/english_speaking/spoken_english_basics",
}

TRANSCRIPT_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "seed_transcripts")


def _resolve_transcript_path(video_id: str, series_id: str) -> str:
    subdir = SERIES_DIR.get(series_id)
    if not subdir:
        raise ValueError(f"No transcript directory mapped for series: {series_id}")
    return os.path.join(TRANSCRIPT_BASE, subdir, f"{video_id}.txt")


def preprocess_video(video_id: str, transcript_path: str, category: str) -> dict:
    """Preprocess a single video. Returns a summary dict of what was generated."""
    if category not in CONCEPTS:
        raise ValueError(f"No taxonomy for category '{category}'. Only aspiration categories can be preprocessed.")

    print(f"\n{'='*60}")
    print(f"Preprocessing {video_id} (category: {category})")
    print(f"{'='*60}")

    # 1. Load transcript
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read().strip()
    print(f"  Transcript loaded: {len(transcript)} chars")

    # 2. Concept extraction
    print("  Running concept extraction...")
    concept_profile = extract_concepts(transcript, category)
    print(f"  Concept profile: {concept_profile}")

    # 3. Filter active concepts
    active_concepts = {c: s for c, s in concept_profile.items() if s >= MIN_COVERAGE}
    inactive_concepts = {c: s for c, s in concept_profile.items() if s < MIN_COVERAGE}
    print(f"  Active concepts (>= {MIN_COVERAGE}): {list(active_concepts.keys())}")
    print(f"  Inactive concepts: {list(inactive_concepts.keys())}")

    # 4. Generate recaps for active concepts only
    recap_bullets = {}
    if active_concepts:
        print("  Generating recap bullets...")
        recap_bullets = generate_recaps(transcript, active_concepts)
        print(f"  Recaps generated for: {list(recap_bullets.keys())}")

    # 5. Generate questions for active concepts only
    question_sets = {}
    if active_concepts:
        print("  Generating questions...")
        question_sets = generate_questions(transcript, active_concepts)
        print(f"  Questions generated for: {list(question_sets.keys())}")

    # 6. Store artifacts in MinIO
    storage = get_storage_client()
    storage.put_json(f"videos/{video_id}/concept_profile.json", concept_profile)
    storage.put_json(f"videos/{video_id}/recap_bullets.json", recap_bullets)
    storage.put_json(f"videos/{video_id}/questions.json", question_sets)
    print(f"  Artifacts stored in MinIO under videos/{video_id}/")

    # 7. Mark video as preprocessed in DB
    db = SessionLocal()
    try:
        video = get_video(db, video_id)
        if video:
            video.preprocessed = True
            db.commit()
            print(f"  Video {video_id} marked as preprocessed in DB")
    finally:
        db.close()

    return {
        "video_id": video_id,
        "category": category,
        "concept_profile": concept_profile,
        "active_concepts": list(active_concepts.keys()),
        "inactive_concepts": list(inactive_concepts.keys()),
        "recap_count": len(recap_bullets),
        "question_count": len(question_sets),
    }


# All 7 aspiration videos
ASPIRATION_VIDEOS = [
    ("vid_001", "series_cj_001", "career_and_jobs"),
    ("vid_002", "series_cj_001", "career_and_jobs"),
    ("vid_003", "series_cj_001", "career_and_jobs"),
    ("vid_004", "series_cj_002", "career_and_jobs"),
    ("vid_005", "series_cj_002", "career_and_jobs"),
    ("vid_006", "series_es_001", "english_speaking"),
    ("vid_007", "series_es_001", "english_speaking"),
]


def preprocess_all(force: bool = False) -> list[dict]:
    """Preprocess all 7 aspiration videos. Skips videos whose artifacts already exist in MinIO unless force=True."""
    storage = get_storage_client()
    results = []
    for video_id, series_id, category in ASPIRATION_VIDEOS:
        if not force and storage.exists(f"videos/{video_id}/concept_profile.json"):
            print(f"  {video_id}: artifacts exist in MinIO — skipping (use force=True to re-run)")
            continue
        transcript_path = _resolve_transcript_path(video_id, series_id)
        summary = preprocess_video(video_id, transcript_path, category)
        results.append(summary)
    return results


if __name__ == "__main__":
    results = preprocess_all()
    print("\n" + "=" * 60)
    print("PREPROCESSING COMPLETE")
    print("=" * 60)
    for r in results:
        print(f"  {r['video_id']}: active={r['active_concepts']}, "
              f"recaps={r['recap_count']}, questions={r['question_count']}")
