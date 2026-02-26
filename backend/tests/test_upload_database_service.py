from __future__ import annotations

from typing import Any, Dict, List

from services.upload_database_service import UploadDatabaseService


class _FakeUploadRepo:
    def __init__(self, docs: List[Dict[str, Any]], deletions: Dict[str, bool]) -> None:
        self.docs = [dict(doc) for doc in docs]
        self.deletions = deletions
        self.delete_calls: List[str] = []

    def list_user_file_sizes_since(self, user_id: str, is_class10: bool, cutoff: Any) -> List[Dict[str, Any]]:
        return [dict(doc) for doc in self.docs]

    def delete_file(self, file_id: str, is_class10: bool, delete_children: bool = True) -> bool:
        self.delete_calls.append(file_id)
        return self.deletions.get(file_id, True)


def test_enforce_user_bytes_cap_deletes_until_under_limit() -> None:
    repo = _FakeUploadRepo(
        docs=[
            {"_id": "a", "length": 60},
            {"_id": "b", "length": 50},
            {"_id": "c", "length": 30},
        ],
        deletions={"a": True, "b": True, "c": True},
    )
    service = UploadDatabaseService(repo)

    service.enforce_user_bytes_cap(user_id="u1", is_class10=False, bytes_limit=100)

    assert repo.delete_calls == ["a"]


def test_enforce_user_bytes_cap_continues_when_delete_fails() -> None:
    repo = _FakeUploadRepo(
        docs=[
            {"_id": "a", "length": 60},
            {"_id": "b", "length": 50},
        ],
        deletions={"a": False, "b": True},
    )
    service = UploadDatabaseService(repo)

    service.enforce_user_bytes_cap(user_id="u1", is_class10=False, bytes_limit=40)

    assert repo.delete_calls == ["a", "b"]
