from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pymongo import ASCENDING

from .base import DatabaseClient, should_ensure_indexes
from utils.static_content_utils import KNOWN_STATIC_CONTENT_ALIASES, normalize_static_rel_path

class StaticContentRepository:
    """
    Stores static JSON content in Mongo so runtime does not depend on local files.
    Content is stored in class-9 DB as a single shared source.
    """

    def __init__(self, db_client: DatabaseClient) -> None:
        self.db_client = db_client
        self._col = db_client.get_collection("StaticContent", standard=9)
        if should_ensure_indexes():
            self.ensure_indexes()

    def ensure_indexes(self) -> None:
        self._col.create_index([("kind", ASCENDING), ("rel_path", ASCENDING)])
        self._col.create_index([("alias", ASCENDING)])
        self._col.create_index([("standard", ASCENDING), ("subject", ASCENDING)])

    def upsert_json(
        self,
        rel_path: str,
        content: Any,
        standard: Optional[int] = None,
        subject: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> None:
        rel = normalize_static_rel_path(rel_path)
        doc_id = f"json:{rel}"
        update_set: Dict[str, Any] = {
            "kind": "json_file",
            "rel_path": rel,
            "content": content,
            "updated_at": datetime.now(timezone.utc),
        }
        if standard is not None:
            update_set["standard"] = int(standard)
        if subject:
            update_set["subject"] = subject
        if alias:
            update_set["alias"] = alias
        self._col.update_one({"_id": doc_id}, {"$set": update_set}, upsert=True)

    def upsert_alias(self, alias: str, content: Any) -> None:
        doc_id = f"alias:{alias}"
        self._col.update_one(
            {"_id": doc_id},
            {
                "$set": {
                    "kind": "alias",
                    "alias": alias,
                    "content": content,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    def get_alias(self, alias: str) -> Optional[Any]:
        doc = self._col.find_one({"_id": f"alias:{alias}"}, {"_id": 0, "content": 1})
        if not doc:
            return None
        return doc.get("content")

    def get_json(self, rel_path_or_name: str) -> Optional[Any]:
        rel = normalize_static_rel_path(rel_path_or_name)
        if not rel:
            return None

        alias_key = KNOWN_STATIC_CONTENT_ALIASES.get(rel.lower())
        if alias_key:
            alias_doc = self.get_alias(alias_key)
            if alias_doc is not None:
                return alias_doc

        doc = self._col.find_one({"_id": f"json:{rel}"}, {"_id": 0, "content": 1})
        if doc:
            return doc.get("content")

        # Try lowercase Update alias fallback.
        if rel == "Update.json":
            alias_doc = self.get_alias("updates")
            if alias_doc is not None:
                return alias_doc
        return None

    def has_data(self) -> bool:
        return self._col.estimated_document_count() > 0
