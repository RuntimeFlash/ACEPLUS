from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def build_available_tests_filter(standard: int, user_id: str, division: Optional[str]) -> Dict[str, Any]:
    assignment_filters: List[Dict[str, Any]] = [
        {"students": user_id},
        {
            "$and": [
                {"$or": [{"students": {"$exists": False}}, {"students": []}, {"students": None}]},
                {"$or": [{"division": {"$exists": False}}, {"division": None}, {"division": ""}]},
            ]
        },
    ]
    if division:
        assignment_filters.append({"division": division})

    return {
        "$and": [
            {"standard": int(standard), "completed_by": {"$ne": user_id}},
            {"$or": assignment_filters},
        ]
    }


def is_test_visible_to_student(test_doc: Dict[str, Any], user_id: str, division: Optional[str]) -> bool:
    completed_by = test_doc.get("completed_by", []) or []
    if user_id in completed_by:
        return False

    assigned_students = test_doc.get("students")
    assigned_division = test_doc.get("division")

    if assigned_students:
        return user_id in assigned_students
    if assigned_division:
        return bool(division and division == assigned_division)
    return True


def parse_expiration_datetime(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None
