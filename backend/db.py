import os
import threading
import queue
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pytz import timezone as pytz_timezone
from typing import Any, Dict, List, Optional, Tuple
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from bson import ObjectId
from gridfs import GridFSBucket
import hashlib
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(current_dir, ".env"))

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

IST = pytz_timezone("Asia/Kolkata")

def convert_objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    else:
        return obj

def month_key_from_date_str(date_str: str) -> str:
    # date is in 'dd-mm-YYYY'
    try:
        dt = datetime.strptime(date_str, "%d-%m-%Y")
    except Exception:
        # If format unexpected, fallback to current month
        dt = datetime.now(IST)
    return dt.strftime("%Y-%m")

def current_month_key() -> str:
    return datetime.now(IST).strftime("%Y-%m")

# -----------------------------------------------------------------------------
# Database Client and WriteQueue
# -----------------------------------------------------------------------------

class DatabaseClient:
    """Mongo client wrapper supporting class-wise (9/10) DB segregation."""

    def __init__(self) -> None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise ValueError("MONGODB_URI environment variable is not set")

        db9_name = os.getenv("MONGODB_DB_CLASS9")
        db10_name = os.getenv("MONGODB_DB_CLASS10")

        if not db9_name or not db10_name:
            raise ValueError(
                "Database names for both classes must be set. "
                "Please define MONGODB_DB_CLASS9 and MONGODB_DB_CLASS10 in your environment."
            )

        self._client = MongoClient(uri)
        self._db9 = self._client[db9_name]
        self._db10 = self._client[db10_name]

    def get_collection(
        self,
        name: str,
        is_class10: Optional[bool] = None,
        standard: Optional[int] = None
    ) -> Collection:
        if is_class10 is not None:
            return (self._db10 if is_class10 else self._db9)[name]
        if standard is not None:
            return (self._db10 if int(standard) == 10 else self._db9)[name]
        # default to class 9 if ambiguous
        return self._db9[name]


