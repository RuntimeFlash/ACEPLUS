from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def week_start_key(dt: Optional[datetime] = None) -> str:
    target = dt or datetime.now(timezone.utc)
    monday = target.date() - timedelta(days=target.weekday())
    return monday.isoformat()


def build_friend_code(user_id: str, standard: int) -> str:
    digest = hashlib.sha1(f"{user_id}:{standard}".encode("utf-8")).hexdigest()[:8].upper()
    return f"ACE-{digest}"


def default_badges() -> List[Dict[str, Any]]:
    return [
        {
            "id": "ranked-rookie",
            "type": "ranked",
            "name": "Ranked Rookie",
            "description": "Complete 10 exams to unlock.",
            "earned_at": None,
            "is_locked": True,
        },
        {
            "id": "event-sprinter",
            "type": "event",
            "name": "Event Sprinter",
            "description": "Complete your first test-series exam.",
            "earned_at": None,
            "is_locked": True,
        },
        {
            "id": "streak-keeper",
            "type": "streak",
            "name": "Streak Keeper",
            "description": "Reach a 7-day study streak.",
            "earned_at": None,
            "is_locked": True,
        },
        {
            "id": "helper-signal",
            "type": "helper",
            "name": "Helper Signal",
            "description": "Send 10 friend nudges.",
            "earned_at": None,
            "is_locked": True,
        },
    ]


def build_default_profile(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(user_doc.get("id", "")).strip()
    standard = int(user_doc.get("standard", 9) or 9)
    name = str(user_doc.get("name", user_id) or user_id)
    return {
        "username": user_id,
        "display_name": name,
        "avatar_url": "",
        "banner_url": "",
        "bio": "",
        "country": "",
        "timezone": "",
        "title": "",
        "theme": "default",
        "name_style": "default",
        "music_snippet": "",
        "status": "offline",
        "privacy": {"activity": "friends"},
        "friend_code": build_friend_code(user_id, standard),
        "showcase_badges": [],
        "badges": default_badges(),
        "streak": {
            "current": 0,
            "best": 0,
            "last_active_date": None,
        },
        "progress": {
            "xp": 0,
            "level": 1,
            "sessions": 0,
            "solved_items": 0,
            "wins": 0,
            "weekly": {
                "week_start": week_start_key(),
                "xp": 0,
                "wins": 0,
                "sessions": 0,
            },
        },
        "activity_feed": [],
        "nudge_stats": {"sent": 0, "received": 0},
        "last_seen_at": utc_now_iso(),
    }


def merge_profile_with_defaults(profile: Dict[str, Any], user_doc: Dict[str, Any]) -> Dict[str, Any]:
    base = build_default_profile(user_doc)
    merged = dict(base)
    merged.update(profile or {})

    privacy = dict(base.get("privacy", {}))
    privacy.update((profile or {}).get("privacy", {}) or {})
    merged["privacy"] = privacy

    streak = dict(base.get("streak", {}))
    streak.update((profile or {}).get("streak", {}) or {})
    merged["streak"] = streak

    progress = dict(base.get("progress", {}))
    progress.update((profile or {}).get("progress", {}) or {})
    weekly = dict(base.get("progress", {}).get("weekly", {}))
    weekly.update(((profile or {}).get("progress", {}) or {}).get("weekly", {}) or {})
    progress["weekly"] = weekly
    merged["progress"] = progress

    nudge_stats = dict(base.get("nudge_stats", {}))
    nudge_stats.update((profile or {}).get("nudge_stats", {}) or {})
    merged["nudge_stats"] = nudge_stats

    if not isinstance(merged.get("badges"), list):
        merged["badges"] = base["badges"]
    if not isinstance(merged.get("showcase_badges"), list):
        merged["showcase_badges"] = []
    if not isinstance(merged.get("activity_feed"), list):
        merged["activity_feed"] = []

    return merged


def compute_level_from_xp(xp: int) -> int:
    return max(1, (int(xp) // 100) + 1)


def update_streak(streak: Dict[str, Any], active_date: Optional[date] = None) -> Dict[str, Any]:
    current_date = active_date or datetime.now(timezone.utc).date()
    current = int(streak.get("current", 0) or 0)
    best = int(streak.get("best", 0) or 0)
    last_active_raw = streak.get("last_active_date")

    if last_active_raw:
        try:
            last_active_date = date.fromisoformat(str(last_active_raw))
        except ValueError:
            last_active_date = None
    else:
        last_active_date = None

    if last_active_date == current_date:
        return {
            "current": current,
            "best": max(best, current),
            "last_active_date": current_date.isoformat(),
        }

    if last_active_date and (current_date - last_active_date).days == 1:
        current += 1
    else:
        current = 1

    best = max(best, current)
    return {
        "current": current,
        "best": best,
        "last_active_date": current_date.isoformat(),
    }


def update_weekly_progress(weekly: Dict[str, Any], xp_gain: int, win_gain: int, session_gain: int) -> Dict[str, Any]:
    current_week = week_start_key()
    current = dict(weekly or {})
    if current.get("week_start") != current_week:
        current = {
            "week_start": current_week,
            "xp": 0,
            "wins": 0,
            "sessions": 0,
        }

    current["xp"] = int(current.get("xp", 0) or 0) + max(0, int(xp_gain))
    current["wins"] = int(current.get("wins", 0) or 0) + max(0, int(win_gain))
    current["sessions"] = int(current.get("sessions", 0) or 0) + max(0, int(session_gain))
    return current


def upsert_badge(badges: List[Dict[str, Any]], badge_id: str) -> List[Dict[str, Any]]:
    now_iso = utc_now_iso()
    updated: List[Dict[str, Any]] = []
    for badge in badges:
        item = dict(badge)
        if item.get("id") == badge_id:
            item["earned_at"] = item.get("earned_at") or now_iso
            item["is_locked"] = False
        updated.append(item)
    return updated
