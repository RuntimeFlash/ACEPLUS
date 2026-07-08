from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import pytest

from services.replay_service import replay_service
from db import replay_repo


class _FakeReplayRepo:
    def __init__(self) -> None:
        self.cards: Dict[str, Dict[str, Any]] = {}
        self.upsert_fail = False
        self.update_fail = False

    def upsert_card(self, card_data: Dict[str, Any], is_class10: Optional[bool] = None) -> bool:
        if self.upsert_fail:
            return False
        replay_id = card_data["replay_id"]
        # Ensure a copy is stored to simulate database serialization
        self.cards[replay_id] = dict(card_data)
        return True

    def get_due_cards(
        self,
        user_id: str,
        is_class10: bool,
        now_utc: datetime,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        due = []
        for card in self.cards.values():
            if (
                card.get("userId") == user_id
                and card.get("is_active") is True
                # Parse due_at_dt or compare
                and card.get("due_at_dt") <= now_utc
            ):
                due.append(dict(card))
        
        # Sort by due_at_dt
        due.sort(key=lambda x: x["due_at_dt"])
        return due[:limit]

    def get_next_card(self, user_id: str, is_class10: bool) -> Optional[Dict[str, Any]]:
        active = [card for card in self.cards.values() if card.get("userId") == user_id and card.get("is_active") is True]
        if not active:
            return None
        active.sort(key=lambda x: x["due_at_dt"])
        return dict(active[0])

    def get_card_by_replay_id(self, replay_id: str, user_id: str, is_class10: bool) -> Optional[Dict[str, Any]]:
        card = self.cards.get(replay_id)
        if card and card.get("userId") == user_id and card.get("is_active") is True:
            return dict(card)
        return None

    def update_card(self, replay_id: str, user_id: str, is_class10: bool, update_data: Dict[str, Any]) -> bool:
        if self.update_fail:
            return False
        card = self.cards.get(replay_id)
        if card and card.get("userId") == user_id:
            card.update(update_data)
            return True
        return False


@pytest.fixture
def mock_replay_repo(monkeypatch):
    fake_repo = _FakeReplayRepo()
    monkeypatch.setattr(replay_repo, "upsert_card", fake_repo.upsert_card)
    monkeypatch.setattr(replay_repo, "get_due_cards", fake_repo.get_due_cards)
    monkeypatch.setattr(replay_repo, "get_next_card", fake_repo.get_next_card)
    monkeypatch.setattr(replay_repo, "get_card_by_replay_id", fake_repo.get_card_by_replay_id)
    monkeypatch.setattr(replay_repo, "update_card", fake_repo.update_card)
    return fake_repo


def test_ingest_exam_mistakes_saves_only_mistakes(mock_replay_repo) -> None:
    questions = [
        {"question": "What is 1+1?", "options": {"a": "1", "b": "2"}, "answer": "b"},
        {"question": "What is 2+2?", "options": {"a": "4", "b": "5"}, "answer": "a"},
        {"question": "What is 3+3?", "options": {"a": "6", "b": "7"}, "answer": "a"},
    ]
    # Selected answers: wrong for Q1, correct for Q2, wrong for Q3
    selected_answers = [
        {"option": "a"},  # wrong (correct is b)
        {"option": "a"},  # correct (correct is a)
        {"option": "b"},  # wrong (correct is a)
    ]

    result = replay_service.ingest_exam_mistakes(
        exam_id="exam-123",
        user_id="user-99",
        is_class10=False,
        subject="Math",
        lessons=["L1"],
        questions=questions,
        selected_answers=selected_answers,
    )

    # Should have saved 2 cards (Q1 and Q3)
    assert result["saved"] == 2
    assert len(mock_replay_repo.cards) == 2

    # Check key structure of saved cards
    for card in mock_replay_repo.cards.values():
        assert card["userId"] == "user-99"
        assert card["subject"] == "Math"
        assert card["is_active"] is True
        assert card["standard"] == 9
        assert card["consecutive_correct"] == 0
        assert card["review_step"] == 0


def test_ingest_exam_mistakes_with_empty_or_invalid_answers(mock_replay_repo) -> None:
    questions = [
        {"question": "Q1", "options": {"a": "1"}, "answer": "a"},
    ]
    # Missing/empty selected answers
    selected_answers = [
        {"option": None},
    ]

    result = replay_service.ingest_exam_mistakes(
        exam_id="exam-123",
        user_id="user-99",
        is_class10=True,
        subject="Math",
        lessons=["L1"],
        questions=questions,
        selected_answers=selected_answers,
    )

    # Should ignore card since there is no selected answer
    assert result["saved"] == 0
    assert len(mock_replay_repo.cards) == 0


def test_get_due_cards(mock_replay_repo, monkeypatch) -> None:
    # Set a fixed utc_now for replay_service to compare against
    now = datetime(2026, 2, 25, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(replay_service, "_utc_now", lambda: now)

    # Card 1: due in the past
    mock_replay_repo.upsert_card(
        {
            "replay_id": "c1",
            "userId": "user-99",
            "is_active": True,
            "subject": "Math",
            "question": "Q1",
            "due_at": (now - timedelta(hours=1)).isoformat(),
            "due_at_dt": now - timedelta(hours=1),
            "interval_days": 1,
            "review_step": 0,
            "consecutive_correct": 0,
            "total_reviews": 0,
        }
    )

    # Card 2: due in the future
    mock_replay_repo.upsert_card(
        {
            "replay_id": "c2",
            "userId": "user-99",
            "is_active": True,
            "subject": "Math",
            "question": "Q2",
            "due_at": (now + timedelta(hours=1)).isoformat(),
            "due_at_dt": now + timedelta(hours=1),
            "interval_days": 1,
            "review_step": 0,
            "consecutive_correct": 0,
            "total_reviews": 0,
        }
    )

    result = replay_service.get_due_cards(user_id="user-99", is_class10=False)

    assert result["due_count"] == 1
    assert result["cards"][0]["replay_id"] == "c1"
    # The next due card overall is c1 (even though c2 is also there, c1 is due first/next)
    assert result["next_due_at"] == (now - timedelta(hours=1)).isoformat()


def test_review_card_correct_answer(mock_replay_repo, monkeypatch) -> None:
    now = datetime(2026, 2, 25, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(replay_service, "_utc_now", lambda: now)

    mock_replay_repo.upsert_card(
        {
            "replay_id": "c1",
            "userId": "user-99",
            "is_active": True,
            "correct_option": "b",
            "review_step": 0,
            "consecutive_correct": 0,
            "total_reviews": 0,
            "correct_reviews": 0,
            "wrong_reviews": 0,
        }
    )

    # Reviewing with correct answer
    result = replay_service.review_card(
        replay_id="c1",
        user_id="user-99",
        is_class10=False,
        selected_option="b",
    )

    assert result["ok"] is True
    assert result["status_code"] == 200
    payload = result["payload"]
    assert payload["is_correct"] is True
    assert payload["consecutive_correct"] == 1
    # step 0 -> 1. _INTERVAL_DAYS[0] is 1 day.
    assert payload["interval_days"] == 1
    assert payload["next_due_at"] == (now + timedelta(days=1)).isoformat()

    # Verify state in repo
    updated_card = mock_replay_repo.cards["c1"]
    assert updated_card["review_step"] == 1
    assert updated_card["consecutive_correct"] == 1
    assert updated_card["total_reviews"] == 1
    assert updated_card["correct_reviews"] == 1


def test_review_card_incorrect_answer(mock_replay_repo, monkeypatch) -> None:
    now = datetime(2026, 2, 25, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(replay_service, "_utc_now", lambda: now)

    mock_replay_repo.upsert_card(
        {
            "replay_id": "c1",
            "userId": "user-99",
            "is_active": True,
            "correct_option": "b",
            "review_step": 3,
            "consecutive_correct": 3,
            "total_reviews": 3,
            "correct_reviews": 3,
            "wrong_reviews": 0,
        }
    )

    # Reviewing with incorrect answer
    result = replay_service.review_card(
        replay_id="c1",
        user_id="user-99",
        is_class10=False,
        selected_option="c",
    )

    assert result["ok"] is True
    assert result["status_code"] == 200
    payload = result["payload"]
    assert payload["is_correct"] is False
    assert payload["consecutive_correct"] == 0
    # On wrong answer, resets to step 0 and sets interval to 1 day
    assert payload["interval_days"] == 1

    # Verify state in repo
    updated_card = mock_replay_repo.cards["c1"]
    assert updated_card["review_step"] == 0
    assert updated_card["consecutive_correct"] == 0
    assert updated_card["total_reviews"] == 4
    assert updated_card["wrong_reviews"] == 1


def test_review_card_not_found(mock_replay_repo) -> None:
    result = replay_service.review_card(
        replay_id="missing-card",
        user_id="user-99",
        is_class10=False,
        selected_option="a",
    )
    assert result["ok"] is False
    assert result["status_code"] == 404
    assert "not found" in result["message"]


def test_review_card_invalid_option(mock_replay_repo) -> None:
    mock_replay_repo.upsert_card(
        {
            "replay_id": "c1",
            "userId": "user-99",
            "is_active": True,
            "correct_option": "b",
        }
    )

    result = replay_service.review_card(
        replay_id="c1",
        user_id="user-99",
        is_class10=False,
        selected_option="invalid-option-xyz",
    )
    assert result["ok"] is False
    assert result["status_code"] == 400
    assert "Invalid selected option" in result["message"]


def test_review_card_failed_update(mock_replay_repo) -> None:
    mock_replay_repo.upsert_card(
        {
            "replay_id": "c1",
            "userId": "user-99",
            "is_active": True,
            "correct_option": "b",
        }
    )
    mock_replay_repo.update_fail = True

    result = replay_service.review_card(
        replay_id="c1",
        user_id="user-99",
        is_class10=False,
        selected_option="b",
    )
    assert result["ok"] is False
    assert result["status_code"] == 500
    assert "Failed to update replay card" in result["message"]
