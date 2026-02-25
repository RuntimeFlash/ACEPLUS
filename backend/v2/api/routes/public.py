from fastapi import APIRouter
from fastapi.responses import JSONResponse

from v2.services.static_data import static_data_service


router = APIRouter(tags=["public"])


@router.get("/updates")
def get_updates():
    if not static_data_service.ensure_loaded():
        payload, status_code = static_data_service.unavailable_payload()
        return JSONResponse(content=payload, status_code=status_code)

    latest = static_data_service.latest_update()
    if latest:
        return JSONResponse(content=latest, status_code=200)
    return JSONResponse(content={"message": "No updates found"}, status_code=200)

