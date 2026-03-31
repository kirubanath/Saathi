from datetime import datetime
from pydantic import BaseModel


# --- Shared sub-models ---

class RecapBulletSchema(BaseModel):
    concept: str
    bullet: str
    tone: str
    coverage_score: float
    gap_score: float
    rank: int


class QuestionSchema(BaseModel):
    concept: str
    difficulty: str
    question: str
    options: list[str]
    correct_index: int


class EvalResultSchema(BaseModel):
    concept: str
    correct: bool
    score: float


class RecommendationSchema(BaseModel):
    slot1: dict | None = None
    slot2: dict | None = None
    reasoning: list[str] = []


class RecallItemSchema(BaseModel):
    recall_id: int
    concept_key: str
    source_video_id: str
    question: dict
    due_at: datetime
    interval_hours: float


# --- Session Start ---

class SessionStartRequest(BaseModel):
    user_id: str
    simulated_time: datetime | None = None


class SessionStartResponse(BaseModel):
    recalls: list[RecallItemSchema]
    milestones: list[str]


# --- Recall Answer ---

class RecallAnswerRequest(BaseModel):
    user_id: str
    recall_id: int
    answer_index: int


class RecallAnswerResponse(BaseModel):
    correct: bool
    new_score: float
    next_interval_hours: float


# --- Video Complete ---

class VideoCompleteRequest(BaseModel):
    user_id: str
    video_id: str
    completion_rate: float = 1.0


class VideoCompleteResponse(BaseModel):
    classification: dict
    recap: list[RecapBulletSchema] | None = None
    questions: list[QuestionSchema] | None = None
    recommendation: RecommendationSchema | None = None


# --- Quiz Submit ---

class AnswerItem(BaseModel):
    concept: str
    answer_index: int


class QuizSubmitRequest(BaseModel):
    user_id: str
    video_id: str
    questions: list[QuestionSchema]
    answers: list[AnswerItem]


class QuizSubmitResponse(BaseModel):
    results: list[EvalResultSchema]
    progress: dict
    progress_message: str | None = None
    recommendation: RecommendationSchema
    recalls_scheduled: int
