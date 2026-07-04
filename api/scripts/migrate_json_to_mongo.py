import json
import os
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(
    os.getenv("BACKEND_DATA_DIR", str(ROOT.parent / "Legacy Json Qs"))
).resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import static_content_repo

ALIASES = {
    "students.json": "students.class9",
    "class10_students.json": "students.class10",
    "teachers.json": "teachers",
    "update.json": "updates",
    "lessons.json": "lessons.class9",
    "lessons10.json": "lessons.class10",
}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return json.loads(path.read_text(encoding="latin-1"))


def _infer_metadata(rel_path: str) -> Tuple[Optional[int], Optional[str]]:
    rel = rel_path.replace("\\", "/").lower()
    parts = rel.split("/")
    standard = None
    subject = None

    if rel.startswith("lessons10/"):
        standard = 10
        if len(parts) > 1:
            subject = parts[1]
    elif rel.startswith("lessons/"):
        standard = 9
        if len(parts) > 1:
            subject = parts[1]
    elif rel == "class10_students.json" or rel == "lessons10.json":
        standard = 10
    elif rel == "students.json" or rel == "lessons.json":
        standard = 9

    return standard, subject


def main() -> None:
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")

    files = sorted(DATA_DIR.rglob("*.json"))
    if not files:
        print(f"No JSON files found under {DATA_DIR}.")
        return

    migrated = 0
    alias_count = 0
    for file_path in files:
        rel_path = file_path.relative_to(DATA_DIR).as_posix()
        payload = _load_json(file_path)
        standard, subject = _infer_metadata(rel_path)
        alias = ALIASES.get(rel_path.lower())

        static_content_repo.upsert_json(
            rel_path=rel_path,
            content=payload,
            standard=standard,
            subject=subject,
            alias=alias,
        )
        migrated += 1

        if alias:
            static_content_repo.upsert_alias(alias, payload)
            alias_count += 1

    print(f"Migrated {migrated} JSON files into Mongo StaticContent.")
    print(f"Updated {alias_count} alias documents.")


if __name__ == "__main__":
    main()
