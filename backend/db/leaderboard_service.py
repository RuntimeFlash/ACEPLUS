from __future__ import annotations

from typing import Any, Dict, List, Optional

from pymongo.collection import Collection

from .base import DatabaseClient


class LeaderboardRepository:
    def __init__(self, db_client: DatabaseClient) -> None:
        self.db_client = db_client
        for std in (9, 10):
            db_client.get_collection("LeaderboardMonthly", standard=std)

    def _leaderboard_col(self, standard: int) -> Collection:
        return self.db_client.get_collection("LeaderboardMonthly", standard=standard)

    def _users_col(self, standard: int) -> Collection:
        return self.db_client.get_collection("Users", standard=standard)

    def get_monthly_snapshot(self, standard: int, month_key: str) -> Optional[Dict[str, Any]]:
        doc_id = f"{month_key}-{standard}"
        return self._leaderboard_col(standard).find_one({"_id": doc_id})

    def upsert_monthly_snapshot(
        self,
        standard: int,
        month_key: str,
        entries: List[Dict[str, Any]],
        version: str,
    ) -> Dict[str, Any]:
        doc_id = f"{month_key}-{standard}"
        snapshot = {
            "_id": doc_id,
            "version": version,
            "month": month_key,
            "standard": standard,
            "entries": entries,
        }
        self._leaderboard_col(standard).replace_one({"_id": doc_id}, snapshot, upsert=True)
        return snapshot

    def list_users_for_standard(self, standard: int) -> List[Dict[str, Any]]:
        return list(self._users_col(standard).find({}, {"_id": 0}))

    def get_user_for_standard(self, standard: int, user_id: str) -> Optional[Dict[str, Any]]:
        return self._users_col(standard).find_one({"id": user_id}, {"_id": 0})
