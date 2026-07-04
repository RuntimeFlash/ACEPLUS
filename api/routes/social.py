from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import JSONResponse

from core.auth import CurrentUser, get_current_user
from services.social_service import social_service


router = APIRouter(tags=["social"])


def _error_response(exc: Exception) -> JSONResponse:
    return JSONResponse(content={"message": str(exc)}, status_code=400)


@router.get("/profile/me")
def get_my_profile(current_user: CurrentUser = Depends(get_current_user)):
    try:
        data = social_service.get_profile(current_user.user_id, current_user.user_id)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=200)


@router.get("/profile/{user_id}")
def get_profile(user_id: str, current_user: CurrentUser = Depends(get_current_user)):
    try:
        data = social_service.get_profile(current_user.user_id, user_id)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=200)


@router.put("/profile/me")
def update_my_profile(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        data = social_service.update_profile(current_user.user_id, payload or {})
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=200)


@router.post("/profile/status")
def update_status(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        status = str((payload or {}).get("status", "")).strip()
        data = social_service.set_status(current_user.user_id, status)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=200)


@router.post("/profile/showcase")
def update_showcase(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        badge_ids = (payload or {}).get("badge_ids", []) or []
        data = social_service.set_showcase_badges(current_user.user_id, badge_ids)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=200)


@router.get("/friends/search")
def search_friends(
    q: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        data = social_service.search_users(current_user.user_id, q, limit=limit)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content={"results": data}, status_code=200)


@router.post("/friends/request")
def send_friend_request(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    identifier = str((payload or {}).get("identifier", "")).strip()
    if not identifier:
        return JSONResponse(content={"message": "identifier is required"}, status_code=400)
    try:
        data = social_service.send_friend_request(current_user.user_id, identifier)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=200)


@router.get("/friends/requests")
def get_friend_requests(current_user: CurrentUser = Depends(get_current_user)):
    try:
        data = social_service.get_friend_requests(current_user.user_id)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=200)


@router.post("/friends/respond")
def respond_friend_request(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    request_id = str((payload or {}).get("request_id", "")).strip()
    action = str((payload or {}).get("action", "")).strip().lower()
    if not request_id:
        return JSONResponse(content={"message": "request_id is required"}, status_code=400)
    try:
        data = social_service.respond_friend_request(current_user.user_id, request_id, action)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=200)


@router.get("/friends/list")
def get_friends(current_user: CurrentUser = Depends(get_current_user)):
    try:
        data = social_service.get_friends(current_user.user_id)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content={"friends": data}, status_code=200)


@router.delete("/friends/{friend_id}")
def remove_friend(friend_id: str, current_user: CurrentUser = Depends(get_current_user)):
    try:
        data = social_service.remove_friend(current_user.user_id, friend_id)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=200)


@router.get("/friends/leaderboard")
def get_friend_leaderboard(
    metric: str = Query(default="xp"),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        data = social_service.get_friend_leaderboard(current_user.user_id, metric)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content={"leaderboard": data}, status_code=200)


@router.post("/friends/challenges")
def create_challenge(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        data = social_service.create_challenge(
            requester_id=current_user.user_id,
            title=str((payload or {}).get("title", "")),
            goal_type=str((payload or {}).get("goal_type", "xp")),
            goal_value=int((payload or {}).get("goal_value", 1) or 1),
            participant_ids=(payload or {}).get("participant_ids", []) or [],
            end_date=(payload or {}).get("end_date"),
        )
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=201)


@router.get("/friends/challenges")
def get_challenges(current_user: CurrentUser = Depends(get_current_user)):
    try:
        data = social_service.get_challenges(current_user.user_id)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content={"challenges": data}, status_code=200)


@router.post("/friends/squads")
def create_squad(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        data = social_service.create_squad(
            requester_id=current_user.user_id,
            name=str((payload or {}).get("name", "")),
            member_ids=(payload or {}).get("member_ids", []) or [],
            goal=(payload or {}).get("goal", {}) or {},
        )
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=201)


@router.get("/friends/squads")
def get_squads(current_user: CurrentUser = Depends(get_current_user)):
    try:
        data = social_service.get_squads(current_user.user_id)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content={"squads": data}, status_code=200)


@router.put("/friends/squads/{squad_id}/goal")
def update_squad_goal(
    squad_id: str,
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        data = social_service.update_squad_goal(current_user.user_id, squad_id, (payload or {}).get("goal", {}) or {})
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=200)


@router.post("/friends/nudge")
def send_nudge(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    friend_id = str((payload or {}).get("friend_id", "")).strip()
    if not friend_id:
        return JSONResponse(content={"message": "friend_id is required"}, status_code=400)
    try:
        data = social_service.send_nudge(
            requester_id=current_user.user_id,
            friend_id=friend_id,
            nudge_type=str((payload or {}).get("type", "study")),
            message=str((payload or {}).get("message", "")),
        )
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=201)


@router.get("/friends/nudges")
def get_nudges(
    unread_only: bool = Query(default=False),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        data = social_service.get_nudges(current_user.user_id, unread_only=unread_only)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content={"nudges": data}, status_code=200)


@router.post("/friends/nudges/{nudge_id}/read")
def mark_nudge_read(nudge_id: str, current_user: CurrentUser = Depends(get_current_user)):
    try:
        data = social_service.mark_nudge_read(current_user.user_id, nudge_id)
    except Exception as exc:
        return _error_response(exc)
    return JSONResponse(content=data, status_code=200)
