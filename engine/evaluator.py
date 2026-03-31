from dataclasses import dataclass
from engine.quiz_engine import Question


@dataclass
class EvalResult:
    concept: str
    correct: bool
    score: float  # 1.0 or 0.0


def evaluate(questions: list[Question], answers: list[int]) -> list[EvalResult]:
    results = []
    for question, answer in zip(questions, answers):
        correct = answer == question.correct_index
        results.append(
            EvalResult(
                concept=question.concept,
                correct=correct,
                score=1.0 if correct else 0.0,
            )
        )
    return results
