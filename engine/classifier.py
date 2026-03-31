from dataclasses import dataclass, field
from db.models import User, Video


@dataclass
class ClassificationResult:
    content_type: str  # aspiration | utility | entertainment
    user_type: str  # IS | converting | AS
    maturity: str  # new | warming_up | established
    show_recap: bool = False
    show_quiz: bool = False
    show_recall: bool = False
    max_bullets: int = 2
    difficulty_cap: str | None = None  # None means no cap
    reasoning: list[str] = field(default_factory=list)


def classify(user: User, video: Video) -> ClassificationResult:
    reasoning = []

    # Step 1: Content type from video metadata
    content_type = video.content_type
    reasoning.append(f"Content type: {content_type} (from video metadata)")

    # Step 2: User type from user record
    user_type = user.user_type
    reasoning.append(f"User type: {user_type} (from user record)")

    # Step 3: Maturity from user record
    maturity = user.maturity
    reasoning.append(f"Maturity: {maturity} (from user record)")

    # Step 4: Decision matrix
    if content_type in ("utility", "entertainment"):
        # Utility/entertainment: no recap, no quiz, no recall
        reasoning.append(
            f"{content_type} content: no learning loop (no recap, no quiz, no recall)"
        )
        return ClassificationResult(
            content_type=content_type,
            user_type=user_type,
            maturity=maturity,
            show_recap=False,
            show_quiz=False,
            show_recall=False,
            max_bullets=0,
            difficulty_cap=None,
            reasoning=reasoning,
        )

    # Aspiration content: branch on user type
    if user_type == "IS":
        reasoning.append(
            "IS user + aspiration: recap only (IS-toned, 2 bullets max, no quiz, no recall)"
        )
        return ClassificationResult(
            content_type=content_type,
            user_type=user_type,
            maturity=maturity,
            show_recap=True,
            show_quiz=False,
            show_recall=False,
            max_bullets=2,
            difficulty_cap=None,
            reasoning=reasoning,
        )

    if user_type == "converting":
        reasoning.append(
            "Converting user + aspiration: recap + quiz (medium difficulty cap, 2 bullets)"
        )
        return ClassificationResult(
            content_type=content_type,
            user_type=user_type,
            maturity=maturity,
            show_recap=True,
            show_quiz=True,
            show_recall=False,
            max_bullets=2,
            difficulty_cap="medium",
            reasoning=reasoning,
        )

    # AS user
    show_recall = maturity in ("warming_up", "established")
    recall_note = "recall enabled" if show_recall else "recall disabled (new user)"
    reasoning.append(
        f"AS user + aspiration: full loop (recap + quiz + {recall_note}, 3 bullets)"
    )
    return ClassificationResult(
        content_type=content_type,
        user_type=user_type,
        maturity=maturity,
        show_recap=True,
        show_quiz=True,
        show_recall=show_recall,
        max_bullets=3,
        difficulty_cap=None,
        reasoning=reasoning,
    )
