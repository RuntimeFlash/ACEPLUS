from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse

from v2.core.auth import CurrentUser, get_current_user
from v2.services.exam_service import exam_service


router = APIRouter(tags=["exams"])


@router.get("/exam/{exam_id}")
def get_exam(
    exam_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    exam_data = exam_service.get_exam(exam_id, current_user.is_class10)
    if not exam_data:
        return JSONResponse(content={"message": "Exam not found"}, status_code=404)
    return JSONResponse(content=exam_data, status_code=200)


@router.put("/exam/{exam_id}")
def save_exam_answers(
    exam_id: str,
    payload: Dict[str, List[Dict[str, Any]]] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    answers = payload.get("answers", [])
    if not isinstance(answers, list):
        return JSONResponse(content={"message": "answers must be a list"}, status_code=400)

    result = exam_service.save_exam_answers(
        exam_id=exam_id,
        user_id=current_user.user_id,
        is_class10=current_user.is_class10,
        answers=answers,
    )
    if not result["ok"]:
        return JSONResponse(content={"message": result["message"]}, status_code=result["status_code"])
    return JSONResponse(content=result["payload"], status_code=result["status_code"])


@router.get("/user_exams")
def get_user_exams(
    current_user: CurrentUser = Depends(get_current_user),
):
    data = exam_service.get_user_exams(
        user_id=current_user.user_id,
        is_class10=current_user.is_class10,
    )
    return JSONResponse(content=data, status_code=200)


@router.get("/unsubmitted_exams")
def get_unsubmitted_exams(
    current_user: CurrentUser = Depends(get_current_user),
):
    data = exam_service.get_recent_unsubmitted_exams(
        user_id=current_user.user_id,
        is_class10=current_user.is_class10,
    )
    return JSONResponse(content=data, status_code=200)


@router.delete("/delete_unsubmitted_exam/{exam_id}")
def delete_unsubmitted_exam(
    exam_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    result = exam_service.delete_unsubmitted_exam(
        exam_id=exam_id,
        user_id=current_user.user_id,
        is_class10=current_user.is_class10,
    )
    if not result["ok"]:
        return JSONResponse(content={"message": result["message"]}, status_code=result["status_code"])
    return JSONResponse(content=result["payload"], status_code=result["status_code"])

