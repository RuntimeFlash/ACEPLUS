from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from utils.user_stats_utils import compute_exam_stats_update


class UserStatsService:
    def __init__(self, user_repo: Any) -> None:
        self.user_repo = user_repo

    def update_stats_after_exam(
        self,
        user_id: str,
        subject: str,
        score: int,
        total_questions: int,
        percentage: float,
        exam_id: str,
        lessons: List[str],
        test: bool = False,
        test_name: Optional[str] = None,
        is_class10: Optional[bool] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        user = self.user_repo.get_user(user_id, is_class10)
        if not user:
            raise ValueError(f"User {user_id} not found")

        overall, subjects, overview, subject_stats = compute_exam_stats_update(
            user_doc=user,
            subject=subject,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            exam_id=exam_id,
            lessons=lessons,
            test=test,
            test_name=test_name,
        )
        updated = self.user_repo.update_stats_and_exam_history(
            user_id=user_id,
            stats=overall,
            subjects=subjects,
            exam_overview=overview,
            is_class10=is_class10,
        )
        if not updated:
            raise ValueError(f"Failed to update stats for user {user_id}")
        return overall, subject_stats
