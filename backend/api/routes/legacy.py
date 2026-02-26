from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional

import generate
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.datastructures import UploadFile

from core.auth import CurrentUser, get_current_user
from db import (
    exam_repo,
    question_report_repo,
    test_database_service,
    test_repo,
    upload_repo,
    user_repo,
)
from services.static_data import static_data_service
from utils.lesson_utils import lesson2filepath
from utils.name_utils import generate_memorable_name


router = APIRouter(tags=["legacy-compat"])


def _normalize_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _extract_answer_text(option_text: str) -> str:
    raw = str(option_text or "")
    if ")" in raw:
        return raw.split(")", 1)[1].strip()
    return raw.strip()


def _sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _build_tests_payload(test_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for test in test_docs:
        questions = test.get("questions", [])
        payload.append(
            {
                "test-id": test.get("test-id"),
                "test_name": test.get("test_name"),
                "subject": test.get("subject"),
                "lessons": test.get("lessons", []) or [],
                "questions": len(questions) if isinstance(questions, list) else int(test.get("question_count", 0)),
                "description": test.get("description", ""),
            }
        )
    return payload


@router.get("/tests")
def get_tests(current_user: CurrentUser = Depends(get_current_user)):
    user = user_repo.get_user(current_user.user_id, current_user.is_class10)
    if not user:
        return JSONResponse(content={"message": "User not found"}, status_code=404)

    standard = 10 if current_user.is_class10 else 9
    is_teacher = bool(user.get("teacher", False))

    if is_teacher:
        docs = test_repo.get_tests_created_by(standard=standard, created_by=current_user.user_id)
        teacher_data = static_data_service.teachers_map().get(current_user.user_id, {})
        teacher_standard = teacher_data.get("standard", [standard])
        if isinstance(teacher_standard, int):
            teacher_standard = [teacher_standard]
        return {
            "tests": _build_tests_payload(docs),
            "teacher": True,
            "teacher_subject": teacher_data.get("subject", ""),
            "teacher_standard": teacher_standard,
        }

    docs = test_database_service.get_available_tests_for_student(
        standard=standard,
        user_id=current_user.user_id,
        division=user.get("division"),
    )
    return {"tests": _build_tests_payload(docs), "teacher": False}


@router.post("/generate_test")
def generate_test(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    subject = str(payload.get("subject", "")).strip()
    lessons = payload.get("lessons", [])
    is_class10 = _normalize_bool(payload.get("class10"), default=current_user.is_class10)

    if not subject or not isinstance(lessons, list) or not lessons:
        return JSONResponse(content={"message": "subject and lessons are required"}, status_code=400)

    lesson_paths = [lesson2filepath(subject, lesson, class10=is_class10) for lesson in lessons]
    lesson_paths = [path for path in lesson_paths if path]
    if not lesson_paths:
        return JSONResponse(content={"message": "Invalid lessons provided"}, status_code=400)

    try:
        questions = generate.generate_exam_questions(
            subject=subject,
            lesson_files=lesson_paths,
            user_id=current_user.user_id,
            is_class10=is_class10,
        )
    except Exception as exc:
        return JSONResponse(content={"message": f"Failed to generate test: {exc}"}, status_code=500)

    return {"questions": questions}


@router.post("/create_test")
def create_test(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    subject = str(payload.get("subject", "")).strip()
    lessons = payload.get("lessons", []) or []
    questions = payload.get("questions", []) or []
    if not subject or not isinstance(questions, list) or not questions:
        return JSONResponse(content={"message": "subject and questions are required"}, status_code=400)

    is_class10 = _normalize_bool(payload.get("class10"), default=current_user.is_class10)
    standard = 10 if is_class10 else 9
    test_id = str(payload.get("test-id") or generate_memorable_name())

    test_data: Dict[str, Any] = {
        "test-id": test_id,
        "test_name": str(payload.get("test_name", "")).strip() or None,
        "subject": subject,
        "lessons": lessons if isinstance(lessons, list) else [],
        "questions": questions,
        "standard": standard,
        "created_by": current_user.user_id,
        "completed_by": [],
        "division": payload.get("division"),
        "students": payload.get("students") if isinstance(payload.get("students"), list) else None,
        "expiration_date": payload.get("expiration_date"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        test_repo.add_test(test_data, is_class10=is_class10)
    except Exception as exc:
        return JSONResponse(content={"message": f"Failed to create test: {exc}"}, status_code=500)

    return JSONResponse(
        content={"message": "Test created successfully", "test-id": test_id},
        status_code=201,
    )


@router.get("/subject_stats/{subject}")
def get_subject_stats(subject: str, current_user: CurrentUser = Depends(get_current_user)):
    stats = user_repo.get_user_subject_stats(current_user.user_id, subject, current_user.is_class10)
    if not stats:
        return {
            "subject": subject,
            "attempted": 0,
            "avgPercentage": 0.0,
            "marksGained": 0,
            "marksAttempted": 0,
            "highestMark": 0.0,
            "lowestMark": 0.0,
        }
    return stats


@router.post("/report")
def report_question(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    exam_id = str(payload.get("examId", "")).strip()
    question_id = str(payload.get("questionId", "")).strip()
    question_index = int(payload.get("questionIndex", 0) or 0)
    reason = str(payload.get("reason", "")).strip()
    description = str(payload.get("description", "")).strip()

    if not exam_id or not question_index or not description:
        return JSONResponse(
            content={"message": "examId, questionIndex and description are required"},
            status_code=400,
        )

    report_doc = {
        "user_id": current_user.user_id,
        "exam_id": exam_id,
        "question_id": question_id or None,
        "question_index": question_index,
        "reason": reason or None,
        "description": description,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    created = question_report_repo.create_report_if_absent(report_doc, is_class10=current_user.is_class10)
    return {"message": "Question report submitted", "created": bool(created)}


@router.get("/students_by_standard")
def get_students_by_standard(
    class10: Optional[str] = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
):
    is_class10 = _normalize_bool(class10, default=current_user.is_class10)
    standard = 10 if is_class10 else 9
    return user_repo.get_all_students_by_standard(standard)


@router.post("/upload_files")
async def upload_files(request: Request, current_user: CurrentUser = Depends(get_current_user)):
    form = await request.form()
    uploads = [value for value in form.values() if isinstance(value, UploadFile)]
    if not uploads:
        return JSONResponse(content={"message": "No files uploaded"}, status_code=400)

    items: List[Dict[str, Any]] = []
    for upload in uploads:
        raw = await upload.read()
        if not raw:
            continue
        file_id = upload_repo.save_file(
            data=raw,
            filename=upload.filename or "upload.bin",
            user_id=current_user.user_id,
            is_class10=current_user.is_class10,
            content_type=upload.content_type,
            file_kind="original",
        )
        ext = os.path.splitext((upload.filename or "").lower())[1]
        if ext in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
            file_type = "image"
        elif ext == ".pdf":
            file_type = "pdf"
        elif ext == ".pptx":
            file_type = "pptx"
        else:
            file_type = "file"
        items.append({"filename": file_id, "type": file_type, "previews": []})

    if not items:
        return JSONResponse(content={"message": "No valid files uploaded"}, status_code=400)
    return {"items": items}


@router.post("/upload_images")
async def upload_images(request: Request, current_user: CurrentUser = Depends(get_current_user)):
    return await upload_files(request, current_user)


@router.get("/uploads/{filename}")
def get_uploaded_file(filename: str, current_user: CurrentUser = Depends(get_current_user)):
    doc = upload_repo.get_file(filename, is_class10=current_user.is_class10)
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    media_type = doc.get("content_type") or "application/octet-stream"
    return StreamingResponse(
        BytesIO(doc.get("data", b"")),
        media_type=media_type,
        headers={"X-Original-Filename": str(doc.get("filename", ""))},
    )


def _file_generation_stream(file_ids: List[str], is_class10: bool):
    temp_dir = tempfile.mkdtemp(prefix="aceplus-gen-")
    temp_paths: List[str] = []
    try:
        for file_id in file_ids:
            doc = upload_repo.get_file(file_id, is_class10=is_class10)
            if not doc:
                yield _sse("error", {"message": f"File not found: {file_id}"})
                return
            filename = str(doc.get("filename") or file_id)
            _, ext = os.path.splitext(filename)
            safe_ext = ext if ext else ".bin"
            temp_path = os.path.join(temp_dir, f"{file_id}{safe_ext}")
            with open(temp_path, "wb") as f:
                f.write(doc.get("data", b""))
            temp_paths.append(temp_path)

        yield _sse("start", {"message": "Starting file processing..."})

        for event in generate.analyze_files(temp_paths):
            event_type = event.get("type")
            if event_type == "total":
                yield _sse("total", {"count": int(event.get("count", 0))})
            elif event_type == "progress":
                yield _sse("progress", {"count": int(event.get("count", 0))})
            elif event_type == "result":
                yield _sse("result", {"questions": event.get("questions", [])})
            elif event_type == "error":
                yield _sse("error", {"message": str(event.get("message", "Unknown error"))})
                return
    except Exception as exc:
        yield _sse("error", {"message": str(exc)})
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/generate_from_files")
def generate_from_files(
    filenames: List[str] = Query(default=[]),
    current_user: CurrentUser = Depends(get_current_user),
):
    if not filenames:
        return JSONResponse(content={"message": "filenames are required"}, status_code=400)
    stream = _file_generation_stream(filenames, is_class10=current_user.is_class10)
    return StreamingResponse(stream, media_type="text/event-stream")


@router.get("/generate_from_images")
def generate_from_images(
    filenames: List[str] = Query(default=[]),
    current_user: CurrentUser = Depends(get_current_user),
):
    return generate_from_files(filenames=filenames, current_user=current_user)


@router.post("/generate_hint")
def generate_hint(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    _ = current_user
    question = str(payload.get("question", "")).strip()
    if not question:
        return JSONResponse(content={"message": "question is required"}, status_code=400)
    return StreamingResponse(generate.generate_hint(question), media_type="text/plain")


@router.post("/generate_solution")
def generate_solution(
    payload: Dict[str, Any] = Body(default={}),
    current_user: CurrentUser = Depends(get_current_user),
):
    exam_id = str(payload.get("examId", "")).strip()
    question_index = payload.get("questionIndex")
    if not exam_id or question_index is None:
        return JSONResponse(content={"message": "examId and questionIndex are required"}, status_code=400)

    try:
        idx = int(question_index)
    except Exception:
        return JSONResponse(content={"message": "questionIndex must be an integer"}, status_code=400)

    exam = exam_repo.get_exam(exam_id, current_user.is_class10)
    if not exam:
        return JSONResponse(content={"message": "Exam not found"}, status_code=404)

    results = exam.get("results", []) or []
    questions = exam.get("questions", []) or []
    if idx < 0 or idx >= len(results) or idx >= len(questions):
        return JSONResponse(content={"message": "Invalid question index"}, status_code=400)

    result = results[idx]
    question = questions[idx]
    question_text = str(result.get("question") or question.get("question") or "")
    correct_answer = _extract_answer_text(str(result.get("correct_answer", "")))
    given_answer = _extract_answer_text(str(result.get("selected_answer", "")))
    options = question.get("options", {}) or {}

    if not question_text:
        return JSONResponse(content={"message": "Question data unavailable"}, status_code=400)

    return StreamingResponse(
        generate.generate_solution_stream(
            question_text=question_text,
            correct_answer=correct_answer,
            given_answer=given_answer,
            options=options,
        ),
        media_type="text/plain",
    )
