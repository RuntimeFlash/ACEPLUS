from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo.collection import Collection

from .base import DatabaseClient, WriteQueue, current_month_key, month_key_from_date_str
from .user_repository import UserRepository

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

