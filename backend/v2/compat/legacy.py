import os
import threading
from typing import Callable

from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.types import Receive, Scope, Send


def _legacy_enabled() -> bool:
    return os.getenv("ACEPLUS_V2_ENABLE_LEGACY_FALLBACK", "1") == "1"


class LazyWSGIApp:
    def __init__(self, loader: Callable[[], object]) -> None:
        self._loader = loader
        self._lock = threading.Lock()
        self._wrapped = None

    def _get_wrapped(self):
        if self._wrapped is None:
            with self._lock:
                if self._wrapped is None:
                    app = self._loader()
                    self._wrapped = WSGIMiddleware(app)
        return self._wrapped

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        wrapped = self._get_wrapped()
        await wrapped(scope, receive, send)


def _load_legacy_flask_app():
    # Keep legacy app serverless-safe.
    os.environ.setdefault("SERVERLESS", "1")
    from main import app as legacy_flask_app
    return legacy_flask_app


def mount_legacy_app(app: FastAPI) -> None:
    if not _legacy_enabled():
        return
    app.mount("/", LazyWSGIApp(_load_legacy_flask_app))
