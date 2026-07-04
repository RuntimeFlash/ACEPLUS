import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from db import convert_objectid_to_str, replay_repo


class ReplayService:
    _INTERVAL_DAYS: List[int] = [1, 3, 7, 14, 30]

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _normalize_option(option: Any) -> str:
        if option is None:
            return ""
        return str(option).strip().lower()

    @staticmethod
    def _build_mistake_key(subject: str, question_text: str, correct_option: str) -> str:
        raw = f"{subject.strip().lower()}|{question_text.strip().lower()}|{correct_option}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_replay_id(user_id: str, mistake_key: str) -> str:
        raw = f"{user_id}:{mistake_key}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]

    def ingest_exam_mistakes(
        self,
        exam_id: str,
        user_id: str,
        is_class10: bool,
        subject: str,
        lessons: List[str],
        questions: List[Dict[str, Any]],
        selected_answers: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        now_utc = self._utc_now()
        standard = 10 if is_class10 else 9
        saved_count = 0

        for index, question in enumerate(questions):
            answer_payload = selected_answers[index] if index < len(selected_answers) else {}
            selected_option = self._normalize_option(answer_payload.get("option"))
            correct_option = self._normalize_option(question.get("answer"))
            if not selected_option or not correct_option:
                continue
            if selected_option == correct_option:
                continue

            question_text = str(question.get("question", "")).strip()
            if not question_text:
                continue

            options = question.get("options", {})
            if not isinstance(options, dict):
                options = {}

            mistake_key = self._build_mistake_key(subject, question_text, correct_option)
            replay_id = self._build_replay_id(user_id, mistake_key)
            card_data = {
                "replay_id": replay_id,
                "mistake_key": mistake_key,
                "userId": user_id,
                "standard": standard,
                "is_active": True,
                "subject": subject,
                "lessons": lessons or [],
                "question": question_text,
                "options": {str(k).lower(): str(v) for k, v in options.items()},
                "correct_option": correct_option,
                "source_exam_id": exam_id,
                "source_question_index": index,
                "last_selected_option": selected_option,
                "review_step": 0,
                "interval_days": 0,
                "consecutive_correct": 0,
                "total_reviews": 0,
                "correct_reviews": 0,
                "wrong_reviews": 0,
                "last_reviewed_at": None,
                "last_reviewed_at_dt": None,
                "due_at": now_utc.isoformat(),
                "due_at_dt": now_utc,
                "updated_at": now_utc.isoformat(),
                "updated_at_dt": now_utc,
                "created_at_dt": now_utc,
            }
            if replay_repo.upsert_card(card_data, is_class10=is_class10):
                saved_count += 1

        return {"saved": saved_count}

    def get_due_cards(
        self,
        user_id: str,
        is_class10: bool,
        limit: int = 20,
    ) -> Dict[str, Any]:
        now_utc = self._utc_now()
        due_docs = replay_repo.get_due_cards(
            user_id=user_id,
            is_class10=is_class10,
            now_utc=now_utc,
            limit=limit,
        )
        next_doc = replay_repo.get_next_card(user_id=user_id, is_class10=is_class10)

        cards: List[Dict[str, Any]] = []
        for doc in due_docs:
            cards.append(
                {
                    "replay_id": doc.get("replay_id"),
                    "subject": doc.get("subject"),
                    "lessons": doc.get("lessons", []),
                    "question": doc.get("question"),
                    "options": doc.get("options", {}),
                    "due_at": doc.get("due_at"),
                    "interval_days": int(doc.get("interval_days", 0)),
                    "review_step": int(doc.get("review_step", 0)),
                    "consecutive_correct": int(doc.get("consecutive_correct", 0)),
                    "total_reviews": int(doc.get("total_reviews", 0)),
                }
            )

        next_due_at = None
        if next_doc:
            next_due_at = next_doc.get("due_at")

        payload = {
            "cards": cards,
            "due_count": len(cards),
            "next_due_at": next_due_at,
            "server_time": now_utc.isoformat(),
        }
        return convert_objectid_to_str(payload)

    def review_card(
        self,
        replay_id: str,
        user_id: str,
        is_class10: bool,
        selected_option: str,
    ) -> Dict[str, Any]:
        card = replay_repo.get_card_by_replay_id(
            replay_id=replay_id,
            user_id=user_id,
            is_class10=is_class10,
        )
        if not card:
            return {"ok": False, "status_code": 404, "message": "Replay card not found"}

        selected_option_normalized = self._normalize_option(selected_option)
        if selected_option_normalized not in {"a", "b", "c", "d"}:
            return {"ok": False, "status_code": 400, "message": "Invalid selected option"}

        now_utc = self._utc_now()
        correct_option = self._normalize_option(card.get("correct_option"))
        is_correct = selected_option_normalized == correct_option

        previous_step = int(card.get("review_step", 0))
        previous_consecutive = int(card.get("consecutive_correct", 0))
        total_reviews = int(card.get("total_reviews", 0)) + 1
        correct_reviews = int(card.get("correct_reviews", 0))
        wrong_reviews = int(card.get("wrong_reviews", 0))

        if is_correct:
            next_consecutive = previous_consecutive + 1
            next_step = min(previous_step + 1, len(self._INTERVAL_DAYS))
            interval_days = self._INTERVAL_DAYS[next_step - 1]
            correct_reviews += 1
        else:
            next_consecutive = 0
            next_step = 0
            interval_days = 1
            wrong_reviews += 1

        due_at_dt = now_utc + timedelta(days=interval_days)
        update_data = {
            "review_step": next_step,
            "interval_days": interval_days,
            "consecutive_correct": next_consecutive,
            "total_reviews": total_reviews,
            "correct_reviews": correct_reviews,
            "wrong_reviews": wrong_reviews,
            "last_selected_option": selected_option_normalized,
            "last_reviewed_at": now_utc.isoformat(),
            "last_reviewed_at_dt": now_utc,
            "due_at": due_at_dt.isoformat(),
            "due_at_dt": due_at_dt,
            "updated_at": now_utc.isoformat(),
            "updated_at_dt": now_utc,
        }
        updated = replay_repo.update_card(
            replay_id=replay_id,
            user_id=user_id,
            is_class10=is_class10,
            update_data=update_data,
        )
        if not updated:
            return {"ok": False, "status_code": 500, "message": "Failed to update replay card"}

        payload = {
            "is_correct": is_correct,
            "correct_option": correct_option,
            "next_due_at": due_at_dt.isoformat(),
            "interval_days": interval_days,
            "consecutive_correct": next_consecutive,
        }
        return {"ok": True, "status_code": 200, "payload": payload}


replay_service = ReplayService()
