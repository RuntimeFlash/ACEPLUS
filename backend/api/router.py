from fastapi import APIRouter

from api.routes import auth, exams, public


api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(public.router)
api_router.include_router(exams.router)
