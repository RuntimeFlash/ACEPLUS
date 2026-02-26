import os
import sys


def _resolve_backend_dir() -> str:
    file_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(file_dir, "backend"),
        os.path.join(os.path.dirname(file_dir), "backend"),
    ]
    for candidate in candidates:
        normalized = os.path.normpath(candidate)
        if os.path.isdir(normalized):
            return normalized
    # Fallback for local dev shape: <repo>/api/index.py + sibling <repo>/backend
    return os.path.normpath(os.path.join(os.path.dirname(file_dir), "backend"))


BACKEND_DIR = _resolve_backend_dir()

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Force serverless-safe behavior in backend runtime.
os.environ.setdefault("SERVERLESS", "1")
os.environ.setdefault("BACKEND_DATA_DIR", os.path.join(BACKEND_DIR, "data"))

from main import app  # noqa: E402
