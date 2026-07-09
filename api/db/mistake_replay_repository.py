from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING
from pymongo.collection import Collection

from .base import DatabaseClient, WriteQueue

class MistakeReplayRepository:
    def __init__(self, db_client: DatabaseClient, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.write_queue = write_queue

        for std in (9, 10):
            col = db_client.get_collection("MistakeReplay", standard=std)
            col.create_index([("replay_id", ASCENDING)], unique=True)
            col.create_index([("userId", ASCENDING), ("mistake_key", ASCENDING)], unique=True)
            col.create_index([("userId", ASCENDING), ("is_active", ASCENDING), ("due_at_dt", ASCENDING)])
            col.create_index([("due_at_dt", ASCENDING)])

    def _col_by_params(self, is_class10: Optional[bool] = None, standard: Optional[int] = None) -> Collection:
        return self.db_client.get_collection("MistakeReplay", is_class10=is_class10, standard=standard)

    def upsert_card(
        self,
        card_data: Dict[str, Any],
        is_class10: Optional[bool] = None,
    ) -> bool:
        standard = int(card_data.get("standard", 10 if is_class10 else 9))
        col = self._col_by_params(is_class10=is_class10, standard=standard)
        set_data = dict(card_data)
        created_at_dt = set_data.pop("created_at_dt", None)
        result = col.update_one(
            {
                "userId": card_data["userId"],
                "mistake_key": card_data["mistake_key"],
            },
            {
                "$set": set_data,
                "$setOnInsert": {"created_at_dt": created_at_dt},
            },
            upsert=True,
        )
        return bool(result.acknowledged)

    def get_due_cards(
        self,
        user_id: str,
        is_class10: bool,
        now_utc: datetime,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        col = self._col_by_params(is_class10=is_class10)
        docs = list(
            col.find(
                {
                    "userId": user_id,
                    "is_active": True,
                    "due_at_dt": {"$lte": now_utc},
                }
            )
            .sort("due_at_dt", ASCENDING)
            .limit(max(1, min(int(limit), 100)))
        )
        return docs

    def get_next_card(
        self,
        user_id: str,
        is_class10: bool,
    ) -> Optional[Dict[str, Any]]:
        col = self._col_by_params(is_class10=is_class10)
        return col.find_one(
            {"userId": user_id, "is_active": True},
            sort=[("due_at_dt", ASCENDING)],
        )

    def get_card_by_replay_id(
        self,
        replay_id: str,
        user_id: str,
        is_class10: bool,
    ) -> Optional[Dict[str, Any]]:
        col = self._col_by_params(is_class10=is_class10)
        return col.find_one({"replay_id": replay_id, "userId": user_id, "is_active": True})

    def update_card(
        self,
        replay_id: str,
        user_id: str,
        is_class10: bool,
        update_data: Dict[str, Any],
    ) -> bool:
        col = self._col_by_params(is_class10=is_class10)
        result = col.update_one(
            {"replay_id": replay_id, "userId": user_id},
            {"$set": update_data},
        )
        return result.matched_count > 0


# -----------------------------------------------------------------------------
# Test Repository (segregated by class DB)
# -----------------------------------------------------------------------------

