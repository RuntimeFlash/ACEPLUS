from __future__ import annotations


KNOWN_STATIC_CONTENT_ALIASES = {
    "students.json": "students.class9",
    "class10_students.json": "students.class10",
    "teachers.json": "teachers",
    "update.json": "updates",
    "lessons.json": "lessons.class9",
    "lessons10.json": "lessons.class10",
}


def normalize_static_rel_path(path: str) -> str:
    normalized = str(path or "").replace("\\", "/").strip().lstrip("./")
    normalized_lower = normalized.lower()

    prefixes = [
        "legacy json qs/",
        "backend/data/",
        "data/",
        "mongo://",
        "json:",
    ]
    for prefix in prefixes:
        if normalized_lower.startswith(prefix):
            normalized = normalized[len(prefix):]
            normalized_lower = normalized.lower()

    return normalized
