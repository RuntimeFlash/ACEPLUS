import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class StaticDataService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._loaded = False
        self._error: Optional[str] = None
        self._data_path: Optional[Path] = None
        self._updates: List[Dict[str, Any]] = []

    def _resolve_data_path(self) -> Path:
        backend_dir = Path(__file__).resolve().parents[2]
        cwd = Path.cwd()
        configured = os.getenv("BACKEND_DATA_DIR")
        candidates = [
            configured,
            str(cwd / "data"),
            str(cwd / "backend" / "data"),
            str(backend_dir / "data"),
            "/var/task/data",
            "/var/task/backend/data",
        ]
        required = ("students.json", "class10_students.json", "Update.json")
        for candidate in candidates:
            if not candidate:
                continue
            path = Path(candidate).resolve()
            if not path.is_dir():
                continue
            if all((path / filename).exists() for filename in required):
                return path
        raise FileNotFoundError(
            "Could not locate backend data directory with required files "
            f"{required}"
        )

    def ensure_loaded(self) -> bool:
        if self._loaded:
            return True

        with self._lock:
            if self._loaded:
                return True
            try:
                data_path = self._resolve_data_path()
                with (data_path / "Update.json").open("r", encoding="utf-8") as file:
                    self._updates = json.load(file)
                self._data_path = data_path
                self._error = None
                self._loaded = True
                return True
            except Exception as exc:
                self._error = str(exc)
                self._loaded = False
                return False

    def latest_update(self) -> Optional[Dict[str, Any]]:
        if not self.ensure_loaded():
            return None
        if not self._updates:
            return None
        return self._updates[0]

    def unavailable_payload(self) -> Tuple[Dict[str, str], int]:
        details = self._error or "Unknown data load error"
        return (
            {
                "message": "Server data files are unavailable",
                "details": details,
            },
            500,
        )


static_data_service = StaticDataService()

