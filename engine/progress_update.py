from db.models import User


def _format_concept_name(concept: str) -> str:
    return concept.replace("_", " ").title()


def generate_progress_message(user: User, score_delta: dict) -> str:
    """Generate a progress message after quiz submission.

    Only called for AS and Converting users. IS users never reach this function.

    Args:
        user: The user who completed the quiz.
        score_delta: Dict of {concept: {"before": float, "after": float}}.

    Returns:
        A plain text progress message string.
    """
    if not score_delta:
        return "Keep going, every video counts."

    deltas = {
        concept: d["after"] - d["before"]
        for concept, d in score_delta.items()
    }

    avg_delta = sum(deltas.values()) / len(deltas)

    # Find most improved and weakest concept
    most_improved = max(deltas, key=deltas.get)
    focus_concept = min(deltas, key=deltas.get)

    is_as = user.user_type == "AS"

    if avg_delta > 0.05:
        # Positive reinforcement
        concept_name = _format_concept_name(most_improved)
        if is_as:
            return (
                f"You're building real strength in {concept_name}. "
                f"That growth is adding up."
            )
        else:
            return (
                f"Nice work on {concept_name}. "
                f"You're making solid progress."
            )

    if avg_delta >= -0.05:
        # Neutral encouragement
        concept_name = _format_concept_name(focus_concept)
        if is_as:
            return (
                f"You're on the right track. "
                f"Keep focusing on {concept_name} and it will click."
            )
        else:
            return (
                f"Good effort. "
                f"A bit more practice on {concept_name} will help."
            )

    # Regression: supportive message
    concept_name = _format_concept_name(focus_concept)
    if is_as:
        return (
            f"This one was tough. "
            f"Revisiting {concept_name} will strengthen your foundation."
        )
    else:
        return (
            f"No worries, these take practice. "
            f"Try reviewing {concept_name} again."
        )
