from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import JSONResponse

from db import leaderboard_service, user_repo
from core.auth import CurrentUser, get_current_user
from services.auth_service import auth_service
from services.exam_service import exam_service
from services.replay_service import replay_service


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


@router.post("/create_exam")
def create_exam(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = exam_service.create_exam(
        user_id=current_user.user_id,
        is_class10=current_user.is_class10,
        payload=payload,
    )
    if not result["ok"]:
        return JSONResponse(content={"message": result["message"]}, status_code=result["status_code"])
    return JSONResponse(content=result["payload"], status_code=result["status_code"])


@router.post("/submit_exam/{exam_id}")
def submit_exam(
    exam_id: str,
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    selected_answers = payload.get("answers")
    if not isinstance(selected_answers, list):
        return JSONResponse(content={"message": "answers must be a list"}, status_code=400)

    result = exam_service.submit_exam(
        exam_id=exam_id,
        user_id=current_user.user_id,
        is_class10=current_user.is_class10,
        selected_answers=selected_answers,
    )
    if not result["ok"]:
        return JSONResponse(content={"message": result["message"]}, status_code=result["status_code"])
    return JSONResponse(content=result["payload"], status_code=result["status_code"])


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


@router.get("/user_stats")
def get_user_stats(
    current_user: CurrentUser = Depends(get_current_user),
):
    # Projection: avoid shipping examHistory / questionHistory / full subjects on every home load.
    user = user_repo.get_user(
        current_user.user_id,
        current_user.is_class10,
        projection={"stats": 1, "id": 1},
    )
    if not user:
        return JSONResponse(content={"message": "User not found"}, status_code=404)

    stats = user.get("stats", {}) or {}
    attempted = int(stats.get("attempted", 0) or 0)
    total_questions = int(stats.get("questions", 0) or 0)
    marks_gained = int(stats.get("correct", 0) or 0)
    avg_percentage = float(stats.get("avgPercentage", 0.0) or 0.0)

    payload = {
        "stats": [
            {"total_exams": attempted},
            {"total_marks": total_questions},
            {"marks_gained": marks_gained},
            {"average_percentage": f"{avg_percentage:.2f}%"},
        ],
        "version": auth_service.version,
    }
    return JSONResponse(content=payload, status_code=200)


@router.get("/fetch_coins")
def fetch_coins(
    current_user: CurrentUser = Depends(get_current_user),
):
    user = user_repo.get_user(
        current_user.user_id,
        current_user.is_class10,
        projection={"coins": 1, "tasks": 1, "id": 1},
    )
    if not user:
        return JSONResponse(content={"message": "User not found"}, status_code=404)

    tasks = (user.get("tasks", {}) or {}).get("tasks_list", []) or []
    return JSONResponse(
        content={
            "coins": int(user.get("coins", 0) or 0),
            "tasks": tasks,
        },
        status_code=200,
    )


@router.get("/leaderboard")
def get_leaderboard(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
):
    user = user_repo.get_user(
        current_user.user_id,
        current_user.is_class10,
        projection={"division": 1, "id": 1},
    )
    if not user:
        return JSONResponse(content={"message": "User not found"}, status_code=404)

    standard = 10 if current_user.is_class10 else 9
    division = str(user.get("division", "") or "").strip()

    monthly = leaderboard_service.get_or_build_monthly(
        standard=standard,
        page=page,
        page_size=page_size,
        division=division or None,
    )
    total_count = int(monthly.get("total_count", 0) or 0)
    total_pages = max(1, (total_count + page_size - 1) // page_size) if total_count else 1

    payload = {
        "leaderboard_id": f"{monthly.get('month')}-{standard}-{monthly.get('version')}",
        "month": monthly.get("month"),
        "class": str(standard),
        "division": division,
        "leaderboard": monthly.get("entries", []) or [],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_count": total_count,
        },
    }
    return JSONResponse(content=payload, status_code=200)


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


@router.get("/mistake_replay")
def get_mistake_replay(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
):
    payload = replay_service.get_due_cards(
        user_id=current_user.user_id,
        is_class10=current_user.is_class10,
        limit=limit,
    )
    return JSONResponse(content=payload, status_code=200)


@router.post("/mistake_replay/review")
def review_mistake_replay(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    replay_id = str(payload.get("replay_id", "")).strip()
    selected_option = str(payload.get("selected_option", "")).strip().lower()
    if not replay_id:
        return JSONResponse(content={"message": "replay_id is required"}, status_code=400)
    if selected_option not in {"a", "b", "c", "d"}:
        return JSONResponse(content={"message": "selected_option must be one of a/b/c/d"}, status_code=400)

    result = replay_service.review_card(
        replay_id=replay_id,
        user_id=current_user.user_id,
        is_class10=current_user.is_class10,
        selected_option=selected_option,
    )
    if not result["ok"]:
        return JSONResponse(content={"message": result["message"]}, status_code=result["status_code"])
    return JSONResponse(content=result["payload"], status_code=result["status_code"])
