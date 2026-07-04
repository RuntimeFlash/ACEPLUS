from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.date_utils import month_key_from_date_str


def calculate_elo_change(score_percentage: float, num_lessons: int, subject: str) -> int:
    base_multiplier = 32
    subject_weights = {
        "Mathematics": 1.5,
        "Science": 1.2,
        "Social Studies": 1.0,
        "Math": 1.5,
        "SS": 1.0,
    }
    subject_weight = subject_weights.get(subject, 1.0)
    lesson_multiplier = 1 + (num_lessons * 0.1)
    performance_multiplier = score_percentage / 100.0
    return round(base_multiplier * subject_weight * lesson_multiplier * performance_multiplier)


def build_display_name(name: str) -> str:
    name_parts = (name or "").split()
    if len(name_parts) >= 2:
        return f"{name_parts[0].upper()} {name_parts[-1].upper()}"
    if len(name_parts) == 1:
        return name_parts[0].upper()
    return "UNKNOWN"


def entry_from_user_for_month(user_doc: Dict[str, Any], month_key: str) -> Optional[Dict[str, Any]]:
    user_id = user_doc.get("id")
    if not user_id:
        return None

    exam_history = user_doc.get("examHistory", []) or []
    total_exams = 0
    total_score = 0
    total_questions = 0
    elo_score = 0

    for exam in exam_history:
        if month_key_from_date_str(exam.get("date", "")) != month_key:
            continue
        total_exams += 1
        score = int(exam.get("score", 0))
        question_count = int(exam.get("totalQuestions", 0))
        total_score += score
        total_questions += question_count
        pct = float(exam.get("percentage", 0.0))
        subject = exam.get("subject", "")
        lessons = exam.get("lessons", []) or []
        elo_score += calculate_elo_change(pct, len(lessons), subject)

    return {
        "userId": user_id,
        "name": build_display_name(user_doc.get("name", "UNKNOWN")),
        "division": user_doc.get("division", "N/A"),
        "total_exams": total_exams,
        "coins": user_doc.get("coins", 0),
        "elo_score": elo_score,
        "has_taken_exam": total_exams > 0,
        "total_score": total_score,
        "total_questions": total_questions,
        "average_percentage": (total_score / total_questions * 100.0) if total_questions > 0 else 0.0,
    }


def sort_entries(entries: List[Dict[str, Any]]) -> None:
    entries.sort(
        key=lambda x: (x.get("has_taken_exam", False), x.get("elo_score", 0), x.get("coins", 0)),
        reverse=True,
    )


def generate_version(month_key: str) -> str:
    return hashlib.sha256(f"{month_key}-{datetime.now().timestamp()}".encode()).hexdigest()[:8]
