from __future__ import annotations

from datetime import date

from utils.social_utils import (
    build_default_profile,
    compute_level_from_xp,
    update_streak,
    update_weekly_progress,
    upsert_badge,
)


def test_build_default_profile_contains_expected_shape() -> None:
    user_doc = {"id": "u1", "name": "User One", "standard": 9}
    profile = build_default_profile(user_doc)

    assert profile["username"] == "u1"
    assert profile["display_name"] == "User One"
    assert profile["privacy"]["activity"] == "friends"
    assert profile["progress"]["level"] == 1
    assert profile["progress"]["xp"] == 0
    assert isinstance(profile["badges"], list)
    assert len(profile["badges"]) >= 4


def test_compute_level_from_xp() -> None:
    assert compute_level_from_xp(0) == 1
    assert compute_level_from_xp(99) == 1
    assert compute_level_from_xp(100) == 2
    assert compute_level_from_xp(350) == 4


def test_update_streak_increments_and_resets() -> None:
    day1 = update_streak({"current": 0, "best": 0, "last_active_date": None}, active_date=date(2026, 2, 25))
    assert day1["current"] == 1
    assert day1["best"] == 1

    day2 = update_streak(day1, active_date=date(2026, 2, 26))
    assert day2["current"] == 2
    assert day2["best"] == 2

    reset = update_streak(day2, active_date=date(2026, 2, 28))
    assert reset["current"] == 1
    assert reset["best"] == 2


def test_update_weekly_progress_accumulates() -> None:
    current = {"week_start": "2026-02-23", "xp": 10, "wins": 1, "sessions": 2}
    updated = update_weekly_progress(current, xp_gain=30, win_gain=1, session_gain=1)
    assert updated["xp"] >= 30
    assert updated["wins"] >= 1
    assert updated["sessions"] >= 1


def test_upsert_badge_unlocks_expected_badge() -> None:
    badges = [
        {"id": "ranked-rookie", "is_locked": True, "earned_at": None},
        {"id": "event-sprinter", "is_locked": True, "earned_at": None},
    ]
    updated = upsert_badge(badges, "event-sprinter")
    target = [badge for badge in updated if badge["id"] == "event-sprinter"][0]
    assert target["is_locked"] is False
    assert target["earned_at"] is not None
