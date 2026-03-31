import copy

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas import (
    AnswerItem,
    EvalResultSchema,
    QuestionSchema,
    RecallAnswerRequest,
    RecallAnswerResponse,
    RecallItemSchema,
    RecallScheduledSchema,
    RecapBulletSchema,
    RecommendationSchema,
    SessionStartRequest,
    SessionStartResponse,
    UserListResponse,
    UserProfileResponse,
    UserProfileSchema,
    VideoCompleteRequest,
    VideoCompleteResponse,
    VideoListResponse,
    VideoSchema,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from db.base import get_db
from db.models import RecallQueue, User, Video
from db.operations import get_user, get_video
from engine.knowledge_updater import update_from_recall
from engine.loop import run_video_complete_loop, run_quiz_submit
from engine.quiz_engine import Question
from engine.recall_scheduler import get_pending_recalls, process_recall_result
from preprocessing.pipeline import preprocess_all
from storage.base import get_storage_client

router = APIRouter()


def _user_to_schema(user) -> UserProfileSchema:
    return UserProfileSchema(
        user_id=user.user_id,
        user_type=user.user_type,
        maturity=user.maturity,
        total_videos_watched=user.total_videos_watched,
        knowledge_state=copy.deepcopy(user.knowledge_state) if user.knowledge_state else {},
    )


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


@router.get("/user/{user_id}", response_model=UserProfileResponse)
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return UserProfileResponse(user=_user_to_schema(user))


@router.get("/users", response_model=UserListResponse)
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return UserListResponse(users=[_user_to_schema(u) for u in users])


@router.get("/videos", response_model=VideoListResponse)
def list_videos(db: Session = Depends(get_db)):
    videos = db.query(Video).order_by(Video.video_id).all()
    return VideoListResponse(
        videos=[
            VideoSchema(
                video_id=v.video_id,
                title=v.title,
                content_type=v.content_type,
                category=v.category,
            )
            for v in videos
        ]
    )


@router.post("/session/start", response_model=SessionStartResponse)
def session_start(req: SessionStartRequest, db: Session = Depends(get_db)):
    user = get_user(db, req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")

    knowledge_before = copy.deepcopy(user.knowledge_state) if user.knowledge_state else {}

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
    return SessionStartResponse(
        recalls=recall_schemas,
        milestones=[],
        user_data=_user_to_schema(user),
        knowledge_before=knowledge_before,
    )


@router.post("/recall/answer", response_model=RecallAnswerResponse)
def recall_answer(req: RecallAnswerRequest, db: Session = Depends(get_db)):
    user = get_user(db, req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")

    recall = db.get(RecallQueue, req.recall_id)
    if not recall:
        raise HTTPException(status_code=404, detail=f"Recall {req.recall_id} not found")

    category, concept = recall.concept_key.split("/", 1)
    storage = get_storage_client()
    questions_data = storage.get_json(f"videos/{recall.source_video_id}/questions.json")
    concept_questions = questions_data.get(concept, {})

    question = None
    for difficulty in ("medium", "easy", "hard"):
        if difficulty in concept_questions:
            question = concept_questions[difficulty]
            break

    correct = False
    if question:
        correct = req.answer_index == question.get("correct_index")

    recall_update = process_recall_result(db, recall, correct)

    result_score = 1.0 if correct else 0.0
    knowledge_update = update_from_recall(db, user, recall.concept_key, result_score)
    db.refresh(user)

    new_score = knowledge_update.updated_state.get(concept, 0.0)

    return RecallAnswerResponse(
        correct=correct,
        new_score=new_score,
        next_interval_hours=recall_update.new_interval,
        knowledge_delta=copy.deepcopy(knowledge_update.delta),
        knowledge_after=copy.deepcopy(user.knowledge_state) if user.knowledge_state else {},
    )


@router.post("/video/complete", response_model=VideoCompleteResponse)
def video_complete(req: VideoCompleteRequest, db: Session = Depends(get_db)):
    user = get_user(db, req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")

    video = get_video(db, req.video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {req.video_id} not found")

    user_data = _user_to_schema(user)

    result = run_video_complete_loop(db, req.user_id, req.video_id, req.completion_rate)
    db.refresh(user)

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

    watch_update_delta = None
    if result.watch_update:
        watch_update_delta = copy.deepcopy(result.watch_update.delta)

    recap_reasoning = []
    if result.recap:
        recap_reasoning = list(result.recap.reasoning)

    knowledge_after_watch = copy.deepcopy(user.knowledge_state) if user.knowledge_state else {}

    return VideoCompleteResponse(
        classification=classification_dict,
        recap=_recap_to_schema(result.recap),
        questions=_questions_to_schema(result.questions),
        recommendation=_recommendation_to_schema(result.recommendation),
        watch_update_delta=watch_update_delta,
        recap_reasoning=recap_reasoning,
        reasoning=list(result.reasoning),
        user_data=user_data,
        knowledge_after_watch=knowledge_after_watch,
    )


@router.post("/quiz/submit", response_model=QuizSubmitResponse)
def quiz_submit(req: QuizSubmitRequest, db: Session = Depends(get_db)):
    user = get_user(db, req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {req.user_id} not found")

    video = get_video(db, req.video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {req.video_id} not found")

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

    answer_map = {a.concept: a.answer_index for a in req.answers}
    answers = [answer_map[q.concept] for q in questions]

    result = run_quiz_submit(db, req.user_id, req.video_id, questions, answers)
    db.refresh(user)

    recall_details = [
        RecallScheduledSchema(
            concept_key=r.concept_key,
            source_video_id=r.source_video_id,
            due_at=r.due_at,
            interval_hours=r.interval_hours,
        )
        for r in result.recall_entries
    ]

    return QuizSubmitResponse(
        results=[
            EvalResultSchema(concept=r.concept, correct=r.correct, score=r.score)
            for r in result.eval_results
        ],
        progress=result.score_delta,
        progress_message=result.progress_message,
        recommendation=_recommendation_to_schema(result.recommendation),
        recalls_scheduled=result.recalls_scheduled,
        recall_details=recall_details,
        reasoning=list(result.reasoning),
        knowledge_after_quiz=copy.deepcopy(user.knowledge_state) if user.knowledge_state else {},
    )


@router.post("/admin/preprocess")
def admin_preprocess():
    results = preprocess_all()
    return {"status": "ok", "videos_processed": len(results), "results": results}
