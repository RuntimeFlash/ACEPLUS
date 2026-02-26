from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from services.leaderboard_service import LeaderboardService


class _FakeLeaderboardRepo:
    def __init__(self, users_by_standard: Dict[int, List[Dict[str, Any]]]) -> None:
        self.users_by_standard = users_by_standard
        self.snapshots: Dict[Tuple[int, str], Dict[str, Any]] = {}
        self.upsert_calls: List[Dict[str, Any]] = []

    def get_monthly_snapshot(self, standard: int, month_key: str) -> Optional[Dict[str, Any]]:
        snapshot = self.snapshots.get((standard, month_key))
        return dict(snapshot) if snapshot else None

    def upsert_monthly_snapshot(
        self,
        standard: int,
        month_key: str,
        entries: List[Dict[str, Any]],
        version: str,
    ) -> Dict[str, Any]:
        snapshot = {
            "_id": f"{month_key}-{standard}",
            "version": version,
            "month": month_key,
            "standard": standard,
            "entries": [dict(entry) for entry in entries],
        }
        self.snapshots[(standard, month_key)] = snapshot
        self.upsert_calls.append(snapshot)
        return snapshot

    def list_users_for_standard(self, standard: int) -> List[Dict[str, Any]]:
        return [dict(user) for user in self.users_by_standard.get(standard, [])]

    def get_user_for_standard(self, standard: int, user_id: str) -> Optional[Dict[str, Any]]:
        for user in self.users_by_standard.get(standard, []):
            if user.get("id") == user_id:
                return dict(user)
        return None


def test_get_or_build_monthly_builds_ranks_and_paginates() -> None:
    users = {
        9: [
            {"id": "teacher-1", "teacher": True, "name": "Teacher"},
            {
                "id": "s1",
                "name": "John Doe",
                "division": "A",
                "coins": 5,
                "examHistory": [
                    {
                        "date": "10-02-2026",
                        "score": 8,
                        "totalQuestions": 10,
                        "percentage": 80.0,
                        "subject": "Math",
                        "lessons": ["L1"],
                    }
                ],
            },
            {
                "id": "s2",
                "name": "Jane Roe",
                "division": "A",
                "coins": 50,
                "examHistory": [],
            },
        ]
    }
    repo = _FakeLeaderboardRepo(users_by_standard=users)
    service = LeaderboardService(repo)

    payload = service.get_or_build_monthly(standard=9, month_key="2026-02", page=1, page_size=1)

    assert payload["month"] == "2026-02"
    assert payload["total_count"] == 2
    assert payload["entries"][0]["userId"] == "s1"
    assert payload["entries"][0]["rank"] == 1
    assert len(repo.upsert_calls) == 1


def test_update_on_submission_replaces_user_entry() -> None:
    users = {
        9: [
            {
                "id": "s1",
                "name": "John Doe",
                "division": "A",
                "coins": 10,
                "examHistory": [
                    {
                        "date": "10-02-2026",
                        "score": 9,
                        "totalQuestions": 10,
                        "percentage": 90.0,
                        "subject": "Math",
                        "lessons": ["L1"],
                    }
                ],
            },
            {"id": "s2", "name": "Jane Roe", "division": "A", "coins": 1, "examHistory": []},
        ]
    }
    repo = _FakeLeaderboardRepo(users_by_standard=users)
    repo.snapshots[(9, "2026-02")] = {
        "_id": "2026-02-9",
        "version": "abcd1234",
        "month": "2026-02",
        "standard": 9,
        "entries": [
            {"userId": "s1", "elo_score": 1, "has_taken_exam": True, "coins": 0},
            {"userId": "s2", "elo_score": 0, "has_taken_exam": False, "coins": 1},
        ],
    }
    service = LeaderboardService(repo)

    service.update_on_submission(user_id="s1", standard=9, month_key="2026-02")

    updated = repo.snapshots[(9, "2026-02")]
    matching = [entry for entry in updated["entries"] if entry.get("userId") == "s1"]
    assert len(matching) == 1
    assert matching[0]["elo_score"] > 1
