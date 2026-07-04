from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


class UploadDatabaseService:
    def __init__(self, upload_repo: Any) -> None:
        self.upload_repo = upload_repo

    def enforce_user_bytes_cap(
        self,
        user_id: str,
        is_class10: bool,
        bytes_limit: int,
        window_hours: int = 24,
    ) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        docs = self.upload_repo.list_user_file_sizes_since(
            user_id=user_id,
            is_class10=is_class10,
            cutoff=cutoff,
        )
        total_bytes = sum(int(doc.get("length", 0)) for doc in docs)
        while total_bytes > bytes_limit and docs:
            oldest = docs.pop(0)
            removed = self.upload_repo.delete_file(str(oldest.get("_id")), is_class10, delete_children=False)
            if removed:
                total_bytes -= int(oldest.get("length", 0))
