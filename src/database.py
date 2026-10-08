import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.quiz_logic import QuizResult


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "quiz_results.sqlite3"


def initialize_database(db_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
    """Create the quiz history table if it does not already exist."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                completed_at TEXT NOT NULL,
                subject TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                question_count INTEGER NOT NULL,
                correct_count INTEGER NOT NULL,
                marks_awarded INTEGER NOT NULL,
                total_marks INTEGER NOT NULL,
                percentage REAL NOT NULL,
                grade TEXT NOT NULL,
                source_file TEXT NOT NULL
            )
            """
        )


def save_quiz_result(
    subject: str,
    difficulty: str,
    result: QuizResult,
    source_file: str,
    db_path: str | Path = DEFAULT_DATABASE_PATH,
) -> int:
    """Save a completed quiz and return its generated database ID."""
    initialize_database(db_path)
    completed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO quiz_results (
                completed_at, subject, difficulty, question_count, correct_count,
                marks_awarded, total_marks, percentage, grade, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                completed_at,
                subject,
                difficulty,
                result.question_count,
                result.correct_count,
                result.marks_awarded,
                result.total_marks,
                result.percentage,
                result.grade,
                source_file,
            ),
        )
        return int(cursor.lastrowid)


def get_recent_results(
    limit: int = 20,
    db_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict[str, Any]]:
    """Return recent quiz history without exposing any uploaded note contents."""
    if limit < 1:
        raise ValueError("limit must be at least one.")

    initialize_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, completed_at, subject, difficulty, question_count,
                   correct_count, marks_awarded, total_marks, percentage, grade,
                   source_file
            FROM quiz_results
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
