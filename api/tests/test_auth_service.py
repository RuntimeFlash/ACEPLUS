from __future__ import annotations

from typing import Any, Dict, Optional
import pytest

from services.auth_service import auth_service
from services.static_data import static_data_service
from db import user_repo


class _MockUserRepo:
    def __init__(self) -> None:
        self.users: Dict[str, Dict[str, Any]] = {}
        self.passwords: Dict[str, str] = {}
        self.set_password_fail = False

    def get_user(self, user_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        # Simulated db lookup.
        # AuthService uses: user = user_repo.get_user(user_id, is_class10)
        return self.users.get(user_id)

    def set_password(self, user_id: str, new_password: str, is_class10: Optional[bool] = None) -> bool:
        if self.set_password_fail:
            return False
        if user_id in self.users:
            self.users[user_id]["password"] = new_password
            return True
        return False


@pytest.fixture
def mock_auth_dependencies(monkeypatch):
    # Setup mock data mapping
    mock_teachers = {
        "teacher-1": {"current_standard": 10},
        "teacher-2": {"current_standard": 9},
    }
    mock_class9_students = {
        "student-9a": {"registration_code": "code-9a", "division": "A"},
    }
    mock_class10_students = {
        "student-10a": {"registration_code": "code-10a", "division": "A"},
    }

    # Track if static data is loaded
    static_data_state = {"loaded": True}

    monkeypatch.setattr(static_data_service, "ensure_loaded", lambda: static_data_state["loaded"])
    monkeypatch.setattr(static_data_service, "teachers_map", lambda: mock_teachers)
    monkeypatch.setattr(
        static_data_service,
        "students_map",
        lambda is_class10: mock_class10_students if is_class10 else mock_class9_students,
    )

    # Instantiate fake user repo and patch db.user_repo
    fake_user_repo = _MockUserRepo()
    monkeypatch.setattr(user_repo, "get_user", fake_user_repo.get_user)
    monkeypatch.setattr(user_repo, "set_password", fake_user_repo.set_password)

    # Patch create_legacy_access_token
    monkeypatch.setattr("services.auth_service.create_legacy_access_token", lambda user_id, is_class10: f"token-{user_id}")

    return {
        "fake_user_repo": fake_user_repo,
        "static_data_state": static_data_state,
        "teachers": mock_teachers,
        "class9_students": mock_class9_students,
        "class10_students": mock_class10_students,
    }


def test_login_success_student_class9(mock_auth_dependencies) -> None:
    repo = mock_auth_dependencies["fake_user_repo"]
    repo.users["student-9a"] = {
        "id": "student-9a",
        "password": "correct-password",
    }

    payload = {"userId": "student-9a", "password": "correct-password"}
    result = auth_service.login(payload)

    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["payload"]["message"] == "Login successful"
    assert result["payload"]["token"] == "token-student-9a"
    assert result["payload"]["class10"] is False


def test_login_success_student_class10(mock_auth_dependencies) -> None:
    repo = mock_auth_dependencies["fake_user_repo"]
    repo.users["student-10a"] = {
        "id": "student-10a",
        "password": "correct-password",
    }

    payload = {"userId": "student-10a", "password": "correct-password"}
    result = auth_service.login(payload)

    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["payload"]["message"] == "Login successful"
    assert result["payload"]["token"] == "token-student-10a"
    assert result["payload"]["class10"] is True


def test_login_success_teacher(mock_auth_dependencies) -> None:
    repo = mock_auth_dependencies["fake_user_repo"]
    repo.users["teacher-1"] = {
        "id": "teacher-1",
        "password": "correct-password",
    }

    payload = {"userId": "teacher-1", "password": "correct-password"}
    result = auth_service.login(payload)

    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["payload"]["message"] == "Login successful"
    assert result["payload"]["token"] == "token-teacher-1"
    assert result["payload"]["class10"] is True


def test_login_static_data_unavailable(mock_auth_dependencies) -> None:
    mock_auth_dependencies["static_data_state"]["loaded"] = False

    payload = {"userId": "student-9a", "password": "password"}
    result = auth_service.login(payload)

    assert result["ok"] is False
    assert result["status_code"] == 500
    assert "MongoDB" in result["payload"]["message"]


def test_login_missing_credentials(mock_auth_dependencies) -> None:
    payload = {"userId": ""}
    result = auth_service.login(payload)

    assert result["ok"] is False
    assert result["status_code"] == 400
    assert "required" in result["payload"]["message"]


def test_login_invalid_user_id(mock_auth_dependencies) -> None:
    payload = {"userId": "unknown-user", "password": "password"}
    result = auth_service.login(payload)

    assert result["ok"] is False
    assert result["status_code"] == 400
    assert "Invalid User ID" in result["payload"]["message"]


def test_login_user_not_registered(mock_auth_dependencies) -> None:
    # student-9a exists in static data map but has no password set in database
    repo = mock_auth_dependencies["fake_user_repo"]
    repo.users["student-9a"] = {
        "id": "student-9a",
        "password": None,
    }

    payload = {"userId": "student-9a", "password": "password"}
    result = auth_service.login(payload)

    assert result["ok"] is False
    assert result["status_code"] == 401
    assert "not registered" in result["payload"]["message"]


def test_login_invalid_credentials(mock_auth_dependencies) -> None:
    repo = mock_auth_dependencies["fake_user_repo"]
    repo.users["student-9a"] = {
        "id": "student-9a",
        "password": "correct-password",
    }

    payload = {"userId": "student-9a", "password": "wrong-password"}
    result = auth_service.login(payload)

    assert result["ok"] is False
    assert result["status_code"] == 401
    assert "Invalid credentials" in result["payload"]["message"]


def test_register_success(mock_auth_dependencies) -> None:
    repo = mock_auth_dependencies["fake_user_repo"]
    repo.users["student-9a"] = {
        "id": "student-9a",
        "registration_code": "code-9a",
        "password": None,
    }

    payload = {
        "userId": "student-9a",
        "registrationCode": "code-9a",
        "newPassword": "new-password",
    }
    result = auth_service.register(payload)

    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["payload"]["message"] == "Registration successful, logged in"
    assert result["payload"]["token"] == "token-student-9a"
    assert repo.users["student-9a"]["password"] == "new-password"


def test_register_static_data_unavailable(mock_auth_dependencies) -> None:
    mock_auth_dependencies["static_data_state"]["loaded"] = False

    payload = {
        "userId": "student-9a",
        "registrationCode": "code-9a",
        "newPassword": "new-password",
    }
    result = auth_service.register(payload)

    assert result["ok"] is False
    assert result["status_code"] == 500
    assert "MongoDB" in result["payload"]["message"]


def test_register_missing_fields(mock_auth_dependencies) -> None:
    payload = {
        "userId": "student-9a",
        "registrationCode": "",
        "newPassword": "new-password",
    }
    result = auth_service.register(payload)

    assert result["ok"] is False
    assert result["status_code"] == 400
    assert "required" in result["payload"]["message"]


def test_register_invalid_user_id(mock_auth_dependencies) -> None:
    payload = {
        "userId": "unknown-user",
        "registrationCode": "code",
        "newPassword": "password",
    }
    result = auth_service.register(payload)

    assert result["ok"] is False
    assert result["status_code"] == 400
    assert "Invalid User ID" in result["payload"]["message"]


def test_register_user_not_found(mock_auth_dependencies) -> None:
    # student-9a is valid in static data map but does not exist in database repo
    payload = {
        "userId": "student-9a",
        "registrationCode": "code-9a",
        "newPassword": "new-password",
    }
    result = auth_service.register(payload)

    assert result["ok"] is False
    assert result["status_code"] == 404
    assert "User not found" in result["payload"]["message"]


def test_register_user_already_registered(mock_auth_dependencies) -> None:
    repo = mock_auth_dependencies["fake_user_repo"]
    repo.users["student-9a"] = {
        "id": "student-9a",
        "password": "already-set-password",
    }

    payload = {
        "userId": "student-9a",
        "registrationCode": "code-9a",
        "newPassword": "new-password",
    }
    result = auth_service.register(payload)

    assert result["ok"] is False
    assert result["status_code"] == 400
    assert "already registered" in result["payload"]["message"]


def test_register_invalid_registration_code(mock_auth_dependencies) -> None:
    repo = mock_auth_dependencies["fake_user_repo"]
    repo.users["student-9a"] = {
        "id": "student-9a",
        "registration_code": "code-9a",
        "password": None,
    }

    payload = {
        "userId": "student-9a",
        "registrationCode": "incorrect-code",
        "newPassword": "new-password",
    }
    result = auth_service.register(payload)

    assert result["ok"] is False
    assert result["status_code"] == 401
    assert "Invalid registration code" in result["payload"]["message"]


def test_register_failed_database_update(mock_auth_dependencies) -> None:
    repo = mock_auth_dependencies["fake_user_repo"]
    repo.users["student-9a"] = {
        "id": "student-9a",
        "registration_code": "code-9a",
        "password": None,
    }
    repo.set_password_fail = True

    payload = {
        "userId": "student-9a",
        "registrationCode": "code-9a",
        "newPassword": "new-password",
    }
    result = auth_service.register(payload)

    assert result["ok"] is False
    assert result["status_code"] == 500
    assert "Failed to update password" in result["payload"]["message"]
