from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas import (
    AnswerItem,
    EvalResultSchema,
    QuestionSchema,
    RecallAnswerRequest,
    RecallAnswerResponse,
    RecallItemSchema,
    RecapBulletSchema,
    RecommendationSchema,
    SessionStartRequest,
    SessionStartResponse,
    VideoCompleteRequest,
    VideoCompleteResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from db.base import get_db
from db.models import RecallQueue
from db.operations import get_user, get_video
from engine.knowledge_updater import update_from_recall
from engine.loop import run_video_complete_loop, run_quiz_submit
from engine.quiz_engine import Question
from engine.recall_scheduler import get_pending_recalls, process_recall_result
from preprocessing.pipeline import preprocess_all
from storage.base import get_storage_client

router = APIRouter()


def _recap_to_schema(recap_result):
    if recap_result is None:
        return None
    return [
        RecapBulletSchema(
            concept=b.concept,
            bullet=b.bullet,
            tone=b.tone,
            coverage_score=b.coverage_score,
            gap_score=b.gap_score,
            rank=b.rank,
        )
        for b in recap_result.bullets
    ]


def _questions_to_schema(questions):
    if questions is None:
        return None
    return [
        QuestionSchema(
            concept=q.concept,
            difficulty=q.difficulty,
            question=q.question,
            options=q.options,
            correct_index=q.correct_index,
        )
        for q in questions
    ]


def _recommendation_to_schema(rec):
    if rec is None:
        return None
    return RecommendationSchema(
        slot1=rec.slot1,
        slot2=rec.slot2,
        reasoning=rec.reasoning,
    )


@router.post("/session/start", response_model=SessionStartResponse)
def session_start(req: SessionStartRequest, db: Session = Depends(get_db)):
    user = get_user(db, req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")

    recalls = get_pending_recalls(db, req.user_id, req.simulated_time)
    recall_schemas = [
        RecallItemSchema(
            recall_id=r.recall_id,
            concept_key=r.concept_key,
            source_video_id=r.source_video_id,
            question=r.question,
            due_at=r.due_at,
            interval_hours=r.interval_hours,
        )
        for r in recalls
    ]
    return SessionStartResponse(recalls=recall_schemas, milestones=[])


@router.post("/recall/answer", response_model=RecallAnswerResponse)
def recall_answer(req: RecallAnswerRequest, db: Session = Depends(get_db)):
    user = get_user(db, req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")

    recall = db.get(RecallQueue, req.recall_id)
    if not recall:
        raise HTTPException(status_code=404, detail=f"Recall {req.recall_id} not found")

    # Load question from storage to determine correctness
    category, concept = recall.concept_key.split("/", 1)
    storage = get_storage_client()
    questions_data = storage.get_json(f"videos/{recall.source_video_id}/questions.json")
    concept_questions = questions_data.get(concept, {})

    # Find the question that matches (try medium, easy, hard - same order as get_pending_recalls)
    question = None
    for difficulty in ("medium", "easy", "hard"):
        if difficulty in concept_questions:
            question = concept_questions[difficulty]
            break

    correct = False
    if question:
        correct = req.answer_index == question.get("correct_index")

    # Update recall interval
    recall_update = process_recall_result(db, recall, correct)

    # Update knowledge state
    result_score = 1.0 if correct else 0.0
    knowledge_update = update_from_recall(db, user, recall.concept_key, result_score)
    db.refresh(user)

    # Get the new score for the concept
    category, concept = recall.concept_key.split("/", 1)
    new_score = knowledge_update.updated_state.get(concept, 0.0)

    return RecallAnswerResponse(
        correct=correct,
        new_score=new_score,
        next_interval_hours=recall_update.new_interval,
    )


@router.post("/video/complete", response_model=VideoCompleteResponse)
def video_complete(req: VideoCompleteRequest, db: Session = Depends(get_db)):
    user = get_user(db, req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")

    video = get_video(db, req.video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {req.video_id} not found")

    result = run_video_complete_loop(db, req.user_id, req.video_id, req.completion_rate)

    classification_dict = {
        "content_type": result.classification.content_type,
        "user_type": result.classification.user_type,
        "maturity": result.classification.maturity,
        "show_recap": result.classification.show_recap,
        "show_quiz": result.classification.show_quiz,
        "show_recall": result.classification.show_recall,
        "max_bullets": result.classification.max_bullets,
        "difficulty_cap": result.classification.difficulty_cap,
        "reasoning": result.classification.reasoning,
    }

    return VideoCompleteResponse(
        classification=classification_dict,
        recap=_recap_to_schema(result.recap),
        questions=_questions_to_schema(result.questions),
        recommendation=_recommendation_to_schema(result.recommendation),
    )


@router.post("/quiz/submit", response_model=QuizSubmitResponse)
def quiz_submit(req: QuizSubmitRequest, db: Session = Depends(get_db)):
    user = get_user(db, req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")

    video = get_video(db, req.video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {req.video_id} not found")

    # Reconstruct engine Question objects from request
    questions = [
        Question(
            concept=q.concept,
            difficulty=q.difficulty,
            question=q.question,
            options=q.options,
            correct_index=q.correct_index,
        )
        for q in req.questions
    ]

    # Build answer indices in the same order as questions
    answer_map = {a.concept: a.answer_index for a in req.answers}
    answers = [answer_map[q.concept] for q in questions]

    result = run_quiz_submit(db, req.user_id, req.video_id, questions, answers)

    return QuizSubmitResponse(
        results=[
            EvalResultSchema(concept=r.concept, correct=r.correct, score=r.score)
            for r in result.eval_results
        ],
        progress=result.score_delta,
        progress_message=result.progress_message,
        recommendation=_recommendation_to_schema(result.recommendation),
        recalls_scheduled=result.recalls_scheduled,
    )


@router.post("/admin/preprocess")
def admin_preprocess():
    results = preprocess_all()
    return {"status": "ok", "videos_processed": len(results), "results": results}
