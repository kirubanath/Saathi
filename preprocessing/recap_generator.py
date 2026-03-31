"""Generate IS and AS recap bullets for active concepts."""

from llm.base import get_llm_client
from llm.prompts import RECAP_GENERATION_SYSTEM, build_recap_generation_prompt


def generate_recaps(
    transcript: str, active_concepts: dict[str, float]
) -> dict[str, dict[str, str]]:
    """Return {concept: {"IS": "...", "AS": "..."}} for each active concept.

    Only called with concepts that passed the MIN_COVERAGE filter.
    """
    llm = get_llm_client()
    recaps = {}

    for concept, coverage_score in active_concepts.items():
        prompt = build_recap_generation_prompt(transcript, concept, coverage_score)
        result = llm.generate_json(prompt, system=RECAP_GENERATION_SYSTEM)

        if not isinstance(result, dict) or "IS" not in result or "AS" not in result:
            print(f"  Invalid recap for {concept}, retrying...")
            result = llm.generate_json(prompt, system=RECAP_GENERATION_SYSTEM)

        recaps[concept] = {"IS": result.get("IS", ""), "AS": result.get("AS", "")}

    return recaps
