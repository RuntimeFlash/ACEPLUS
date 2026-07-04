import copy
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import generate
from db import (
    convert_objectid_to_str,
    exam_repo,
    leaderboard_service,
    test_repo,
    user_stats_service,
    user_repo,
)
from utils.data_utils import calculate_lesson_analytics, decode_unicode
from utils.name_utils import generate_memorable_name
from services.replay_service import replay_service
from services.social_service import social_service


class ExamService:
    def create_exam(
        self,
        user_id: str,
        is_class10: bool,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        is_test = bool(payload.get("test", False))
        test_data = None

        if is_test:
            test_id = payload.get("test-id")
            if not test_id:
                return {"ok": False, "status_code": 400, "message": "Test ID is required"}
            test_data = test_repo.get_test(test_id, is_class10)
            if not test_data:
                return {
                    "ok": False,
                    "status_code": 404,
                    "message": "Test not found or already completed",
                }
            exam_id = f"{test_id}-{user_id}"
            subject = test_data.get("subject")
            lessons = test_data.get("lessons", [])
            questions = test_data.get("questions", [])
        else:
            from utils.lesson_utils import lesson2filepath

            subject = payload.get("subject")
            lessons = payload.get("lessons")
            if not subject or not lessons:
                return {
                    "ok": False,
                    "status_code": 400,
                    "message": "Subject and lessons are required",
                }
            lesson_paths = [lesson2filepath(subject, lesson, class10=is_class10) for lesson in lessons]
            if not lesson_paths:
                return {"ok": False, "status_code": 400, "message": "Invalid lessons provided"}
            exam_id = generate_memorable_name()
            try:
                questions = generate.generate_exam_questions(
                    subject,
                    lesson_paths,
                    user_id,
                    is_class10=is_class10,
                )
            except Exception as exc:
                return {
                    "ok": False,
                    "status_code": 500,
                    "message": f"Error generating questions: {str(exc)}",
                }

        now_utc = datetime.now(timezone.utc)
        exam_data = {
            "exam-id": exam_id,
            "userId": user_id,
            "standard": 10 if is_class10 else 9,
            "subject": subject,
            "lessons": lessons,
            "questions": questions,
            "is_submitted": False,
            "selected_answers": [],
            "class10": is_class10,
            "timestamp": now_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_dt": now_utc,
            "test": is_test,
        }
        if is_test and isinstance(test_data, dict):
            exam_data["test_name"] = test_data.get("test_name")

        created = exam_repo.add_exam(exam_data, is_class10)
        if not created:
            return {"ok": False, "status_code": 500, "message": "Error creating exam"}
        created_exam = self.get_exam(exam_id, is_class10)
        if not created_exam:
            return {"ok": False, "status_code": 500, "message": "Error loading created exam"}
        response_payload = {**created_exam, "exam-id": created_exam.get("exam-id", exam_id)}
        # Keep legacy nested shape while also returning /api/exam-compatible top-level fields.
        response_payload["exam"] = created_exam
        return {
            "ok": True,
            "status_code": 201,
            "payload": response_payload,
        }

    def submit_exam(
        self,
        exam_id: str,
        user_id: str,
        is_class10: bool,
        selected_answers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        exam = exam_repo.get_exam(exam_id, is_class10)
        if not exam:
            return {"ok": False, "status_code": 404, "message": "Exam not found"}
        if exam.get("is_submitted", False):
            return {"ok": False, "status_code": 400, "message": "Exam already submitted"}
        if exam.get("userId") != user_id:
            return {"ok": False, "status_code": 401, "message": "Unauthorized"}

        total_questions = len(exam.get("questions", []))
        if total_questions == 0:
            return {"ok": False, "status_code": 400, "message": "Exam has no questions"}

        score = 0
        questions_needing_solutions: List[Dict[str, Any]] = []
        initial_results: List[Dict[str, Any]] = []

        for index, (question, selected_answer) in enumerate(
            zip(exam["questions"], selected_answers),
            1,
        ):
            correct_answer = question.get("answer")
            selected_option_key = selected_answer.get("option")
            is_correct = selected_option_key == correct_answer
            if is_correct:
                score += 1

            options = question.get("options", {})
            selected_option_value = options.get(selected_option_key, "")
            correct_option_value = options.get(correct_answer, "")
            result = {
                "question-no": str(index),
                "question": question.get("question"),
                "is_correct": is_correct,
                "selected_answer": f"{selected_option_key}) {selected_option_value}",
                "correct_answer": f"{correct_answer}) {correct_option_value}",
                "solution": None,
            }
            initial_results.append(result)

            if not is_correct:
                questions_needing_solutions.append(
                    {
                        "question": question.get("question"),
                        "correct_answer": correct_option_value,
                        "given_answer": selected_option_value,
                        "options": options,
                        "index": index - 1,
                    }
                )

        percentage = (score / total_questions) * 100 if total_questions else 0
        lesson_analytics = calculate_lesson_analytics(exam["questions"], selected_answers)

        try:
            performance_analysis = generate.generate_performance_analysis(
                initial_results,
                exam.get("lessons", []),
                is_class10,
            )
        except Exception:
            performance_analysis = None

        submitted_at_utc = datetime.now(timezone.utc)
        updated_data = {
            "is_submitted": True,
            "selected_answers": selected_answers,
            "score": score,
            "percentage": percentage,
            "results": initial_results,
            "lessons": exam.get("lessons", []),
            "lesson_analytics": lesson_analytics,
            "submission_timestamp": submitted_at_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "submission_timestamp_dt": submitted_at_utc,
            "test": exam.get("test", False),
            "performance_analysis": performance_analysis,
            "questions_needing_solutions": [q["index"] for q in questions_needing_solutions],
        }
        if updated_data["test"]:
            updated_data["test_name"] = exam.get("test_name")

        if exam.get("test", False):
            test_id = "-".join(exam_id.split("-")[:-1])
            test_data = test_repo.get_test(test_id, is_class10)
            if test_data:
                completed_by = test_data.get("completed_by", [])
                if user_id not in completed_by:
                    completed_by.append(user_id)
                    test_repo.update_test(test_id, {"completed_by": completed_by}, is_class10)

        if not exam_repo.update_exam(exam_id, updated_data, is_class10):
            return {"ok": False, "status_code": 500, "message": "Failed to submit exam"}

        try:
            replay_service.ingest_exam_mistakes(
                exam_id=exam_id,
                user_id=user_id,
                is_class10=is_class10,
                subject=exam.get("subject", ""),
                lessons=exam.get("lessons", []),
                questions=exam.get("questions", []),
                selected_answers=selected_answers,
            )
        except Exception:
            pass

        try:
            user_stats_service.update_stats_after_exam(
                user_id,
                exam["subject"],
                score,
                total_questions,
                float(percentage),
                exam_id,
                exam.get("lessons", []),
                exam.get("test", False),
                exam.get("test_name"),
                is_class10,
            )
            standard = 10 if is_class10 else 9
            leaderboard_service.update_on_submission(user_id, standard)
        except Exception:
            pass

        try:
            social_service.update_progress_after_exam(
                user_id=user_id,
                subject=str(exam.get("subject", "")),
                exam_id=exam_id,
                score=score,
                total_questions=total_questions,
                percentage=float(percentage),
                is_test=bool(exam.get("test", False)),
            )
        except Exception:
            pass

        completed_tasks = self._check_and_update_tasks(user_id, is_class10, exam)

        if exam.get("test", False):
            user = user_repo.get_user(user_id, is_class10)
            if user:
                new_coins = user.get("coins", 0) + 10
                user_repo.update_tasks(
                    user_id,
                    user.get("tasks", {}),
                    is_class10=is_class10,
                    coins=new_coins,
                )
                completed_tasks.append({"title": "Test Completion Bonus", "reward": 10})

        return {
            "ok": True,
            "status_code": 200,
            "payload": {
                "message": "Exam submitted successfully",
                "score": score,
                "total_questions": total_questions,
                "percentage": percentage,
                "results": initial_results,
                "questions_needing_solutions": [q["index"] for q in questions_needing_solutions],
                "completed_tasks": completed_tasks,
            },
        }

    def get_exam(self, exam_id: str, is_class10: bool) -> Optional[Dict[str, Any]]:
        exam_data = exam_repo.get_exam(exam_id, is_class10)
        if not exam_data:
            return None

        response_data = copy.deepcopy(exam_data)
        if not response_data.get("is_submitted", False):
            for question in response_data.get("questions", []):
                question.pop("answer", None)
        response_data = decode_unicode(response_data)
        return convert_objectid_to_str(response_data)

    def get_user_exams(self, user_id: str, is_class10: bool) -> List[Dict[str, Any]]:
        overview_list = user_repo.get_user_exams_overview(user_id, is_class10)
        return convert_objectid_to_str(overview_list)

    def get_recent_unsubmitted_exams(self, user_id: str, is_class10: bool) -> Dict[str, Any]:
        col = exam_repo._col_by_params(is_class10=is_class10)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        unsubmitted_exams = col.find(
            {
                "userId": user_id,
                "is_submitted": False,
                "timestamp_dt": {"$gte": cutoff_date},
            },
            {
                "exam-id": 1,
                "subject": 1,
                "lessons": 1,
                "timestamp": 1,
                "test": 1,
                "test_name": 1,
                "questions": 1,
            }
        )
        recent_unsubmitted: List[Dict[str, Any]] = []

        for exam in unsubmitted_exams:
            recent_unsubmitted.append(
                {
                    "exam-id": exam["exam-id"],
                    "subject": exam.get("subject", "Unknown"),
                    "lessons": exam.get("lessons", []),
                    "timestamp": exam.get("timestamp"),
                    "test": exam.get("test", False),
                    "test_name": exam.get("test_name"),
                    "question_count": len(exam.get("questions", [])),
                }
            )

        # Legacy fallback for exams created before timestamp_dt existed.
        legacy_unsubmitted = col.find(
            {
                "userId": user_id,
                "is_submitted": False,
                "timestamp_dt": {"$exists": False},
            },
            {
                "exam-id": 1,
                "subject": 1,
                "lessons": 1,
                "timestamp": 1,
                "test": 1,
                "test_name": 1,
                "questions": 1,
            },
        )
        for exam in legacy_unsubmitted:
            timestamp_str = exam.get("timestamp")
            if not timestamp_str:
                continue
            try:
                exam_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
            except Exception:
                continue
            if exam_timestamp < cutoff_date:
                continue
            recent_unsubmitted.append(
                {
                    "exam-id": exam["exam-id"],
                    "subject": exam.get("subject", "Unknown"),
                    "lessons": exam.get("lessons", []),
                    "timestamp": timestamp_str,
                    "test": exam.get("test", False),
                    "test_name": exam.get("test_name"),
                    "question_count": len(exam.get("questions", [])),
                }
            )

        recent_unsubmitted.sort(key=lambda item: item["timestamp"], reverse=True)
        return {
            "unsubmitted_exams": recent_unsubmitted,
            "count": len(recent_unsubmitted),
        }

    def delete_unsubmitted_exam(
        self,
        exam_id: str,
        user_id: str,
        is_class10: bool,
    ) -> Dict[str, Any]:
        exam = exam_repo.get_exam(exam_id, is_class10)
        if not exam:
            return {"ok": False, "status_code": 404, "message": "Exam not found"}
        if exam.get("userId") != user_id:
            return {"ok": False, "status_code": 401, "message": "Unauthorized access to exam"}
        if exam.get("is_submitted", False):
            return {"ok": False, "status_code": 400, "message": "Cannot delete submitted exams"}

        success = exam_repo.delete_exam(exam_id, is_class10)
        if not success:
            return {"ok": False, "status_code": 500, "message": "Failed to delete exam"}
        return {
            "ok": True,
            "status_code": 200,
            "payload": {
                "message": "Exam deleted successfully",
                "exam_id": exam_id,
            },
        }

    def save_exam_answers(
        self,
        exam_id: str,
        user_id: str,
        is_class10: bool,
        answers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        exam = exam_repo.get_exam(exam_id, is_class10)
        if not exam:
            return {"ok": False, "status_code": 404, "message": "Exam not found"}
        if exam.get("userId") != user_id:
            return {"ok": False, "status_code": 401, "message": "Unauthorized"}
        if exam.get("is_submitted", False):
            return {"ok": False, "status_code": 400, "message": "Exam already submitted"}

        update_data = {
            "selected_answers": answers,
            "last_saved_at": datetime.utcnow().isoformat(timespec="seconds"),
        }
        success = exam_repo.update_exam(exam_id, update_data, is_class10)
        if not success:
            return {"ok": False, "status_code": 500, "message": "Failed to save answers"}

        return {
            "ok": True,
            "status_code": 200,
            "payload": {
                "message": "Answers saved",
                "exam-id": exam_id,
                "saved_answers": len(answers),
            },
        }

    def _check_and_update_tasks(
        self,
        user_id: str,
        is_class10: bool,
        exam_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        user = user_repo.get_user(user_id, is_class10)
        if not user or "tasks" not in user or "tasks_list" not in user["tasks"]:
            return []

        tasks = user["tasks"]["tasks_list"]
        completed_tasks = []
        coins_earned = 0
        exam_subject = exam_data.get("subject")
        exam_lessons = exam_data.get("lessons", [])

        for task in tasks:
            if task.get("completed"):
                continue

            task_id = task.get("id")
            task_action = task.get("action", {})
            task_type = task_action.get("type")

            if task_id == 1 and task_type == "exam":
                task["num_completed"] = task.get("num_completed", 0) + 1
                if task.get("num_completed", 0) >= task.get("details", {}).get("count", 0):
                    task["completed"] = True
            elif task_id == 2 and task_type == "exam" and task_action.get("subject") == exam_subject:
                task["completed"] = True
            elif (
                task_id == 3
                and task_type == "exam"
                and task_action.get("subject") == exam_subject
                and set(task_action.get("lessons", [])) == set(exam_lessons)
            ):
                task["completed"] = True
            elif task_id == 4:
                if task_type == "test" and exam_data.get("test"):
                    test_id = "-".join(exam_data.get("exam-id", "").split("-")[:-1])
                    if task_action.get("test-id") == test_id:
                        task["completed"] = True
                elif (
                    task_type == "exam"
                    and task_action.get("subject") == exam_subject
                    and set(task_action.get("lessons", [])) == set(exam_lessons)
                ):
                    task["completed"] = True
            elif (
                task_id == 5
                and task_type == "exam"
                and task_action.get("subject") == exam_subject
                and set(task_action.get("lessons", [])) == set(exam_lessons)
            ):
                task["completed"] = True

            if task.get("completed"):
                completed_tasks.append(task)
                coins_earned += int(task.get("reward", 0))

        if coins_earned > 0:
            user["coins"] = user.get("coins", 0) + coins_earned
            user_repo.update_tasks(
                user_id,
                user["tasks"],
                is_class10=is_class10,
                coins=user.get("coins"),
            )

        return completed_tasks


exam_service = ExamService()
