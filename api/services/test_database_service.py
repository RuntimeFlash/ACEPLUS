from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from utils.test_utils import build_available_tests_filter, is_test_visible_to_student, parse_expiration_datetime


class TestDatabaseService:
    def __init__(self, test_repo: Any) -> None:
        self.test_repo = test_repo

    def get_available_tests_for_student(
        self,
        standard: int,
        user_id: str,
        division: Optional[str],
    ) -> List[Dict[str, Any]]:
        docs = self.test_repo.list_tests_with_filter(
            standard=standard,
            mongo_filter=build_available_tests_filter(standard, user_id, division),
        )
        results: List[Dict[str, Any]] = []
        for doc in docs:
            if not is_test_visible_to_student(doc, user_id, division):
                continue
            payload = dict(doc)
            payload.pop("_id", None)
            results.append(payload)
        return results

    def move_expired_tests_to_inactive(self) -> int:
        now = datetime.now(timezone.utc)
        total_moved = 0
        for standard in (9, 10):
            tests = self.test_repo.list_tests_with_filter(standard=standard, mongo_filter={})
            for test_doc in tests:
                exp_dt = parse_expiration_datetime(test_doc.get("expiration_date"))
                if exp_dt is None or exp_dt >= now:
                    continue
                test_copy = dict(test_doc)
                test_copy.pop("_id", None)
                self.test_repo.upsert_inactive_test(standard=standard, test_data=test_copy)
                if self.test_repo.delete_test_by_standard(standard=standard, test_id=test_copy["test-id"]):
                    total_moved += 1
        return total_moved
