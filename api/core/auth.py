import os
import threading
from dataclasses import dataclass

import jwt
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)
_token_lock = threading.Lock()
_token_app: Flask | None = None


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    is_class10: bool


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Header",
        )

    token = credentials.credentials
    secret = os.getenv("FLASK_SECRET_KEY", "boombakabambam")
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    identity = payload.get("sub")
    if isinstance(identity, dict):
        user_id = identity.get("user_id")
        is_class10 = bool(identity.get("class10", False))
    else:
        user_id = identity
        is_class10 = False

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return CurrentUser(user_id=str(user_id), is_class10=is_class10)


def _get_token_app() -> Flask:
    global _token_app
    if _token_app is None:
        with _token_lock:
            if _token_app is None:
                app = Flask("aceplus-v2-token-app")
                app.config["JWT_SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "boombakabambam")
                app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
                app.config["JWT_REFRESH_TOKEN_EXPIRES"] = False
                JWTManager(app)
                _token_app = app
    return _token_app


def create_legacy_access_token(user_id: str, is_class10: bool) -> str:
    token_app = _get_token_app()
    with token_app.app_context():
        return create_access_token(
            identity={"user_id": user_id, "class10": is_class10},
            expires_delta=False,
        )
