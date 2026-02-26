from __future__ import annotations

from typing import Any, Dict

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection

from .base import DatabaseClient

class QuestionReportRepository:
    """Persists question reports in Mongo instead of local JSON files."""

    def __init__(self, db_client: DatabaseClient) -> None:
        self.db_client = db_client
        for std in (9, 10):
            col = db_client.get_collection("QuestionReports", standard=std)
            col.create_index(
                [("user_id", ASCENDING), ("exam_id", ASCENDING), ("question_index", ASCENDING)],
                unique=True,
            )
            col.create_index([("timestamp", DESCENDING)])

    def _col(self, is_class10: bool) -> Collection:
        return self.db_client.get_collection("QuestionReports", is_class10=is_class10)

    def create_report_if_absent(self, report: Dict[str, Any], is_class10: bool) -> bool:
        result = self._col(is_class10).update_one(
            {
                "user_id": report["user_id"],
                "exam_id": report["exam_id"],
                "question_index": report["question_index"],
            },
            {"$setOnInsert": report},
            upsert=True,
        )
        return result.upserted_id is not None
