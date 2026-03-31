from dataclasses import dataclass
from db.models import User
from engine.classifier import ClassificationResult


@dataclass
class RecapBullet:
    concept: str
    bullet: str
    tone: str  # IS or AS
    coverage_score: float
    gap_score: float
    rank: int


@dataclass
class RecapResult:
    bullets: list[RecapBullet]
    reasoning: list[str]


def generate_recap(
    user: User,
    video_artifacts: dict,
    classification: ClassificationResult,
) -> RecapResult:
    concept_profile = video_artifacts["concept_profile"]
    recap_bullets = video_artifacts["recap_bullets"]
    reasoning = []

    category = None
    for cat in (user.knowledge_state or {}):
        if any(c in concept_profile for c in (user.knowledge_state.get(cat) or {})):
            category = cat
            break

    # Determine which category these concepts belong to by checking concept_profile keys
    # against the user's knowledge state
    knowledge = {}
    if category:
        knowledge = user.knowledge_state.get(category, {})

    user_type = classification.user_type
    max_bullets = classification.max_bullets

    # Rank concepts
    ranked = []
    for concept, coverage in concept_profile.items():
        if concept not in recap_bullets:
            continue  # No recap generated for this concept (inactive)

        if user_type == "IS":
            # IS: rank by coverage only (no knowledge state)
            score = coverage
            gap = 0.0
            reasoning.append(
                f"{concept}: coverage={coverage:.2f}, ranked by coverage only (IS user)"
            )
        else:
            # AS/Converting: rank by coverage * (1 - knowledge_score)
            knowledge_score = knowledge.get(concept, 0.0)
            gap = 1.0 - knowledge_score
            score = coverage * gap
            reasoning.append(
                f"{concept}: coverage={coverage:.2f}, knowledge={knowledge_score:.2f}, "
                f"gap={gap:.2f}, score={score:.2f}"
            )

        ranked.append((concept, coverage, gap, score))

    # Sort by score descending
    ranked.sort(key=lambda x: x[3], reverse=True)

    # Select top N bullets
    tone = "IS" if user_type == "IS" else "AS"
    selected = ranked[:max_bullets]

    bullets = []
    for rank, (concept, coverage, gap, score) in enumerate(selected, 1):
        bullet_text = recap_bullets[concept].get(tone, "")
        bullets.append(
            RecapBullet(
                concept=concept,
                bullet=bullet_text,
                tone=tone,
                coverage_score=coverage,
                gap_score=gap,
                rank=rank,
            )
        )

    reasoning.append(
        f"Selected top {len(selected)} of {len(ranked)} concepts "
        f"(max_bullets={max_bullets}, tone={tone})"
    )

    return RecapResult(bullets=bullets, reasoning=reasoning)
