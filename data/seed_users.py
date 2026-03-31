# Seed user definitions for the Saathi prototype.
# These are imported by seed_db.py to populate the database.

SEED_USERS = [
    {
        "user_id": "priya",
        "user_type": "AS",
        "maturity": "warming_up",
        "total_videos_watched": 8,
        "knowledge_state": {
            "career_and_jobs": {
                "body_language": 0.3,
                "answering_structure": 0.25,
                "voice_modulation": 0.7,
            }
        },
        # 3 prior Career & Jobs entries to trigger the depth signal in the classifier.
        # video_ids are abstract historical identifiers, not in the 15-video catalog.
        # Recall queue is empty at seed time; Journey 1 writes recall entries.
        "watch_history": [
            {
                "video_id": "prior_cj_001",
                "category": "career_and_jobs",
                "completion_rate": 1.0,
                "quiz_scores": {},
            },
            {
                "video_id": "prior_cj_002",
                "category": "career_and_jobs",
                "completion_rate": 1.0,
                "quiz_scores": {},
            },
            {
                "video_id": "prior_cj_003",
                "category": "career_and_jobs",
                "completion_rate": 1.0,
                "quiz_scores": {},
            },
        ],
    },
    {
        "user_id": "rahul",
        "user_type": "IS",
        "maturity": "new",
        "total_videos_watched": 2,
        "knowledge_state": {},
        # 1 Career & Jobs + 1 English Speaking entry — no single-category concentration.
        "watch_history": [
            {
                "video_id": "prior_cj_004",
                "category": "career_and_jobs",
                "completion_rate": 1.0,
                "quiz_scores": {},
            },
            {
                "video_id": "prior_es_001",
                "category": "english_speaking",
                "completion_rate": 1.0,
                "quiz_scores": {},
            },
        ],
    },
]
