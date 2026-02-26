from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from services.user_stats_service import UserStatsService


class _FakeUserRepo:
    def __init__(self, user: Optional[Dict[str, Any]], update_ok: bool = True) -> None:
        self._user = user
        self._update_ok = update_ok
        self.updated_payload: Optional[Dict[str, Any]] = None

    def get_user(self, user_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        return self._user

    def update_stats_and_exam_history(
        self,
        user_id: str,
        stats: Dict[str, Any],
        subjects: List[Dict[str, Any]],
        exam_overview: Dict[str, Any],
        is_class10: Optional[bool] = None,
    ) -> bool:
        self.updated_payload = {
            "user_id": user_id,
            "stats": stats,
            "subjects": subjects,
            "exam_overview": exam_overview,
            "is_class10": is_class10,
        }
        return self._update_ok


def test_update_stats_after_exam_success() -> None:
    user = {
        "id": "u1",
        "stats": {"attempted": 1, "correct": 8, "questions": 10, "avgPercentage": 80.0},
        "subjects": [
            {
                "subject": "Math",
                "attempted": 1,
                "avgPercentage": 80.0,
                "marksGained": 8,
                "marksAttempted": 10,
                "highestMark": 90.0,
                "lowestMark": 80.0,
            }
        ],
        "examHistory": [],
    }
    repo = _FakeUserRepo(user=user, update_ok=True)
    service = UserStatsService(repo)

    overall, subject_stats = service.update_stats_after_exam(
        user_id="u1",
        subject="Math",
        score=2,
        total_questions=4,
        percentage=50.0,
        exam_id="exam-1",
        lessons=["L1", "L2"],
        test=True,
        test_name="Weekly Test",
        is_class10=False,
    )

    assert overall["attempted"] == 2
    assert overall["correct"] == 10
    assert overall["questions"] == 14
    assert overall["avgPercentage"] == 71.43
    assert subject_stats["attempted"] == 2
    assert subject_stats["marksGained"] == 10
    assert subject_stats["marksAttempted"] == 14
    assert subject_stats["highestMark"] == 90.0
    assert subject_stats["lowestMark"] == 50.0

    assert repo.updated_payload is not None
    assert repo.updated_payload["user_id"] == "u1"
    assert repo.updated_payload["is_class10"] is False
    assert repo.updated_payload["exam_overview"]["exam-id"] == "exam-1"
    assert repo.updated_payload["exam_overview"]["test"] is True
    assert repo.updated_payload["exam_overview"]["test_name"] == "Weekly Test"


def test_update_stats_after_exam_user_not_found() -> None:
    service = UserStatsService(_FakeUserRepo(user=None))
    with pytest.raises(ValueError, match="not found"):
        service.update_stats_after_exam(
            user_id="missing",
            subject="Math",
            score=1,
            total_questions=2,
            percentage=50.0,
            exam_id="exam-1",
            lessons=["L1"],
        )


def test_update_stats_after_exam_update_failure() -> None:
    user = {"id": "u1", "stats": {}, "subjects": [], "examHistory": []}
    service = UserStatsService(_FakeUserRepo(user=user, update_ok=False))
    with pytest.raises(ValueError, match="Failed to update stats"):
        service.update_stats_after_exam(
            user_id="u1",
            subject="Science",
            score=1,
            total_questions=2,
            percentage=50.0,
            exam_id="exam-1",
            lessons=["L1"],
        )
