import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Force serverless-safe behavior in backend runtime.
os.environ.setdefault("SERVERLESS", "1")
os.environ.setdefault("BACKEND_DATA_DIR", os.path.join(BACKEND_DIR, "data"))

from main import app  # noqa: E402
