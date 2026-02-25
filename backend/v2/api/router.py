from fastapi import APIRouter

from v2.api.routes import public


api_router = APIRouter(prefix="/api")
api_router.include_router(public.router)

