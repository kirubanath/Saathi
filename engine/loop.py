from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy.orm import Session
from db.models import User, Video, WatchHistory
from db.operations import get_user, get_video, add_watch_history
from storage.base import get_storage_client
from engine.classifier import classify, ClassificationResult
from engine.recap_engine import generate_recap, RecapResult
from engine.quiz_engine import select_questions, Question
from engine.evaluator import evaluate, EvalResult
from engine.knowledge_updater import update_from_watch, update_from_quiz, KnowledgeUpdate
from engine.progress_update import generate_progress_message
from engine.recommender import recommend, RecommendationResult
from engine.recall_scheduler import schedule_recalls, RecallEntry


@dataclass
class LoopResult:
    classification: ClassificationResult
    recap: RecapResult | None = None
    questions: list[Question] | None = None
    recommendation: RecommendationResult | None = None
    watch_update: KnowledgeUpdate | None = None
    reasoning: list[str] = field(default_factory=list)


@dataclass
class QuizResult:
    eval_results: list[EvalResult]
    quiz_update: KnowledgeUpdate
    score_delta: dict
    progress_message: str | None = None
    recommendation: RecommendationResult | None = None
    recalls_scheduled: int = 0
    reasoning: list[str] = field(default_factory=list)


def _load_artifacts(video_id: str) -> dict:
    storage = get_storage_client()
    prefix = f"videos/{video_id}"
    return {
        "concept_profile": storage.get_json(f"{prefix}/concept_profile.json"),
        "recap_bullets": storage.get_json(f"{prefix}/recap_bullets.json"),
        "questions": storage.get_json(f"{prefix}/questions.json"),
    }


def run_video_complete_loop(
    db: Session,
    user_id: str,
    video_id: str,
    completion_rate: float = 1.0,
) -> LoopResult:
    user = get_user(db, user_id)
    video = get_video(db, video_id)
    reasoning = []

    # Step 1: Classify
    classification = classify(user, video)
    reasoning.extend(classification.reasoning)

    # Step 2: Record watch history (for all content types)
    add_watch_history(db, user_id, video_id, video.category, completion_rate, {})
    # Refresh user after DB update
    db.refresh(user)

    result = LoopResult(classification=classification, reasoning=reasoning)

    if video.content_type != "aspiration":
        # Utility/entertainment: no learning loop, just recommend
        reasoning.append("Non-aspiration content: skipping learning loop")
        result.recommendation = recommend(db, user, video)
        reasoning.extend(result.recommendation.reasoning)
        return result

    # Step 3: Load artifacts and apply watch bump (all user types for aspiration)
    artifacts = _load_artifacts(video_id)
    watch_update = update_from_watch(
        db, user, video.category, artifacts["concept_profile"], completion_rate
    )
    result.watch_update = watch_update
    # Refresh user after knowledge state update
    db.refresh(user)
    reasoning.append(
        "Watch bump applied: " + ", ".join(
            f"{c}={d['after']:.2f}" for c, d in watch_update.delta.items()
        )
    )

    # Step 4: Generate recap (if applicable)
    if classification.show_recap:
        recap = generate_recap(user, artifacts, classification)
        result.recap = recap
        reasoning.extend(recap.reasoning)

    # Step 5: Branch on quiz requirement
    if classification.show_quiz:
        # Quiz path: select questions and return (caller will submit answers)
        recap_concepts = [b.concept for b in recap.bullets] if recap else []
        questions = select_questions(user, artifacts, recap_concepts, classification)
        result.questions = questions
        reasoning.append(
            f"Quiz path: {len(questions)} questions selected "
            f"(user will submit answers via run_quiz_submit)"
        )
    else:
        # No-quiz path: run recommender now
        reasoning.append("No-quiz path: running recommender")
        result.recommendation = recommend(db, user, video)
        reasoning.extend(result.recommendation.reasoning)

    return result


def run_quiz_submit(
    db: Session,
    user_id: str,
    video_id: str,
    questions: list[Question],
    answers: list[int],
    as_of: datetime | None = None,
) -> QuizResult:
    user = get_user(db, user_id)
    video = get_video(db, video_id)
    reasoning = []

    # Step 1: Evaluate responses
    eval_results = evaluate(questions, answers)
    reasoning.append(
        f"Evaluation: {sum(1 for r in eval_results if r.correct)}/{len(eval_results)} correct"
    )

    # Step 2: Update knowledge from quiz (watch bump already applied)
    quiz_update = update_from_quiz(db, user, video.category, eval_results)
    db.refresh(user)
    reasoning.append(
        "Quiz update: " + ", ".join(
            f"{c}={d['after']:.2f}" for c, d in quiz_update.delta.items()
        )
    )

    # Step 3: Record quiz scores in watch history
    # Update the most recent watch history entry with quiz scores
    quiz_scores = {r.concept: r.score for r in eval_results}
    latest_watch = (
        db.query(WatchHistory)
        .filter_by(user_id=user_id, video_id=video_id)
        .order_by(WatchHistory.id.desc())
        .first()
    )
    if latest_watch:
        latest_watch.quiz_scores = quiz_scores
        db.commit()

    # Step 4: Progress message (AS and Converting only)
    progress_message = None
    if user.user_type in ("AS", "converting"):
        progress_message = generate_progress_message(user, quiz_update.delta)
        reasoning.append(f"Progress message: {progress_message}")
    else:
        reasoning.append("IS user: no progress message")

    # Step 5: Recommend
    recommendation = recommend(db, user, video)
    reasoning.extend(recommendation.reasoning)

    # Step 6: Schedule recalls (AS warming_up/established only)
    recall_entries = schedule_recalls(
        db, user, eval_results, video_id, video.category, as_of
    )
    reasoning.append(f"Recalls scheduled: {len(recall_entries)}")

    return QuizResult(
        eval_results=eval_results,
        quiz_update=quiz_update,
        score_delta=quiz_update.delta,
        progress_message=progress_message,
        recommendation=recommendation,
        recalls_scheduled=len(recall_entries),
        reasoning=reasoning,
    )
