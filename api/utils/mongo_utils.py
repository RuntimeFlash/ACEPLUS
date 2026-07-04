from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from bson import ObjectId


def convert_objectid_to_str(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    return obj


def parse_object_id(file_id: str) -> Optional[ObjectId]:
    try:
        return ObjectId(file_id)
    except Exception:
        return None
