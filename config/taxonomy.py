CONCEPTS = {
    "career_and_jobs": [
        "body_language",
        "voice_modulation",
        "answering_structure",
        "handling_nervousness",
        "preparation",
    ],
    "english_speaking": [
        "vocabulary",
        "pronunciation",
        "fluency",
        "grammar",
    ],
}

# Aspiration-to-aspiration adjacency only.
# Utility and entertainment categories use fixed bucket distributions, not adjacency.
ADJACENCY = {
    "career_and_jobs": ["english_speaking"],
    "english_speaking": ["career_and_jobs"],
}
