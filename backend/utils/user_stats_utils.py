from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from utils.date_utils import current_ist_date_str


_DEFAULT_SUBJECTS = ["Math", "SS", "English", "Science"]


def default_subject_stats(subject: str) -> Dict[str, Any]:
    return {
        "subject": subject,
        "attempted": 0,
        "avgPercentage": 0.0,
        "marksGained": 0,
        "marksAttempted": 0,
        "highestMark": 0.0,
        "lowestMark": 0.0,
    }


def build_user_doc(
    user_id: str,
    password: Optional[str],
    name: str,
    roll_no: int,
    division: str,
    standard: int,
    teacher: bool = False,
) -> Dict[str, Any]:
    return {
        "id": user_id,
        "name": name,
        "password": password,
        "rollno": roll_no,
        "division": division,
        "standard": int(standard),
        "teacher": teacher,
        "coins": 0,
        "tasks": {"generated_at": None, "tasks_list": []},
        "stats": {"attempted": 0, "correct": 0, "questions": 0, "avgPercentage": 0.0},
        "subjects": [default_subject_stats(subj) for subj in _DEFAULT_SUBJECTS],
        "examHistory": [],
    }


def compute_exam_stats_update(
    user_doc: Dict[str, Any],
    subject: str,
    score: int,
    total_questions: int,
    percentage: float,
    exam_id: str,
    lessons: List[str],
    test: bool = False,
    test_name: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    overall = dict(user_doc.get("stats", {"attempted": 0, "correct": 0, "questions": 0, "avgPercentage": 0.0}))
    attempted = int(overall.get("attempted", 0)) + 1
    correct = int(overall.get("correct", 0)) + score
    questions = int(overall.get("questions", 0)) + total_questions
    avg_percentage = (correct / questions * 100.0) if questions > 0 else 0.0
    overall.update(
        {
            "attempted": attempted,
            "correct": correct,
            "questions": questions,
            "avgPercentage": round(avg_percentage, 2),
        }
    )

    subjects = [dict(s) for s in (user_doc.get("subjects", []) or [])]
    subject_stats = None
    for existing in subjects:
        if existing.get("subject") == subject:
            subject_stats = existing
            break

    if subject_stats is None:
        subject_stats = default_subject_stats(subject)
        subjects.append(subject_stats)

    subject_attempted = int(subject_stats.get("attempted", 0)) + 1
    marks_gained = int(subject_stats.get("marksGained", 0)) + score
    marks_attempted = int(subject_stats.get("marksAttempted", 0)) + total_questions
    subject_avg = (marks_gained / marks_attempted * 100.0) if marks_attempted > 0 else 0.0
    subject_high = max(float(subject_stats.get("highestMark", 0.0)), float(percentage))
    previous_low = float(subject_stats.get("lowestMark", 0.0))
    subject_low = (
        float(percentage)
        if previous_low == 0.0 and subject_attempted == 1
        else (min(previous_low, float(percentage)) if previous_low > 0 else float(percentage))
    )
    subject_stats.update(
        {
            "attempted": subject_attempted,
            "avgPercentage": round(subject_avg, 2),
            "marksGained": marks_gained,
            "marksAttempted": marks_attempted,
            "highestMark": round(subject_high, 2),
            "lowestMark": round(subject_low, 2),
        }
    )

    exam_overview = {
        "exam-id": exam_id,
        "subject": subject,
        "score": score,
        "totalQuestions": total_questions,
        "percentage": percentage,
        "lessons": lessons or [],
        "date": current_ist_date_str(),
        "test": bool(test),
    }
    if test and test_name:
        exam_overview["test_name"] = test_name

    return overall, subjects, exam_overview, subject_stats


def to_student_summary(student_doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": student_doc.get("id"),
        "name": student_doc.get("name"),
        "division": student_doc.get("division"),
        "roll": student_doc.get("rollno"),
    }
