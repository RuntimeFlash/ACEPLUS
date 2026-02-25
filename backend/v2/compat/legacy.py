import os

from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware


def _load_legacy_flask_app():
    # Default to serverless mode for mounted legacy app so background threads do not
    # start inside FastAPI workers.
    if os.getenv("ACEPLUS_V2_DISABLE_LEGACY_BACKGROUND", "1") == "1":
        os.environ.setdefault("SERVERLESS", "1")

    from main import app as legacy_flask_app

    return legacy_flask_app


def mount_legacy_app(app: FastAPI) -> None:
    legacy_flask_app = _load_legacy_flask_app()
    # Mounted last as a compatibility fallback for endpoints not yet migrated.
    app.mount("/", WSGIMiddleware(legacy_flask_app))

