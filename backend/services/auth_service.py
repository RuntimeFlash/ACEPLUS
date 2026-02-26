from typing import Any, Dict

from db import user_repo
from core.auth import create_legacy_access_token
from services.static_data import static_data_service


class AuthService:
    version = "1.1.0"

    def login(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not static_data_service.ensure_loaded():
            message, status_code = static_data_service.unavailable_payload()
            return {"ok": False, "status_code": status_code, "payload": message}

        user_id = (payload or {}).get("userId")
        password = (payload or {}).get("password")
        if not user_id or not password:
            return {
                "ok": False,
                "status_code": 400,
                "payload": {"message": "User ID and password are required"},
            }

        teachers_data = static_data_service.teachers_map()
        if user_id in teachers_data:
            teacher_info = teachers_data[user_id]
            is_class10 = teacher_info.get("current_standard") == 10
        else:
            student_info = static_data_service.students_map(False)
            class10_student_info = static_data_service.students_map(True)
            if user_id in class10_student_info:
                is_class10 = True
            elif user_id in student_info:
                is_class10 = False
            else:
                return {
                    "ok": False,
                    "status_code": 400,
                    "payload": {"message": "Invalid User ID"},
                }

        user = user_repo.get_user(user_id, is_class10)
        if not user or user.get("password") is None:
            return {
                "ok": False,
                "status_code": 401,
                "payload": {"message": "User not registered. Please register."},
            }
        if user.get("password") != password:
            return {
                "ok": False,
                "status_code": 401,
                "payload": {"message": "Invalid credentials"},
            }

        token = create_legacy_access_token(user_id=user_id, is_class10=is_class10)
        return {
            "ok": True,
            "status_code": 200,
            "payload": {
                "message": "Login successful",
                "token": token,
                "user_id": user_id,
                "class10": is_class10,
                "version": self.version,
            },
        }

    def register(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not static_data_service.ensure_loaded():
            message, status_code = static_data_service.unavailable_payload()
            return {"ok": False, "status_code": status_code, "payload": message}

        user_id = (payload or {}).get("userId")
        registration_code = (payload or {}).get("registrationCode")
        new_password = (payload or {}).get("newPassword")
        if not all([user_id, registration_code, new_password]):
            return {
                "ok": False,
                "status_code": 400,
                "payload": {
                    "message": "User ID, registration code, and new password are required"
                },
            }

        student_info = static_data_service.students_map(False)
        class10_student_info = static_data_service.students_map(True)
        if user_id in class10_student_info:
            is_class10 = True
        elif user_id in student_info:
            is_class10 = False
        else:
            return {
                "ok": False,
                "status_code": 400,
                "payload": {"message": "Invalid User ID"},
            }

        user = user_repo.get_user(user_id, is_class10)
        if user is None:
            return {"ok": False, "status_code": 404, "payload": {"message": "User not found"}}
        if user.get("password"):
            return {
                "ok": False,
                "status_code": 400,
                "payload": {"message": "User is already registered. Please login."},
            }
        if user.get("registration_code") != registration_code:
            return {
                "ok": False,
                "status_code": 401,
                "payload": {"message": "Invalid registration code"},
            }

        updated = user_repo.set_password(user_id, new_password, is_class10)
        if not updated:
            return {
                "ok": False,
                "status_code": 500,
                "payload": {"message": "Failed to update password"},
            }

        token = create_legacy_access_token(user_id=user_id, is_class10=is_class10)
        return {
            "ok": True,
            "status_code": 200,
            "payload": {
                "message": "Registration successful, logged in",
                "token": token,
                "user_id": user_id,
                "class10": is_class10,
                "version": self.version,
            },
        }


auth_service = AuthService()

