from dataclasses import dataclass
from db.models import User
from engine.classifier import ClassificationResult


@dataclass
class Question:
    concept: str
    difficulty: str  # easy | medium | hard
    question: str
    options: list[str]
    correct_index: int


def _select_difficulty(concept_score: float, difficulty_cap: str | None) -> str:
    if concept_score < 0.4:
        difficulty = "easy"
    elif concept_score <= 0.7:
        difficulty = "medium"
    else:
        difficulty = "hard"

    # Apply cap for converting users
    if difficulty_cap == "medium" and difficulty == "hard":
        difficulty = "medium"

    return difficulty


def select_questions(
    user: User,
    video_artifacts: dict,
    recap_concepts: list[str],
    classification: ClassificationResult,
) -> list[Question]:
    questions_data = video_artifacts["questions"]
    knowledge = user.knowledge_state or {}

    # Find the category for these concepts
    category_knowledge = {}
    for cat_knowledge in knowledge.values():
        if any(c in cat_knowledge for c in recap_concepts):
            category_knowledge = cat_knowledge
            break

    selected = []
    for concept in recap_concepts:
        if concept not in questions_data:
            continue

        concept_score = category_knowledge.get(concept, 0.0)
        difficulty = _select_difficulty(concept_score, classification.difficulty_cap)

        q_data = questions_data[concept].get(difficulty)
        if not q_data:
            continue

        selected.append(
            Question(
                concept=concept,
                difficulty=difficulty,
                question=q_data["question"],
                options=q_data["options"],
                correct_index=q_data["correct_index"],
            )
        )

    return selected
