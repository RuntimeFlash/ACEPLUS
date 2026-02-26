from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING

from .base import DatabaseClient, WriteQueue

class TestRepository:
    def __init__(self, db_client: DatabaseClient, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.write_queue = write_queue

        for std in (9, 10):
            col = db_client.get_collection("Tests", standard=std)
            col.create_index([("test-id", ASCENDING)], unique=True)
            col.create_index([("standard", ASCENDING)])
            col.create_index([("expiration_date", ASCENDING)])
            col.create_index([("standard", ASCENDING), ("created_by", ASCENDING)])
            col.create_index([("standard", ASCENDING), ("division", ASCENDING)])
            col.create_index([("standard", ASCENDING), ("students", ASCENDING)])
            inactive = db_client.get_collection("InactiveTests", standard=std)
            inactive.create_index([("test-id", ASCENDING)], unique=True)

    def add_test(self, test_data: Dict[str, Any], is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        std = test_data.get("standard")
        col = self.db_client.get_collection("Tests", is_class10=is_class10, standard=std)
        col.insert_one(test_data)
        return test_data

    def get_test(self, test_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        if is_class10 is None:
            col9 = self.db_client.get_collection("Tests", is_class10=False)
            doc = col9.find_one({"test-id": test_id})
            if doc:
                return doc
            col10 = self.db_client.get_collection("Tests", is_class10=True)
            return col10.find_one({"test-id": test_id})

        col = self.db_client.get_collection("Tests", is_class10=is_class10)
        return col.find_one({"test-id": test_id})

    def get_all_tests(self, is_class10: Optional[bool] = None) -> List[Dict[str, Any]]:
        if is_class10 is None:
            tests: List[Dict[str, Any]] = []
            for flag in (False, True):
                col = self.db_client.get_collection("Tests", is_class10=flag)
                docs = list(col.find({}))
                for d in docs:
                    d.pop("_id", None)
                tests.extend(docs)
            return tests
        col = self.db_client.get_collection("Tests", is_class10=is_class10)
        docs = list(col.find({}))
        for d in docs:
            d.pop("_id", None)
        return docs

    def get_all_tests_by_standard(self, standard: int) -> List[Dict[str, Any]]:
        col = self.db_client.get_collection("Tests", standard=standard)
        docs = list(col.find({"standard": int(standard)}))
        for d in docs:
            d.pop("_id", None)
        return docs

    def get_tests_created_by(self, standard: int, created_by: str) -> List[Dict[str, Any]]:
        col = self.db_client.get_collection("Tests", standard=standard)
        docs = list(col.find({"standard": int(standard), "created_by": created_by}))
        for d in docs:
            d.pop("_id", None)
        return docs

    def get_available_tests_for_student(
        self,
        standard: int,
        user_id: str,
        division: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Fetch tests directly from Mongo for a student instead of loading all tests and filtering in Python.
        """
        col = self.db_client.get_collection("Tests", standard=standard)
        base_filter: Dict[str, Any] = {
            "standard": int(standard),
            "completed_by": {"$ne": user_id},
        }
        assignment_filters: List[Dict[str, Any]] = [
            {"students": user_id},
            {
                "$and": [
                    {"$or": [{"students": {"$exists": False}}, {"students": []}, {"students": None}]},
                    {"$or": [{"division": {"$exists": False}}, {"division": None}, {"division": ""}]},
                ]
            },
        ]
        if division:
            assignment_filters.append({"division": division})

        docs = list(col.find({"$and": [base_filter, {"$or": assignment_filters}]}))
        results: List[Dict[str, Any]] = []

        for doc in docs:
            completed_by = doc.get("completed_by", []) or []
            if user_id in completed_by:
                continue

            assigned_students = doc.get("students")
            assigned_division = doc.get("division")

            if assigned_students:
                if user_id not in assigned_students:
                    continue
            elif assigned_division:
                if not division or division != assigned_division:
                    continue

            doc.pop("_id", None)
            results.append(doc)

        return results

    def update_test(self, test_id: str, updated_data: Dict[str, Any], is_class10: Optional[bool] = None) -> bool:
        test = self.get_test(test_id, is_class10)
        if not test:
            return False
        col = self.db_client.get_collection("Tests", standard=int(test.get("standard", 9)))
        result = col.update_one({"test-id": test_id}, {"$set": updated_data})
        return result.matched_count > 0

    def delete_test(self, test_id: str, is_class10: Optional[bool] = None) -> bool:
        test = self.get_test(test_id, is_class10)
        if not test:
            return False
        col = self.db_client.get_collection("Tests", standard=int(test.get("standard", 9)))
        return col.delete_one({"test-id": test_id}).deleted_count > 0

    def move_expired_tests_to_inactive(self) -> int:
        """Move expired tests to InactiveTests for both classes."""
        from datetime import timezone as dt_tz
        now = datetime.now(dt_tz.utc)
        total_moved = 0
        try:
            for is_class10 in (False, True):
                tests_col = self.db_client.get_collection("Tests", is_class10=is_class10)
                inactive_col = self.db_client.get_collection("InactiveTests", is_class10=is_class10)
                docs = list(tests_col.find({}))
                for test in docs:
                    exp = test.get("expiration_date")
                    if not exp:
                        continue
                    try:
                        iso = exp.replace("Z", "+00:00")
                        exp_dt = datetime.fromisoformat(iso)
                    except Exception:
                        continue
                    if exp_dt < now:
                        test_copy = dict(test)
                        test_copy.pop("_id", None)
                        inactive_col.update_one(
                            {"test-id": test_copy["test-id"]},
                            {"$setOnInsert": test_copy},
                            upsert=True,
                        )
                        deleted = tests_col.delete_one({"test-id": test_copy["test-id"]})
                        if deleted.deleted_count > 0:
                            total_moved += 1
        except Exception as e:
            print(f"Error during moving expired tests: {e}")
        return total_moved


# -----------------------------------------------------------------------------
# Leaderboard Service (segregated per class DB)
# -----------------------------------------------------------------------------

