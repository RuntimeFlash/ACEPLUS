from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from gridfs import GridFSBucket
from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection

from .base import DatabaseClient
from utils.mongo_utils import parse_object_id

class UploadRepository:
    """Stores user uploads in Mongo GridFS to avoid local-disk dependency."""

    def __init__(self, db_client: DatabaseClient) -> None:
        self.db_client = db_client
        self._bucket9 = GridFSBucket(db_client._db9, bucket_name="uploads")
        self._bucket10 = GridFSBucket(db_client._db10, bucket_name="uploads")
        for std in (9, 10):
            files_col = db_client.get_collection("uploads.files", standard=std)
            files_col.create_index([("metadata.user_id", ASCENDING), ("uploadDate", DESCENDING)])
            files_col.create_index([("metadata.parent_file_id", ASCENDING)])

    def _bucket(self, is_class10: bool) -> GridFSBucket:
        return self._bucket10 if is_class10 else self._bucket9

    def _files_col(self, is_class10: bool) -> Collection:
        return self.db_client.get_collection("uploads.files", is_class10=is_class10)

    def save_file(
        self,
        data: bytes,
        filename: str,
        user_id: str,
        is_class10: bool,
        content_type: Optional[str] = None,
        file_kind: str = "original",
        parent_file_id: Optional[str] = None,
    ) -> str:
        metadata = {
            "user_id": user_id,
            "content_type": content_type or "application/octet-stream",
            "file_kind": file_kind,
        }
        if parent_file_id:
            metadata["parent_file_id"] = str(parent_file_id)
        with self._bucket(is_class10).open_upload_stream(filename, metadata=metadata) as stream:
            stream.write(data)
            return str(stream._id)

    def get_file(self, file_id: str, is_class10: bool) -> Optional[Dict[str, Any]]:
        oid = parse_object_id(file_id)
        if oid is None:
            return None
        file_doc = self._files_col(is_class10).find_one({"_id": oid})
        if not file_doc:
            return None
        stream = self._bucket(is_class10).open_download_stream(oid)
        try:
            data = stream.read()
        finally:
            stream.close()
        metadata = file_doc.get("metadata", {}) or {}
        return {
            "id": str(file_doc["_id"]),
            "filename": file_doc.get("filename") or "",
            "length": int(file_doc.get("length", 0)),
            "upload_date": file_doc.get("uploadDate"),
            "user_id": metadata.get("user_id"),
            "content_type": metadata.get("content_type"),
            "file_kind": metadata.get("file_kind", "original"),
            "parent_file_id": metadata.get("parent_file_id"),
            "data": data,
        }

    def delete_file(self, file_id: str, is_class10: bool, delete_children: bool = True) -> bool:
        oid = parse_object_id(file_id)
        if oid is None:
            return False
        files_col = self._files_col(is_class10)
        file_doc = files_col.find_one({"_id": oid})
        if not file_doc:
            return False
        if delete_children:
            child_docs = files_col.find({"metadata.parent_file_id": str(oid)})
            for child in child_docs:
                try:
                    self._bucket(is_class10).delete(child["_id"])
                except Exception:
                    continue
        self._bucket(is_class10).delete(oid)
        return True

    def list_user_file_sizes_since(
        self,
        user_id: str,
        is_class10: bool,
        cutoff: datetime,
    ) -> List[Dict[str, Any]]:
        return list(
            self._files_col(is_class10)
            .find({"metadata.user_id": user_id, "uploadDate": {"$gte": cutoff}}, {"_id": 1, "length": 1})
            .sort("uploadDate", ASCENDING)
        )

