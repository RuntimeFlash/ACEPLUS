from __future__ import annotations

from services.exam_service import ExamService


def test_create_exam_returns_top_level_exam_fields_and_legacy_exam_wrapper(monkeypatch) -> None:
    created_exam = {
        "exam-id": "test-1-u1",
        "subject": "Math",
        "lessons": ["lesson1"],
        "questions": [{"question": "Q1", "options": {"a": "A", "b": "B", "c": "C", "d": "D"}}],
        "is_submitted": False,
    }

    monkeypatch.setattr(
        "services.exam_service.test_repo.get_test",
        lambda test_id, is_class10: {
            "subject": "Math",
            "lessons": ["lesson1"],
            "questions": [{"question": "Q1"}],
            "test_name": "Weekly Test",
        },
    )
    monkeypatch.setattr("services.exam_service.exam_repo.add_exam", lambda exam_data, is_class10: exam_data)

    service = ExamService()
    monkeypatch.setattr(service, "get_exam", lambda exam_id, is_class10: created_exam)

    result = service.create_exam(
        user_id="u1",
        is_class10=False,
        payload={"test": True, "test-id": "test-1"},
    )

    assert result["ok"] is True
    assert result["status_code"] == 201
    payload = result["payload"]
    assert payload["exam-id"] == "test-1-u1"
    assert payload["questions"] == created_exam["questions"]
    assert payload["subject"] == created_exam["subject"]
    assert payload["exam"] == created_exam

