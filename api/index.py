"""AcePlus API -- FastAPI application entry point."""

import os
import sys
from pathlib import Path

# Add api directory to sys.path to allow absolute imports under Vercel and local uvicorn
api_dir = Path(__file__).resolve().parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from router import api_router
from core.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

# Force serverless-safe behavior in backend runtime.
# SERVERLESS=1: sync WriteQueue (no background threads that die mid-request on Vercel)
# and skip create_index on every cold start (indexes via scripts/ensure_indexes.py).
repo_dir = api_dir.parent
os.environ.setdefault("SERVERLESS", "1")
os.environ.setdefault("BACKEND_DATA_DIR", str(repo_dir / "Legacy Json Qs"))

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=settings.allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=[
            "Content-Type",
            "Authorization",
            "Cache-Control",
            "X-Accel-Buffering",
        ],
    )

    @app.get("/healthz", tags=["system"])
    def healthz():
        return {"status": "ok", "service": "aceplus-backend-v2"}

    app.include_router(api_router)
    return app


app = create_app()