class WriteQueue:
    """Threaded 'no-wait' write queue for fire-and-forget operations."""

    def __init__(self, db_client: DatabaseClient, worker_count: int = 1) -> None:
        self.db_client = db_client
        self._sync_mode = os.getenv("SERVERLESS", "0") == "1"
        self._q: "queue.Queue[Tuple[str, Tuple, Dict]]" = queue.Queue()
        self._workers: List[threading.Thread] = []
        self._stop_event = threading.Event()
        if self._sync_mode:
            return
        for i in range(worker_count):
            t = threading.Thread(target=self._worker, name=f"WriteQueueWorker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

    def enqueue(self, op_name: str, *args, **kwargs) -> None:
        """Enqueue an operation by name and args; repository methods will interpret."""
        if self._sync_mode:
            func = kwargs.pop("callable", None)
            if callable(func):
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print(f"[WriteQueue] Error processing op {op_name}: {e}")
            return
        self._q.put((op_name, args, kwargs))

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                op_name, args, kwargs = self._q.get(timeout=1.0)
            except queue.Empty:
                continue
            try:
                # Dispatch via a callable if provided.
                func = kwargs.pop("callable", None)
                if callable(func):
                    func(*args, **kwargs)
            except Exception as e:
                print(f"[WriteQueue] Error processing op {op_name}: {e}")
            finally:
                self._q.task_done()

    def stop(self) -> None:
        if self._sync_mode:
            return
        self._stop_event.set()
        for t in self._workers:
            t.join(timeout=1.0)


class UploadRepository:
    """Stores user uploads in Mongo GridFS to avoid local-disk dependency."""

    def __init__(self, db_client: DatabaseClient) -> None:
        self.db_client = db_client
        self._bucket9 = GridFSBucket(db_client._db9, bucket_name="uploads")
        self._bucket10 = GridFSBucket(db_client._db10, bucket_name="uploads")
        for std in (9, 10):
            files_col = db_client.get_collection("uploads.files", standard=std)
            files_col.create_index([("metadata.user_id", ASCENDING), ("uploadDate", DESCENDING)])
            files_col.create_index([("metadata.parent_file_id", ASCENDING)])

    @staticmethod
    def _parse_object_id(file_id: str) -> Optional[ObjectId]:
        try:
            return ObjectId(file_id)
        except Exception:
            return None

    def _bucket(self, is_class10: bool) -> GridFSBucket:
        return self._bucket10 if is_class10 else self._bucket9

    def _files_col(self, is_class10: bool) -> Collection:
        return self.db_client.get_collection("uploads.files", is_class10=is_class10)

    def save_file(
        self,
        data: bytes,
        filename: str,
        user_id: str,
        is_class10: bool,
        content_type: Optional[str] = None,
        file_kind: str = "original",
        parent_file_id: Optional[str] = None,
    ) -> str:
        metadata = {
            "user_id": user_id,
            "content_type": content_type or "application/octet-stream",
            "file_kind": file_kind,
        }
        if parent_file_id:
            metadata["parent_file_id"] = str(parent_file_id)
        with self._bucket(is_class10).open_upload_stream(filename, metadata=metadata) as stream:
            stream.write(data)
            return str(stream._id)

    def get_file(self, file_id: str, is_class10: bool) -> Optional[Dict[str, Any]]:
        oid = self._parse_object_id(file_id)
        if oid is None:
            return None
        file_doc = self._files_col(is_class10).find_one({"_id": oid})
        if not file_doc:
            return None
        stream = self._bucket(is_class10).open_download_stream(oid)
        try:
            data = stream.read()
        finally:
            stream.close()
        metadata = file_doc.get("metadata", {}) or {}
        return {
            "id": str(file_doc["_id"]),
            "filename": file_doc.get("filename") or "",
            "length": int(file_doc.get("length", 0)),
            "upload_date": file_doc.get("uploadDate"),
            "user_id": metadata.get("user_id"),
            "content_type": metadata.get("content_type"),
            "file_kind": metadata.get("file_kind", "original"),
            "parent_file_id": metadata.get("parent_file_id"),
            "data": data,
        }

    def delete_file(self, file_id: str, is_class10: bool, delete_children: bool = True) -> bool:
        oid = self._parse_object_id(file_id)
        if oid is None:
            return False
        files_col = self._files_col(is_class10)
        file_doc = files_col.find_one({"_id": oid})
        if not file_doc:
            return False
        if delete_children:
            child_docs = files_col.find({"metadata.parent_file_id": str(oid)})
            for child in child_docs:
                try:
                    self._bucket(is_class10).delete(child["_id"])
                except Exception:
                    continue
        self._bucket(is_class10).delete(oid)
        return True

    def enforce_user_bytes_cap(
        self,
        user_id: str,
        is_class10: bool,
        bytes_limit: int,
        window_hours: int = 24,
    ) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        files_col = self._files_col(is_class10)
        docs = list(
            files_col.find(
                {"metadata.user_id": user_id, "uploadDate": {"$gte": cutoff}},
                {"_id": 1, "length": 1},
            ).sort("uploadDate", ASCENDING)
        )
        total_bytes = sum(int(doc.get("length", 0)) for doc in docs)
        while total_bytes > bytes_limit and docs:
            oldest = docs.pop(0)
            removed = self.delete_file(str(oldest.get("_id")), is_class10, delete_children=False)
            if removed:
                total_bytes -= int(oldest.get("length", 0))


class QuestionReportRepository:
    """Persists question reports in Mongo instead of local JSON files."""

    def __init__(self, db_client: DatabaseClient) -> None:
        self.db_client = db_client
        for std in (9, 10):
            col = db_client.get_collection("QuestionReports", standard=std)
            col.create_index(
                [("user_id", ASCENDING), ("exam_id", ASCENDING), ("question_index", ASCENDING)],
                unique=True,
            )
            col.create_index([("timestamp", DESCENDING)])

    def _col(self, is_class10: bool) -> Collection:
        return self.db_client.get_collection("QuestionReports", is_class10=is_class10)

    def create_report_if_absent(self, report: Dict[str, Any], is_class10: bool) -> bool:
        result = self._col(is_class10).update_one(
            {
                "user_id": report["user_id"],
                "exam_id": report["exam_id"],
                "question_index": report["question_index"],
            },
            {"$setOnInsert": report},
            upsert=True,
        )
        return result.upserted_id is not None


# -----------------------------------------------------------------------------
# Static Content Repository (JSON content migrated to Mongo)
# -----------------------------------------------------------------------------

class StaticContentRepository:
    """
    Stores static JSON content in Mongo so runtime does not depend on local files.
    Content is stored in class-9 DB as a single shared source.
    """

    _KNOWN_ALIASES = {
        "students.json": "students.class9",
        "class10_students.json": "students.class10",
        "teachers.json": "teachers",
        "update.json": "updates",
        "lessons.json": "lessons.class9",
        "lessons10.json": "lessons.class10",
    }

    def __init__(self, db_client: DatabaseClient) -> None:
        self.db_client = db_client
        self._col = db_client.get_collection("StaticContent", standard=9)
        self._col.create_index([("kind", ASCENDING), ("rel_path", ASCENDING)])
        self._col.create_index([("alias", ASCENDING)])
        self._col.create_index([("standard", ASCENDING), ("subject", ASCENDING)])

    @staticmethod
    def _normalize_rel_path(path: str) -> str:
        normalized = str(path or "").replace("\\", "/").strip()
        normalized = normalized.lstrip("./")
        if normalized.startswith("backend/data/"):
            normalized = normalized[len("backend/data/"):]
        if normalized.startswith("data/"):
            normalized = normalized[len("data/"):]
        if normalized.startswith("mongo://"):
            normalized = normalized[len("mongo://"):]
        if normalized.startswith("json:"):
            normalized = normalized[len("json:"):]
        return normalized

    def upsert_json(
        self,
        rel_path: str,
        content: Any,
        standard: Optional[int] = None,
        subject: Optional[str] = None,
        alias: Optional[str] = None,
    ) -> None:
        rel = self._normalize_rel_path(rel_path)
        doc_id = f"json:{rel}"
        update_set: Dict[str, Any] = {
            "kind": "json_file",
            "rel_path": rel,
            "content": content,
            "updated_at": datetime.now(timezone.utc),
        }
        if standard is not None:
            update_set["standard"] = int(standard)
        if subject:
            update_set["subject"] = subject
        if alias:
            update_set["alias"] = alias
        self._col.update_one({"_id": doc_id}, {"$set": update_set}, upsert=True)

    def upsert_alias(self, alias: str, content: Any) -> None:
        doc_id = f"alias:{alias}"
        self._col.update_one(
            {"_id": doc_id},
            {
                "$set": {
                    "kind": "alias",
                    "alias": alias,
                    "content": content,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    def get_alias(self, alias: str) -> Optional[Any]:
        doc = self._col.find_one({"_id": f"alias:{alias}"}, {"_id": 0, "content": 1})
        if not doc:
            return None
        return doc.get("content")

    def get_json(self, rel_path_or_name: str) -> Optional[Any]:
        rel = self._normalize_rel_path(rel_path_or_name)
        if not rel:
            return None

        alias_key = self._KNOWN_ALIASES.get(rel.lower())
        if alias_key:
            alias_doc = self.get_alias(alias_key)
            if alias_doc is not None:
                return alias_doc

        doc = self._col.find_one({"_id": f"json:{rel}"}, {"_id": 0, "content": 1})
        if doc:
            return doc.get("content")

        # Try lowercase Update alias fallback.
        if rel == "Update.json":
            alias_doc = self.get_alias("updates")
            if alias_doc is not None:
                return alias_doc
        return None

    def has_data(self) -> bool:
        return self._col.estimated_document_count() > 0


# -----------------------------------------------------------------------------
# User Repository (user-centric schema, segregated by class DB)
# -----------------------------------------------------------------------------

class UserRepository:
    def __init__(self, db_client: DatabaseClient, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.write_queue = write_queue

        # Ensure indexes exist on both DBs
        for std in (9, 10):
            col = db_client.get_collection("Users", standard=std)
            col.create_index([("id", ASCENDING)], unique=True)
            col.create_index([("standard", ASCENDING), ("division", ASCENDING)])
            col.create_index([("teacher", ASCENDING)])

    def _col_for_user(self, user_id: str, is_class10: Optional[bool]) -> Tuple[Collection, bool]:
        """Resolve collection for user. If class unknown, probe 9 then 10. Returns (collection, is_class10)."""
        if is_class10 is not None:
            return self.db_client.get_collection("Users", is_class10=is_class10), is_class10

        col9 = self.db_client.get_collection("Users", is_class10=False)
        if col9.find_one({"id": user_id}, {"_id": 1}):
            return col9, False

        col10 = self.db_client.get_collection("Users", is_class10=True)
        if col10.find_one({"id": user_id}, {"_id": 1}):
            return col10, True

        # Default to class 9 if unknown (caller may insert).
        return col9, False

    def get_user(self, user_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        if is_class10 is not None:
            col = self.db_client.get_collection("Users", is_class10=is_class10)
            doc = col.find_one({"id": user_id})
            if doc:
                return doc
            other_col = self.db_client.get_collection("Users", is_class10=not is_class10)
            return other_col.find_one({"id": user_id})

        col9 = self.db_client.get_collection("Users", is_class10=False)
        doc = col9.find_one({"id": user_id})
        if doc:
            return doc

        col10 = self.db_client.get_collection("Users", is_class10=True)
        return col10.find_one({"id": user_id})

    def create_user(
        self,
        user_id: str,
        password: Optional[str],
        name: str,
        roll_no: int,
        division: str,
        standard: int,
        teacher: bool = False,
    ) -> Dict[str, Any]:
        subjects = ["Math", "SS", "English", "Science"]
        subject_stats = [
            {
                "subject": subj,
                "attempted": 0,
                "avgPercentage": 0.0,
                "marksGained": 0,
                "marksAttempted": 0,
                "highestMark": 0.0,
                "lowestMark": 0.0,
            }
            for subj in subjects
        ]
        user_doc = {
            "id": user_id,
            "name": name,
            "password": password,
            "rollno": roll_no,
            "division": division,
            "standard": int(standard),
            "teacher": teacher,
            "coins": 0,
            "tasks": {"generated_at": None, "tasks_list": []},
            "stats": {"attempted": 0, "correct": 0, "questions": 0, "avgPercentage": 0.0},
            "subjects": subject_stats,
            "examHistory": [],
        }

        col = self.db_client.get_collection("Users", standard=standard)
        col.update_one({"id": user_id}, {"$setOnInsert": user_doc}, upsert=True)
        return user_doc

    def set_password(self, user_id: str, new_password: str, is_class10: Optional[bool] = None) -> bool:
        col, _ = self._col_for_user(user_id, is_class10)
        result = col.update_one({"id": user_id}, {"$set": {"password": new_password}})
        return result.matched_count > 0

    def update_tasks(self, user_id: str, tasks: Dict[str, Any], is_class10: Optional[bool] = None, coins: Optional[int] = None) -> None:
        col, _ = self._col_for_user(user_id, is_class10)
        update_set = {"tasks": tasks}
        if coins is not None:
            update_set["coins"] = coins
        col.update_one({"id": user_id}, {"$set": update_set})

    def get_user_stats(self, user_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        user = self.get_user(user_id, is_class10)
        if not user:
            return None
        return user.get("stats", None)

    def get_all_user_subject_stats(self, user_id: str, is_class10: Optional[bool] = None) -> List[Dict[str, Any]]:
        user = self.get_user(user_id, is_class10)
        if not user:
            return []
        subjects = user.get("subjects", []) or []
        for s in subjects:
            s.pop("_id", None)
        return subjects

    def get_user_subject_stats(self, user_id: str, subject: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        subjects = self.get_all_user_subject_stats(user_id, is_class10)
        for s in subjects:
            if s.get("subject", "").lower() == subject.lower():
                return s
        return None

    def add_exam_history(self, user_id: str, overview: Dict[str, Any], is_class10: Optional[bool] = None) -> None:
        col, _ = self._col_for_user(user_id, is_class10)
        col.update_one({"id": user_id}, {"$push": {"examHistory": overview}})

    def update_stats_after_exam(
        self,
        user_id: str,
        subject: str,
        score: int,
        total_questions: int,
        percentage: float,
        exam_id: str,
        lessons: List[str],
        test: bool = False,
        test_name: Optional[str] = None,
        is_class10: Optional[bool] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        user = self.get_user(user_id, is_class10)
        if not user:
            raise ValueError(f"User {user_id} not found")

        overall = user.get("stats", {"attempted": 0, "correct": 0, "questions": 0, "avgPercentage": 0.0})
        attempted = int(overall.get("attempted", 0)) + 1
        correct = int(overall.get("correct", 0)) + score
        questions = int(overall.get("questions", 0)) + total_questions
        avg_percentage = (correct / questions * 100.0) if questions > 0 else 0.0
        overall.update(
            {
                "attempted": attempted,
                "correct": correct,
                "questions": questions,
                "avgPercentage": round(avg_percentage, 2),
            }
        )

        subjects = user.get("subjects", [])
        subj = None
        for s in subjects:
            if s.get("subject") == subject:
                subj = s
                break
        if not subj:
            subj = {
                "subject": subject,
                "attempted": 0,
                "avgPercentage": 0.0,
                "marksGained": 0,
                "marksAttempted": 0,
                "highestMark": 0.0,
                "lowestMark": 0.0,
            }
            subjects.append(subj)

        subj_attempted = int(subj.get("attempted", 0)) + 1
        subj_marks_gained = int(subj.get("marksGained", 0)) + score
        subj_marks_attempted = int(subj.get("marksAttempted", 0)) + total_questions
        subj_avg = (subj_marks_gained / subj_marks_attempted * 100.0) if subj_marks_attempted > 0 else 0.0
        subj_high = max(float(subj.get("highestMark", 0.0)), float(percentage))
        prev_low = float(subj.get("lowestMark", 0.0))
        subj_low = (
            float(percentage)
            if prev_low == 0.0 and subj_attempted == 1
            else (min(prev_low, float(percentage)) if prev_low > 0 else float(percentage))
        )
        subj.update(
            {
                "attempted": subj_attempted,
                "avgPercentage": round(subj_avg, 2),
                "marksGained": subj_marks_gained,
                "marksAttempted": subj_marks_attempted,
                "highestMark": round(subj_high, 2),
                "lowestMark": round(subj_low, 2),
            }
        )

        overview_stats = {
            "exam-id": exam_id,
            "subject": subject,
            "score": score,
            "totalQuestions": total_questions,
            "percentage": percentage,
            "lessons": lessons or [],
            "date": datetime.now(IST).strftime("%d-%m-%Y"),
            "test": bool(test),
        }
        if test and test_name:
            overview_stats["test_name"] = test_name

        col, _ = self._col_for_user(user_id, is_class10)
        col.update_one(
            {"id": user_id},
            {"$set": {"stats": overall, "subjects": subjects}, "$push": {"examHistory": overview_stats}},
        )
        return overall, subj

    def get_user_exams_overview(self, user_id: str, is_class10: Optional[bool] = None) -> List[Dict[str, Any]]:
        user = self.get_user(user_id, is_class10)
        if not user:
            return []
        return user.get("examHistory", []) or []

    def get_question_history(self, user_id: str, is_class10: Optional[bool] = None) -> List[str]:
        user = self.get_user(user_id, is_class10)
        if not user:
            return []
        history = user.get("questionHistory", [])
        return history if isinstance(history, list) else []

    def set_question_history(self, user_id: str, history: List[str], is_class10: Optional[bool] = None) -> None:
        col, _ = self._col_for_user(user_id, is_class10)
        col.update_one({"id": user_id}, {"$set": {"questionHistory": history}})

    def get_all_students_by_standard(self, standard: int) -> List[Dict[str, Any]]:
        col = self.db_client.get_collection("Users", standard=standard)
        students = list(col.find({"teacher": {"$ne": True}}))
        result = []
        for s in students:
            s.pop("_id", None)
            result.append(
                {"id": s.get("id"), "name": s.get("name"), "division": s.get("division"), "roll": s.get("rollno")}
            )
        return result


# -----------------------------------------------------------------------------
# Exam Repository (segregated by class DB)
# -----------------------------------------------------------------------------

class ExamRepository:
    def __init__(self, db_client: DatabaseClient, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.write_queue = write_queue

        # Ensure indexes on both DBs
        for std in (9, 10):
            col = db_client.get_collection("Exams", standard=std)
            col.create_index([("exam-id", ASCENDING)], unique=True)
            col.create_index([("userId", ASCENDING), ("is_submitted", ASCENDING)])
            col.create_index([("submission_timestamp", DESCENDING)])

    def _col_by_params(self, is_class10: Optional[bool] = None, standard: Optional[int] = None) -> Collection:
        return self.db_client.get_collection("Exams", is_class10=is_class10, standard=standard)

    def add_exam(self, exam_data: Dict[str, Any], is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        std = exam_data.get("standard")
        col = self._col_by_params(is_class10=is_class10, standard=std)
        col.insert_one(exam_data)
        return exam_data

    def get_exam(self, exam_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        if is_class10 is None:
            # Probe DB 9 then 10
            col9 = self._col_by_params(is_class10=False)
            doc = col9.find_one({"exam-id": exam_id})
            if doc:
                return doc
            col10 = self._col_by_params(is_class10=True)
            return col10.find_one({"exam-id": exam_id})

        col = self._col_by_params(is_class10=is_class10)
        return col.find_one({"exam-id": exam_id})

    def update_exam(self, exam_id: str, updated_data: Dict[str, Any], is_class10: Optional[bool] = None) -> bool:
        exam = self.get_exam(exam_id, is_class10)
        if not exam:
            return False
        col = self._col_by_params(standard=int(exam.get("standard", 9)))
        result = col.update_one({"exam-id": exam_id}, {"$set": updated_data})
        return result.matched_count > 0

    def update_exam_solution(self, exam_id: str, question_index: int, solution: str, is_class10: Optional[bool] = None) -> bool:
        exam = self.get_exam(exam_id, is_class10)
        if not exam:
            return False

        col = self._col_by_params(standard=int(exam.get("standard", 9)))
        update_field = f"results.{question_index}.solution"
        result = col.update_one({"exam-id": exam_id}, {"$set": {update_field: solution}})
        return result.matched_count > 0

    def delete_exam(self, exam_id: str, is_class10: Optional[bool] = None) -> bool:
        if is_class10 is not None:
            col = self._col_by_params(is_class10=is_class10)
            return col.delete_one({"exam-id": exam_id}).deleted_count > 0

        col9 = self._col_by_params(is_class10=False)
        deleted9 = col9.delete_one({"exam-id": exam_id}).deleted_count
        if deleted9 > 0:
            return True
        col10 = self._col_by_params(is_class10=True)
        return col10.delete_one({"exam-id": exam_id}).deleted_count > 0


# -----------------------------------------------------------------------------
# Test Repository (segregated by class DB)
# -----------------------------------------------------------------------------

class TestRepository:
    def __init__(self, db_client: DatabaseClient, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.write_queue = write_queue

        for std in (9, 10):
            col = db_client.get_collection("Tests", standard=std)
            col.create_index([("test-id", ASCENDING)], unique=True)
            col.create_index([("standard", ASCENDING)])
            col.create_index([("expiration_date", ASCENDING)])
            inactive = db_client.get_collection("InactiveTests", standard=std)
            inactive.create_index([("test-id", ASCENDING)], unique=True)

    def add_test(self, test_data: Dict[str, Any], is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        std = test_data.get("standard")
        col = self.db_client.get_collection("Tests", is_class10=is_class10, standard=std)
        col.insert_one(test_data)
        return test_data

    def get_test(self, test_id: str, is_class10: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        if is_class10 is None:
            col9 = self.db_client.get_collection("Tests", is_class10=False)
            doc = col9.find_one({"test-id": test_id})
            if doc:
                return doc
            col10 = self.db_client.get_collection("Tests", is_class10=True)
            return col10.find_one({"test-id": test_id})

        col = self.db_client.get_collection("Tests", is_class10=is_class10)
        return col.find_one({"test-id": test_id})

    def get_all_tests(self, is_class10: Optional[bool] = None) -> List[Dict[str, Any]]:
        if is_class10 is None:
            tests: List[Dict[str, Any]] = []
            for flag in (False, True):
                col = self.db_client.get_collection("Tests", is_class10=flag)
                docs = list(col.find({}))
                for d in docs:
                    d.pop("_id", None)
                tests.extend(docs)
            return tests
        col = self.db_client.get_collection("Tests", is_class10=is_class10)
        docs = list(col.find({}))
        for d in docs:
            d.pop("_id", None)
        return docs

    def get_all_tests_by_standard(self, standard: int) -> List[Dict[str, Any]]:
        col = self.db_client.get_collection("Tests", standard=standard)
        docs = list(col.find({"standard": int(standard)}))
        for d in docs:
            d.pop("_id", None)
        return docs

    def update_test(self, test_id: str, updated_data: Dict[str, Any], is_class10: Optional[bool] = None) -> bool:
        test = self.get_test(test_id, is_class10)
        if not test:
            return False
        col = self.db_client.get_collection("Tests", standard=int(test.get("standard", 9)))
        result = col.update_one({"test-id": test_id}, {"$set": updated_data})
        return result.matched_count > 0

    def delete_test(self, test_id: str, is_class10: Optional[bool] = None) -> bool:
        test = self.get_test(test_id, is_class10)
        if not test:
            return False
        col = self.db_client.get_collection("Tests", standard=int(test.get("standard", 9)))
        return col.delete_one({"test-id": test_id}).deleted_count > 0

    def move_expired_tests_to_inactive(self) -> int:
        """Move expired tests to InactiveTests for both classes."""
        from datetime import timezone as dt_tz
        now = datetime.now(dt_tz.utc)
        total_moved = 0
        try:
            for is_class10 in (False, True):
                tests_col = self.db_client.get_collection("Tests", is_class10=is_class10)
                inactive_col = self.db_client.get_collection("InactiveTests", is_class10=is_class10)
                docs = list(tests_col.find({}))
                for test in docs:
                    exp = test.get("expiration_date")
                    if not exp:
                        continue
                    try:
                        iso = exp.replace("Z", "+00:00")
                        exp_dt = datetime.fromisoformat(iso)
                    except Exception:
                        continue
                    if exp_dt < now:
                        test_copy = dict(test)
                        test_copy.pop("_id", None)
                        inactive_col.update_one(
                            {"test-id": test_copy["test-id"]},
                            {"$setOnInsert": test_copy},
                            upsert=True,
                        )
                        deleted = tests_col.delete_one({"test-id": test_copy["test-id"]})
                        if deleted.deleted_count > 0:
                            total_moved += 1
        except Exception as e:
            print(f"Error during moving expired tests: {e}")
        return total_moved


# -----------------------------------------------------------------------------
# Leaderboard Service (segregated per class DB)
# -----------------------------------------------------------------------------

class LeaderboardService:
    def __init__(self, db_client: DatabaseClient, user_repo: UserRepository, write_queue: WriteQueue) -> None:
        self.db_client = db_client
        self.user_repo = user_repo
        self.write_queue = write_queue
        # Index on both DBs
        for std in (9, 10):
            col = db_client.get_collection("LeaderboardMonthly", standard=std)
            # _id index exists by default and is unique; no need to create it manually.

    @staticmethod
    def calculate_elo_change(score_percentage: float, num_lessons: int, subject: str) -> int:
        base_multiplier = 32
        subject_weights = {
            "Mathematics": 1.5,
            "Science": 1.2,
            "Social Studies": 1.0,
            "Math": 1.5,
            "SS": 1.0,
        }
        subject_weight = subject_weights.get(subject, 1.0)
        lesson_multiplier = 1 + (num_lessons * 0.1)
        performance_multiplier = (score_percentage / 100.0)
        elo_change = base_multiplier * subject_weight * lesson_multiplier * performance_multiplier
        return round(elo_change)

    def _entry_from_user_for_month(self, u: Dict[str, Any], month_key: str) -> Optional[Dict[str, Any]]:
        user_id = u.get("id")
        if not user_id:
            return None
        name = u.get("name", "UNKNOWN")
        division = u.get("division", "N/A")
        coins = u.get("coins", 0)
        exam_history = u.get("examHistory", []) or []
        total_exams = 0
        total_score = 0
        total_questions = 0
        elo_score = 0
        for e in exam_history:
            if month_key_from_date_str(e.get("date", "")) != month_key:
                continue
            total_exams += 1
            score = int(e.get("score", 0))
            tq = int(e.get("totalQuestions", 0))
            total_score += score
            total_questions += tq
            pct = float(e.get("percentage", 0.0))
            subj = e.get("subject", "")
            lessons = e.get("lessons", []) or []
            elo_score += self.calculate_elo_change(pct, len(lessons), subj)
        has_taken_exam = total_exams > 0
        name_parts = (name or "").split()
        if len(name_parts) >= 2:
            display_name = f"{name_parts[0].upper()} {name_parts[-1].upper()}"
        elif len(name_parts) == 1:
            display_name = name_parts[0].upper()
        else:
            display_name = "UNKNOWN"
        return {
            "userId": user_id,
            "name": display_name,
            "division": division,
            "total_exams": total_exams,
            "coins": coins,
            "elo_score": elo_score,
            "has_taken_exam": has_taken_exam,
            "total_score": total_score,
            "total_questions": total_questions,
            "average_percentage": (total_score / total_questions * 100.0) if total_questions > 0 else 0.0,
        }

    def _col(self, standard: int) -> Collection:
        return self.db_client.get_collection("LeaderboardMonthly", standard=standard)

    def _build_snapshot_for_month(self, standard: int, month_key: str) -> Dict[str, Any]:
        users_col = self.db_client.get_collection("Users", standard=standard)
        teachers = set(u["id"] for u in users_col.find({"teacher": True}, {"id": 1}))
        users = list(users_col.find({}, {"_id": 0}))
        entries: List[Dict[str, Any]] = []
        for u in users:
            user_id = u.get("id")
            if not user_id or user_id in teachers:
                continue
            entry = self._entry_from_user_for_month(u, month_key)
            if entry:
                entries.append(entry)

        entries.sort(
            key=lambda x: (x.get("has_taken_exam", False), x.get("elo_score", 0), x.get("coins", 0)),
            reverse=True,
        )
        version = hashlib.sha256(f"{month_key}-{datetime.now().timestamp()}".encode()).hexdigest()[:8]
        doc_id = f"{month_key}-{standard}"
        snapshot = {
            "_id": doc_id,
            "version": version,
            "month": month_key,
            "standard": standard,
            "entries": entries,
        }
        self._col(standard).replace_one({"_id": doc_id}, snapshot, upsert=True)
        return snapshot

    def get_or_build_monthly(
        self,
        standard: int,
        month_key: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        mk = month_key or current_month_key()
        doc_id = f"{mk}-{standard}"
        doc = self._col(standard).find_one({"_id": doc_id})
        if not doc:
            doc = self._build_snapshot_for_month(standard, mk)
        entries = doc.get("entries", [])
        total_count = len(entries)
        start_idx = max(0, (page - 1) * page_size)
        end_idx = min(total_count, start_idx + page_size)
        paged = entries[start_idx:end_idx]
        for i, entry in enumerate(paged, 1):
            entry["rank"] = start_idx + i
        return {
            "version": doc.get("version"),
            "month": mk,
            "standard": standard,
            "total_count": total_count,
            "entries": paged,
        }

    def preload_current_month_leaderboard(self):
        """Builds the leaderboard for the current month for both standards if it doesn't exist."""
        print("Pre-loading current month leaderboard...")
        month_key = current_month_key()
        for std in (9, 10):
            try:
                # Check if it exists first to avoid unnecessary rebuilds
                doc_id = f"{month_key}-{std}"
                doc = self._col(std).find_one({"_id": doc_id}, {"_id": 1})
                if not doc:
                    self._build_snapshot_for_month(std, month_key)
            except Exception as e:
                print(f"Error pre-loading leaderboard for standard {std}: {e}")
        print("Finished pre-loading leaderboard.")

    def update_on_submission(self, user_id: str, standard: int, month_key: Optional[str] = None) -> None:
        """Recompute a single user's leaderboard entry for the month and upsert into snapshot."""
        mk = month_key or current_month_key()
        doc_id = f"{mk}-{standard}"

        def _op():
            col = self._col(standard)
            doc = col.find_one({"_id": doc_id})
            if not doc:
                doc = self._build_snapshot_for_month(standard, mk)
            user = self.db_client.get_collection("Users", standard=standard).find_one({"id": user_id})
            if not user or user.get("teacher"):
                return
            updated_entry = self._entry_from_user_for_month(user, mk)
            if updated_entry is None:
                return
            entries = doc.get("entries", [])
            replaced = False
            for idx, e in enumerate(entries):
                if e.get("userId") == user_id:
                    entries[idx] = updated_entry
                    replaced = True
                    break
            if not replaced:
                entries.append(updated_entry)
            entries.sort(
                key=lambda x: (x.get("has_taken_exam", False), x.get("elo_score", 0), x.get("coins", 0)),
                reverse=True,
            )
            version = doc.get("version") or hashlib.sha256(f"{mk}-{datetime.now().timestamp()}".encode()).hexdigest()[:8]
            col.update_one(
                {"_id": doc_id},
                {"$set": {"entries": entries, "version": version, "month": mk, "standard": standard}},
                upsert=True,
            )
        _op()


# -----------------------------------------------------------------------------
# Lazy app-level instances for better serverless cold start
# -----------------------------------------------------------------------------

@dataclass
class _RepositoryContainer:
    db_client: DatabaseClient
    write_queue: WriteQueue
    user_repo: UserRepository
    exam_repo: ExamRepository
    test_repo: TestRepository
    leaderboard_service: LeaderboardService
    upload_repo: UploadRepository
    question_report_repo: QuestionReportRepository
    static_content_repo: StaticContentRepository


_container_lock = threading.Lock()
_container: Optional[_RepositoryContainer] = None


def _build_container() -> _RepositoryContainer:
    db_client = DatabaseClient()
    write_queue = WriteQueue(db_client, worker_count=1)
    user = UserRepository(db_client, write_queue)
    exam = ExamRepository(db_client, write_queue)
    test = TestRepository(db_client, write_queue)
    leaderboard = LeaderboardService(db_client, user, write_queue)
    uploads = UploadRepository(db_client)
    reports = QuestionReportRepository(db_client)
    static_content = StaticContentRepository(db_client)
    return _RepositoryContainer(
        db_client=db_client,
        write_queue=write_queue,
        user_repo=user,
        exam_repo=exam,
        test_repo=test,
        leaderboard_service=leaderboard,
        upload_repo=uploads,
        question_report_repo=reports,
        static_content_repo=static_content,
    )


def _get_container() -> _RepositoryContainer:
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = _build_container()
    return _container


class _LazyProxy:
    def __init__(self, key: str) -> None:
        self._key = key

    def _target(self):
        return getattr(_get_container(), self._key)

    def __getattr__(self, item):
        return getattr(self._target(), item)

    def __repr__(self) -> str:
        return f"<LazyProxy {self._key}>"


user_repo = _LazyProxy("user_repo")
exam_repo = _LazyProxy("exam_repo")
test_repo = _LazyProxy("test_repo")
leaderboard_service = _LazyProxy("leaderboard_service")
upload_repo = _LazyProxy("upload_repo")
question_report_repo = _LazyProxy("question_report_repo")
static_content_repo = _LazyProxy("static_content_repo")


def preload_caches():
    """Startup hook retained for compatibility; no RAM caches are used."""
    print("----- Pre-loading startup data -----")
    try:
        _get_container().leaderboard_service.preload_current_month_leaderboard()
    except Exception as e:
        print(f"Error during startup pre-loading: {e}")
    print("----- Startup pre-loading finished -----")


__all__ = [
    "DatabaseClient",
    "WriteQueue",
    "UserRepository",
    "ExamRepository",
    "TestRepository",
    "LeaderboardService",
    "user_repo",
    "exam_repo",
    "test_repo",
    "leaderboard_service",
    "upload_repo",
    "question_report_repo",
    "static_content_repo",
    "convert_objectid_to_str",
    "preload_caches",
]
