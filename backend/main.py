from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from core.settings import settings


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

