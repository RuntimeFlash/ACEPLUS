from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from services.test_database_service import TestDatabaseService as DbTestsService


class _FakeTestRepo:
    def __init__(self, docs_by_standard: Dict[int, List[Dict[str, Any]]]) -> None:
        self.docs_by_standard = docs_by_standard
        self.filter_calls: List[Dict[str, Any]] = []
        self.inactive_upserts: List[Dict[str, Any]] = []
        self.delete_calls: List[Dict[str, Any]] = []

    def list_tests_with_filter(self, standard: int, mongo_filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        self.filter_calls.append({"standard": standard, "mongo_filter": mongo_filter})
        return [dict(doc) for doc in self.docs_by_standard.get(standard, [])]

    def upsert_inactive_test(self, standard: int, test_data: Dict[str, Any]) -> None:
        self.inactive_upserts.append({"standard": standard, "test_data": dict(test_data)})

    def delete_test_by_standard(self, standard: int, test_id: str) -> bool:
        self.delete_calls.append({"standard": standard, "test_id": test_id})
        return not test_id.endswith("-fail")


def test_get_available_tests_for_student_filters_and_strips_id() -> None:
    repo = _FakeTestRepo(
        {
            9: [
                {"_id": "1", "test-id": "t-1", "students": ["u1"], "completed_by": []},
                {"_id": "2", "test-id": "t-2", "students": ["u1"], "completed_by": ["u1"]},
                {"_id": "3", "test-id": "t-3", "division": "A", "completed_by": []},
                {"_id": "4", "test-id": "t-4", "division": "B", "completed_by": []},
                {"_id": "5", "test-id": "t-5", "completed_by": []},
            ]
        }
    )
    service = DbTestsService(repo)

    results = service.get_available_tests_for_student(standard=9, user_id="u1", division="A")
    test_ids = [doc["test-id"] for doc in results]

    assert test_ids == ["t-1", "t-3", "t-5"]
    assert all("_id" not in doc for doc in results)
    assert repo.filter_calls[0]["standard"] == 9
    assert "$and" in repo.filter_calls[0]["mongo_filter"]


def test_move_expired_tests_to_inactive_moves_only_expired() -> None:
    now = datetime.now(timezone.utc)
    expired = (now - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    future = (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z")

    repo = _FakeTestRepo(
        {
            9: [
                {"_id": "a", "test-id": "t-expired-ok", "expiration_date": expired},
                {"_id": "b", "test-id": "t-future", "expiration_date": future},
                {"_id": "c", "test-id": "t-invalid", "expiration_date": "not-a-date"},
            ],
            10: [
                {"_id": "d", "test-id": "t-expired-fail", "expiration_date": expired},
            ],
        }
    )
    service = DbTestsService(repo)

    moved = service.move_expired_tests_to_inactive()

    assert moved == 1
    assert len(repo.inactive_upserts) == 2
    assert len(repo.delete_calls) == 2
    assert all("_id" not in call["test_data"] for call in repo.inactive_upserts)
