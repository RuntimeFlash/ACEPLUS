from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pymongo import ASCENDING
from pymongo.collection import Collection

from .base import DatabaseClient, WriteQueue
from utils.user_stats_utils import build_user_doc, to_student_summary

class UserRepository:
    def __init__(self, db_client: DatabaseClient, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.write_queue = write_queue

        # Ensure indexes exist on both DBs
        for std in (9, 10):
            col = db_client.get_collection("Users", standard=std)
            col.create_index([("id", ASCENDING)], unique=True)
            col.create_index([("standard", ASCENDING), ("division", ASCENDING)])
            col.create_index([("teacher", ASCENDING)])

    def _col_for_user(self, user_id: str, is_class10: Optional[bool]) -> Tuple[Collection, bool]:
        """Resolve collection for user. If class unknown, probe 9 then 10. Returns (collection, is_class10)."""
        if is_class10 is not None:
            return self.db_client.get_collection("Users", is_class10=is_class10), is_class10

        col9 = self.db_client.get_collection("Users", is_class10=False)
        if col9.find_one({"id": user_id}, {"_id": 1}):
            return col9, False

        col10 = self.db_client.get_collection("Users", is_class10=True)
        if col10.find_one({"id": user_id}, {"_id": 1}):
            return col10, True

        # Default to class 9 if unknown (caller may insert).
        return col9, False

    def get_user(self, user_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        if is_class10 is not None:
            col = self.db_client.get_collection("Users", is_class10=is_class10)
            doc = col.find_one({"id": user_id})
            if doc:
                return doc
            other_col = self.db_client.get_collection("Users", is_class10=not is_class10)
            return other_col.find_one({"id": user_id})

        col9 = self.db_client.get_collection("Users", is_class10=False)
        doc = col9.find_one({"id": user_id})
        if doc:
            return doc

        col10 = self.db_client.get_collection("Users", is_class10=True)
        return col10.find_one({"id": user_id})

    def create_user(
        self,
        user_id: str,
        password: Optional[str],
        name: str,
        roll_no: int,
        division: str,
        standard: int,
        teacher: bool = False,
    ) -> Dict[str, Any]:
        user_doc = build_user_doc(
            user_id=user_id,
            password=password,
            name=name,
            roll_no=roll_no,
            division=division,
            standard=standard,
            teacher=teacher,
        )

        col = self.db_client.get_collection("Users", standard=standard)
        col.update_one({"id": user_id}, {"$setOnInsert": user_doc}, upsert=True)
        return user_doc

    def set_password(self, user_id: str, new_password: str, is_class10: Optional[bool] = None) -> bool:
        col, _ = self._col_for_user(user_id, is_class10)
        result = col.update_one({"id": user_id}, {"$set": {"password": new_password}})
        return result.matched_count > 0

    def update_tasks(self, user_id: str, tasks: Dict[str, Any], is_class10: Optional[bool] = None, coins: Optional[int] = None) -> None:
        col, _ = self._col_for_user(user_id, is_class10)
        update_set = {"tasks": tasks}
        if coins is not None:
            update_set["coins"] = coins
        col.update_one({"id": user_id}, {"$set": update_set})

    def get_user_stats(self, user_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        user = self.get_user(user_id, is_class10)
        if not user:
            return None
        return user.get("stats", None)

    def get_all_user_subject_stats(self, user_id: str, is_class10: Optional[bool] = None) -> List[Dict[str, Any]]:
        user = self.get_user(user_id, is_class10)
        if not user:
            return []
        subjects = user.get("subjects", []) or []
        for s in subjects:
            s.pop("_id", None)
        return subjects

    def get_user_subject_stats(self, user_id: str, subject: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        subjects = self.get_all_user_subject_stats(user_id, is_class10)
        for s in subjects:
            if s.get("subject", "").lower() == subject.lower():
                return s
        return None

    def add_exam_history(self, user_id: str, overview: Dict[str, Any], is_class10: Optional[bool] = None) -> None:
        col, _ = self._col_for_user(user_id, is_class10)
        col.update_one({"id": user_id}, {"$push": {"examHistory": overview}})

    def update_stats_and_exam_history(
        self,
        user_id: str,
        stats: Dict[str, Any],
        subjects: List[Dict[str, Any]],
        exam_overview: Dict[str, Any],
        is_class10: Optional[bool] = None,
    ) -> bool:
        col, _ = self._col_for_user(user_id, is_class10)
        result = col.update_one(
            {"id": user_id},
            {"$set": {"stats": stats, "subjects": subjects}, "$push": {"examHistory": exam_overview}},
        )
        return result.matched_count > 0

    def get_user_exams_overview(self, user_id: str, is_class10: Optional[bool] = None) -> List[Dict[str, Any]]:
        user = self.get_user(user_id, is_class10)
        if not user:
            return []
        return user.get("examHistory", []) or []

    def get_question_history(self, user_id: str, is_class10: Optional[bool] = None) -> List[str]:
        user = self.get_user(user_id, is_class10)
        if not user:
            return []
        history = user.get("questionHistory", [])
        return history if isinstance(history, list) else []

    def set_question_history(self, user_id: str, history: List[str], is_class10: Optional[bool] = None) -> None:
        col, _ = self._col_for_user(user_id, is_class10)
        col.update_one({"id": user_id}, {"$set": {"questionHistory": history}})

    def get_all_students_by_standard(self, standard: int) -> List[Dict[str, Any]]:
        col = self.db_client.get_collection("Users", standard=standard)
        return [to_student_summary(student) for student in col.find({"teacher": False})]
