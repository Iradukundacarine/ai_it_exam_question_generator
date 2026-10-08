import pytest

from src.database import get_recent_results, save_quiz_result
from src.quiz_logic import grade_for_percentage, grade_quiz


def make_questions(count: int = 2) -> list[dict]:
    return [
        {
            "question": f"Question {index}",
            "options": {"A": "first", "B": "second", "C": "third", "D": "fourth"},
            "correct_answer": "B",
            "explanation": f"Explanation {index}",
            "source": f"Source {index}",
        }
        for index in range(count)
    ]


def test_quiz_marking_calculates_score_and_feedback() -> None:
    result = grade_quiz(make_questions(), ["b", None])

    assert result.correct_count == 1
    assert result.marks_awarded == 1
    assert result.total_marks == 2
    assert result.percentage == 50.0
    assert result.grade == "D"
    assert result.feedback[0].is_correct is True
    assert result.feedback[1].correct_answer == "B"
    assert result.feedback[1].explanation == "Explanation 1"


def test_quiz_rejects_empty_questions_or_answer_count_mismatch() -> None:
    with pytest.raises(ValueError, match="at least one"):
        grade_quiz([], [])
    with pytest.raises(ValueError, match="exactly one"):
        grade_quiz(make_questions(), ["A"])


def test_short_answer_accepts_normalized_aliases() -> None:
    question = {
        "question_type": "Short answer",
        "correct_answer": "Domain Name System",
        "accepted_answers": ["DNS"],
        "explanation": "DNS translates domain names into IP addresses.",
        "source": "The notes define DNS.",
    }

    result = grade_quiz([question], ["  dns  "])

    assert result.correct_count == 1
    assert result.feedback[0].is_correct is True


def test_grade_boundaries() -> None:
    assert [grade_for_percentage(score) for score in (100, 80, 79, 70, 69, 60, 59, 50, 49)] == [
        "A", "A", "B", "B", "C", "C", "D", "D", "F"
    ]
    with pytest.raises(ValueError):
        grade_for_percentage(101)


def test_database_saves_and_returns_recent_results(tmp_path) -> None:
    database_path = tmp_path / "history.sqlite3"
    result = grade_quiz(make_questions(), ["B", "A"])

    result_id = save_quiz_result(
        "Networking",
        "Easy",
        result,
        "networking_fundamentals.pdf",
        db_path=database_path,
    )
    history = get_recent_results(db_path=database_path)

    assert result_id == 1
    assert len(history) == 1
    assert history[0]["subject"] == "Networking"
    assert history[0]["percentage"] == 50.0
    assert history[0]["source_file"] == "networking_fundamentals.pdf"
    assert len(history[0]["completed_at"]) > 10


def test_history_limit_must_be_positive(tmp_path) -> None:
    with pytest.raises(ValueError, match="limit"):
        get_recent_results(limit=0, db_path=tmp_path / "history.sqlite3")
