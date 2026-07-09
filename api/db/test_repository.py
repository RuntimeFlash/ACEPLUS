from __future__ import annotations

from typing import Any, Dict, List, Optional

from pymongo import ASCENDING
from pymongo.collection import Collection

from .base import DatabaseClient, WriteQueue, should_ensure_indexes

class TestRepository:
    def __init__(self, db_client: DatabaseClient, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.write_queue = write_queue

        if should_ensure_indexes():
            self.ensure_indexes()

    def ensure_indexes(self) -> None:
        for std in (9, 10):
            col = self.db_client.get_collection("Tests", standard=std)
            col.create_index([("test-id", ASCENDING)], unique=True)
            col.create_index([("standard", ASCENDING)])
            col.create_index([("expiration_date", ASCENDING)])
            col.create_index([("standard", ASCENDING), ("created_by", ASCENDING)])
            col.create_index([("standard", ASCENDING), ("division", ASCENDING)])
            col.create_index([("standard", ASCENDING), ("students", ASCENDING)])
            inactive = self.db_client.get_collection("InactiveTests", standard=std)
            inactive.create_index([("test-id", ASCENDING)], unique=True)

    def _tests_col(self, is_class10: Optional[bool] = None, standard: Optional[int] = None) -> Collection:
        return self.db_client.get_collection("Tests", is_class10=is_class10, standard=standard)

    def add_test(self, test_data: Dict[str, Any], is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        std = test_data.get("standard")
        col = self._tests_col(is_class10=is_class10, standard=std)
        col.insert_one(test_data)
        return test_data

    def get_test(self, test_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        if is_class10 is None:
            col9 = self._tests_col(is_class10=False)
            doc = col9.find_one({"test-id": test_id})
            if doc:
                return doc
            col10 = self._tests_col(is_class10=True)
            return col10.find_one({"test-id": test_id})

        col = self._tests_col(is_class10=is_class10)
        return col.find_one({"test-id": test_id})

    def get_all_tests(self, is_class10: Optional[bool] = None) -> List[Dict[str, Any]]:
        if is_class10 is None:
            tests: List[Dict[str, Any]] = []
            for flag in (False, True):
                col = self._tests_col(is_class10=flag)
                docs = list(col.find({}))
                for d in docs:
                    d.pop("_id", None)
                tests.extend(docs)
            return tests
        col = self._tests_col(is_class10=is_class10)
        docs = list(col.find({}))
        for d in docs:
            d.pop("_id", None)
        return docs

    def get_all_tests_by_standard(self, standard: int) -> List[Dict[str, Any]]:
        col = self._tests_col(standard=standard)
        docs = list(col.find({"standard": int(standard)}))
        for d in docs:
            d.pop("_id", None)
        return docs

    def get_tests_created_by(self, standard: int, created_by: str) -> List[Dict[str, Any]]:
        col = self._tests_col(standard=standard)
        docs = list(col.find({"standard": int(standard), "created_by": created_by}))
        for d in docs:
            d.pop("_id", None)
        return docs

    def list_tests_with_filter(self, standard: int, mongo_filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        return list(self._tests_col(standard=standard).find(mongo_filter))

    def update_test(self, test_id: str, updated_data: Dict[str, Any], is_class10: Optional[bool] = None) -> bool:
        test = self.get_test(test_id, is_class10)
        if not test:
            return False
        col = self._tests_col(standard=int(test.get("standard", 9)))
        result = col.update_one({"test-id": test_id}, {"$set": updated_data})
        return result.matched_count > 0

    def delete_test(self, test_id: str, is_class10: Optional[bool] = None) -> bool:
        test = self.get_test(test_id, is_class10)
        if not test:
            return False
        col = self._tests_col(standard=int(test.get("standard", 9)))
        return col.delete_one({"test-id": test_id}).deleted_count > 0

    def upsert_inactive_test(self, standard: int, test_data: Dict[str, Any]) -> None:
        self.db_client.get_collection("InactiveTests", standard=standard).update_one(
            {"test-id": test_data["test-id"]},
            {"$setOnInsert": test_data},
            upsert=True,
        )

    def delete_test_by_standard(self, standard: int, test_id: str) -> bool:
        return self._tests_col(standard=standard).delete_one({"test-id": test_id}).deleted_count > 0
