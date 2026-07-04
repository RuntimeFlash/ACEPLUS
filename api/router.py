from fastapi import APIRouter

from routes import auth, exams, legacy, public, social


api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(public.router)
api_router.include_router(exams.router)
api_router.include_router(legacy.router)
api_router.include_router(social.router)
