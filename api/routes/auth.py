from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import JSONResponse

from core.auth import CurrentUser, get_current_user
from services.auth_service import auth_service
from services.static_data import static_data_service


router = APIRouter(tags=["auth"])


@router.post("/login")
def login(payload: Dict[str, Any] = Body(default={})):
    result = auth_service.login(payload)
    return JSONResponse(content=result["payload"], status_code=result["status_code"])


@router.post("/register")
def register(payload: Dict[str, Any] = Body(default={})):
    result = auth_service.register(payload)
    return JSONResponse(content=result["payload"], status_code=result["status_code"])


@router.get("/lessons")
def get_lessons(
    subject: str = Query(default=""),
    class10: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
):
    if not static_data_service.ensure_loaded():
        payload, status_code = static_data_service.unavailable_payload()
        return JSONResponse(content=payload, status_code=status_code)

    if not subject:
        return JSONResponse(content={"message": "Subject parameter is required"}, status_code=400)

    is_class10 = current_user.is_class10
    teachers = static_data_service.teachers_map()
    if current_user.user_id in teachers and class10 is not None:
        is_class10 = class10.lower() == "true"

    lessons = static_data_service.lessons_map(is_class10)
    if subject not in lessons:
        return JSONResponse(content={"message": "Invalid subject"}, status_code=400)

    return JSONResponse(content=lessons[subject], status_code=200)
