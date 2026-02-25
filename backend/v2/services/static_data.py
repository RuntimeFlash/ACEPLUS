from typing import Any, Dict, Optional, Tuple

from db import static_content_repo


class StaticDataService:
    def ensure_loaded(self) -> bool:
        try:
            return bool(static_content_repo.has_data())
        except Exception:
            return False

    def latest_update(self) -> Optional[Dict[str, Any]]:
        updates = static_content_repo.get_json("Update.json")
        if isinstance(updates, list) and updates:
            return updates[0]
        return None

    def students_map(self, is_class10: bool) -> Dict[str, Any]:
        key = "class10_students.json" if is_class10 else "students.json"
        data = static_content_repo.get_json(key)
        return data if isinstance(data, dict) else {}

    def teachers_map(self) -> Dict[str, Any]:
        data = static_content_repo.get_json("teachers.json")
        return data if isinstance(data, dict) else {}

    def lessons_map(self, is_class10: bool) -> Dict[str, Any]:
        key = "lessons10.json" if is_class10 else "lessons.json"
        data = static_content_repo.get_json(key)
        return data if isinstance(data, dict) else {}

    def unavailable_payload(self) -> Tuple[Dict[str, str], int]:
        return (
            {
                "message": "Server static content is unavailable in MongoDB",
                "details": "Run backend/scripts/migrate_json_to_mongo.py to seed StaticContent.",
            },
            500,
        )


static_data_service = StaticDataService()

