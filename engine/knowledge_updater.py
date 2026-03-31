from dataclasses import dataclass
from sqlalchemy.orm import Session
from db.models import User
from db.operations import update_knowledge_state
from engine.evaluator import EvalResult


@dataclass
class KnowledgeUpdate:
    updated_state: dict  # {concept: new_score}
    delta: dict  # {concept: {"before": float, "after": float}}


def update_from_watch(
    db: Session,
    user: User,
    category: str,
    concept_profile: dict,
    completion_rate: float,
) -> KnowledgeUpdate:
    knowledge = (user.knowledge_state or {}).get(category, {})
    updated = {}
    delta = {}

    for concept, coverage in concept_profile.items():
        before = knowledge.get(concept, 0.0)
        new_score = min(0.8, before + 0.1 * completion_rate * coverage)
        new_score = round(new_score, 4)
        updated[concept] = new_score
        delta[concept] = {"before": before, "after": new_score}
        update_knowledge_state(db, user.user_id, category, concept, new_score)

    return KnowledgeUpdate(updated_state=updated, delta=delta)


def update_from_quiz(
    db: Session,
    user: User,
    category: str,
    quiz_results: list[EvalResult],
) -> KnowledgeUpdate:
    knowledge = (user.knowledge_state or {}).get(category, {})
    updated = {}
    delta = {}
    alpha = 0.3

    for result in quiz_results:
        before = knowledge.get(result.concept, 0.0)
        new_score = before + alpha * (result.score - before)
        new_score = round(min(1.0, max(0.0, new_score)), 4)
        updated[result.concept] = new_score
        delta[result.concept] = {"before": before, "after": new_score}
        update_knowledge_state(db, user.user_id, category, result.concept, new_score)

    return KnowledgeUpdate(updated_state=updated, delta=delta)


def update_from_recall(
    db: Session,
    user: User,
    concept_key: str,
    result: float,
) -> KnowledgeUpdate:
    # concept_key format: "category/concept"
    category, concept = concept_key.split("/", 1)
    knowledge = (user.knowledge_state or {}).get(category, {})
    alpha = 0.15

    before = knowledge.get(concept, 0.0)
    new_score = before + alpha * (result - before)
    new_score = round(min(1.0, max(0.0, new_score)), 4)

    update_knowledge_state(db, user.user_id, category, concept, new_score)

    return KnowledgeUpdate(
        updated_state={concept: new_score},
        delta={concept: {"before": before, "after": new_score}},
    )
