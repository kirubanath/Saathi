"""Extract concept coverage scores from a video transcript using LLM."""

from config.taxonomy import CONCEPTS
from llm.base import get_llm_client
from llm.prompts import CONCEPT_EXTRACTION_SYSTEM, build_concept_extraction_prompt


def extract_concepts(transcript: str, category: str) -> dict[str, float]:
    """Return {concept: coverage_score} for all concepts in the category taxonomy.

    Retries once on validation failure.
    """
    concepts = CONCEPTS.get(category)
    if not concepts:
        raise ValueError(f"No taxonomy defined for category: {category}")

    llm = get_llm_client()
    prompt = build_concept_extraction_prompt(transcript, concepts)

    for attempt in range(2):
        result = llm.generate_json(prompt, system=CONCEPT_EXTRACTION_SYSTEM)
        if _validate(result, concepts):
            return result
        if attempt == 0:
            print(f"  Concept extraction validation failed, retrying... Got: {result}")

    raise ValueError(
        f"Concept extraction failed validation after 2 attempts. Last result: {result}"
    )


def _validate(result: dict, concepts: list[str]) -> bool:
    if not isinstance(result, dict):
        return False
    for c in concepts:
        if c not in result:
            return False
        score = result[c]
        if not isinstance(score, (int, float)):
            return False
        if score < 0.0 or score > 1.0:
            return False
    if set(result.keys()) != set(concepts):
        return False
    return True
