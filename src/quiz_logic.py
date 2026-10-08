from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AnswerFeedback:
    question_number: int
    submitted_answer: str | None
    is_correct: bool
    correct_answer: str
    explanation: str
    source: str


@dataclass(frozen=True)
class QuizResult:
    question_count: int
    correct_count: int
    marks_awarded: int
    total_marks: int
    percentage: float
    grade: str
    feedback: tuple[AnswerFeedback, ...]


def grade_for_percentage(percentage: float) -> str:
    """Convert a percentage to the project's documented grade band."""
    if not 0 <= percentage <= 100:
        raise ValueError("percentage must be between 0 and 100.")
    if percentage >= 80:
        return "A"
    if percentage >= 70:
        return "B"
    if percentage >= 60:
        return "C"
    if percentage >= 50:
        return "D"
    return "F"


def grade_quiz(
    questions: list[dict[str, Any]],
    submitted_answers: list[str | None],
) -> QuizResult:
    """Mark one-point MCQs and return explanations for post-submission feedback."""
    if not questions:
        raise ValueError("A quiz must contain at least one question.")
    if len(questions) != len(submitted_answers):
        raise ValueError("Provide exactly one submitted answer per question.")

    feedback: list[AnswerFeedback] = []
    for index, (question, answer) in enumerate(zip(questions, submitted_answers), start=1):
        normalized_answer = answer.strip().upper() if isinstance(answer, str) else None
        correct_answer = question["correct_answer"]
        if question.get("question_type") == "Short answer":
            normalize_text = lambda value: " ".join(value.casefold().split())
            accepted_answers = {correct_answer, *question.get("accepted_answers", [])}
            is_correct = normalized_answer is not None and normalize_text(answer) in {
                normalize_text(value) for value in accepted_answers
            }
        else:
            is_correct = normalized_answer == correct_answer
        feedback.append(
            AnswerFeedback(
                question_number=index,
                submitted_answer=normalized_answer,
                is_correct=is_correct,
                correct_answer=correct_answer,
                explanation=question["explanation"],
                source=question["source"],
            )
        )

    correct_count = sum(item.is_correct for item in feedback)
    total_marks = len(questions)
    percentage = round(correct_count / total_marks * 100, 2)
    return QuizResult(
        question_count=total_marks,
        correct_count=correct_count,
        marks_awarded=correct_count,
        total_marks=total_marks,
        percentage=percentage,
        grade=grade_for_percentage(percentage),
        feedback=tuple(feedback),
    )
