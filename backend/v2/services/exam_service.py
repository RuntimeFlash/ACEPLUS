import copy
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from db import convert_objectid_to_str, exam_repo, user_repo
from utils.data_utils import decode_unicode


class ExamService:
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
        unsubmitted_exams = col.find(
            {
                "userId": user_id,
                "is_submitted": False,
            }
        )
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_unsubmitted: List[Dict[str, Any]] = []

        for exam in unsubmitted_exams:
            try:
                exam_timestamp = datetime.strptime(exam["timestamp"], "%Y-%m-%d %H:%M:%S")
                if exam_timestamp > cutoff_date:
                    recent_unsubmitted.append(
                        {
                            "exam-id": exam["exam-id"],
                            "subject": exam.get("subject", "Unknown"),
                            "lessons": exam.get("lessons", []),
                            "timestamp": exam["timestamp"],
                            "test": exam.get("test", False),
                            "test_name": exam.get("test_name"),
                            "question_count": len(exam.get("questions", [])),
                        }
                    )
            except Exception:
                continue

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


exam_service = ExamService()

