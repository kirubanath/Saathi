"""Generate easy/medium/hard MCQs for active concepts."""

from llm.base import get_llm_client
from llm.prompts import QUESTION_GENERATION_SYSTEM, build_question_generation_prompt

VALID_DIFFICULTIES = {"easy", "medium", "hard"}


def generate_questions(
    transcript: str, active_concepts: dict[str, float]
) -> dict[str, dict]:
    """Return {concept: {"easy": {...}, "medium": {...}, "hard": {...}}} for each active concept.

    Only called with concepts that passed the MIN_COVERAGE filter.
    """
    llm = get_llm_client()
    questions = {}

    for concept in active_concepts:
        prompt = build_question_generation_prompt(transcript, concept)
        result = llm.generate_json(prompt, system=QUESTION_GENERATION_SYSTEM)

        if not _validate(result):
            print(f"  Invalid questions for {concept}, retrying...")
            result = llm.generate_json(prompt, system=QUESTION_GENERATION_SYSTEM)

        if _validate(result):
            questions[concept] = result
        else:
            print(f"  WARNING: Questions for {concept} failed validation after retry")
            questions[concept] = result

    return questions


def _validate(result: dict) -> bool:
    if not isinstance(result, dict):
        return False
    for diff in VALID_DIFFICULTIES:
        if diff not in result:
            return False
        q = result[diff]
        if not isinstance(q, dict):
            return False
        if "question" not in q or "options" not in q or "correct_index" not in q:
            return False
        if not isinstance(q["options"], list) or len(q["options"]) != 4:
            return False
        if q["correct_index"] not in (0, 1, 2, 3):
            return False
    return True
