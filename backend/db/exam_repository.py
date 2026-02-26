from __future__ import annotations

from typing import Any, Dict, Optional

from pymongo import ASCENDING
from pymongo.collection import Collection

from .base import DatabaseClient, WriteQueue

class ExamRepository:
    def __init__(self, db_client: DatabaseClient, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.write_queue = write_queue

        # Ensure indexes on both DBs
        for std in (9, 10):
            col = db_client.get_collection("Exams", standard=std)
            col.create_index([("exam-id", ASCENDING)], unique=True)
            col.create_index([("userId", ASCENDING), ("is_submitted", ASCENDING)])
            col.create_index([("submission_timestamp", DESCENDING)])
            col.create_index([("userId", ASCENDING), ("is_submitted", ASCENDING), ("timestamp_dt", DESCENDING)])
            col.create_index([("is_submitted", ASCENDING), ("timestamp_dt", ASCENDING)])

    def _col_by_params(self, is_class10: Optional[bool] = None, standard: Optional[int] = None) -> Collection:
        return self.db_client.get_collection("Exams", is_class10=is_class10, standard=standard)

    def add_exam(self, exam_data: Dict[str, Any], is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        std = exam_data.get("standard")
        col = self._col_by_params(is_class10=is_class10, standard=std)
        col.insert_one(exam_data)
        return exam_data

    def get_exam(self, exam_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        if is_class10 is None:
            # Probe DB 9 then 10
            col9 = self._col_by_params(is_class10=False)
            doc = col9.find_one({"exam-id": exam_id})
            if doc:
                return doc
            col10 = self._col_by_params(is_class10=True)
            return col10.find_one({"exam-id": exam_id})

        col = self._col_by_params(is_class10=is_class10)
        return col.find_one({"exam-id": exam_id})

    def update_exam(self, exam_id: str, updated_data: Dict[str, Any], is_class10: Optional[bool] = None) -> bool:
        exam = self.get_exam(exam_id, is_class10)
        if not exam:
            return False
        col = self._col_by_params(standard=int(exam.get("standard", 9)))
        result = col.update_one({"exam-id": exam_id}, {"$set": updated_data})
        return result.matched_count > 0

    def update_exam_solution(self, exam_id: str, question_index: int, solution: str, is_class10: Optional[bool] = None) -> bool:
        exam = self.get_exam(exam_id, is_class10)
        if not exam:
            return False

        col = self._col_by_params(standard=int(exam.get("standard", 9)))
        update_field = f"results.{question_index}.solution"
        result = col.update_one({"exam-id": exam_id}, {"$set": {update_field: solution}})
        return result.matched_count > 0

    def delete_exam(self, exam_id: str, is_class10: Optional[bool] = None) -> bool:
        if is_class10 is not None:
            col = self._col_by_params(is_class10=is_class10)
            return col.delete_one({"exam-id": exam_id}).deleted_count > 0

        col9 = self._col_by_params(is_class10=False)
        deleted9 = col9.delete_one({"exam-id": exam_id}).deleted_count
        if deleted9 > 0:
            return True
        col10 = self._col_by_params(is_class10=True)
        return col10.delete_one({"exam-id": exam_id}).deleted_count > 0


# -----------------------------------------------------------------------------
# Mistake Replay Repository (segregated by class DB)
# -----------------------------------------------------------------------------

