from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pymongo import ASCENDING, DESCENDING

from db import user_repo
from utils.social_utils import (
    compute_level_from_xp,
    merge_profile_with_defaults,
    update_streak,
    update_weekly_progress,
    upsert_badge,
    utc_now_iso,
)

ALLOWED_PRIVACY = {"public", "friends", "private"}
ALLOWED_STATUS = {"online", "studying", "challenge", "offline"}


class SocialService:
    def __init__(self) -> None:
        self.db_client = user_repo.db_client
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        for standard in (9, 10):
            users = self.db_client.get_collection("Users", standard=standard)
            users.create_index([("profile.friend_code", ASCENDING)], unique=True, sparse=True)
            users.create_index([("profile.username", ASCENDING)], unique=True, sparse=True)

            requests = self.db_client.get_collection("FriendRequests", standard=standard)
            requests.create_index([("request_id", ASCENDING)], unique=True)
            requests.create_index([("to_user_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)])
            requests.create_index([("from_user_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)])

            challenges = self.db_client.get_collection("FriendChallenges", standard=standard)
            challenges.create_index([("challenge_id", ASCENDING)], unique=True)
            challenges.create_index([("participant_ids", ASCENDING)])

            squads = self.db_client.get_collection("StudySquads", standard=standard)
            squads.create_index([("squad_id", ASCENDING)], unique=True)
            squads.create_index([("member_ids", ASCENDING)])

            nudges = self.db_client.get_collection("FriendNudges", standard=standard)
            nudges.create_index([("nudge_id", ASCENDING)], unique=True)
            nudges.create_index([("to_user_id", ASCENDING), ("read", ASCENDING), ("created_at", DESCENDING)])

    def _is_class10(self, user_doc: Dict[str, Any]) -> bool:
        return int(user_doc.get("standard", 9) or 9) == 10

    def _users_col(self, is_class10: bool):
        return self.db_client.get_collection("Users", is_class10=is_class10)

    def _requests_col(self, is_class10: bool):
        return self.db_client.get_collection("FriendRequests", is_class10=is_class10)

    def _challenges_col(self, is_class10: bool):
        return self.db_client.get_collection("FriendChallenges", is_class10=is_class10)

    def _squads_col(self, is_class10: bool):
        return self.db_client.get_collection("StudySquads", is_class10=is_class10)

    def _nudges_col(self, is_class10: bool):
        return self.db_client.get_collection("FriendNudges", is_class10=is_class10)

    def _get_user_with_class(
        self,
        user_id: str,
        is_class10: Optional[bool] = None,
    ) -> tuple[Optional[Dict[str, Any]], Optional[bool]]:
        user = user_repo.get_user(user_id, is_class10)
        if not user:
            return None, None
        return user, self._is_class10(user)

    def _ensure_profile(self, user_doc: Dict[str, Any], is_class10: bool) -> Dict[str, Any]:
        profile = merge_profile_with_defaults(user_doc.get("profile", {}) or {}, user_doc)
        updates: Dict[str, Any] = {}
        if user_doc.get("profile") != profile:
            updates["profile"] = profile
        if not isinstance(user_doc.get("friends"), list):
            updates["friends"] = []
        if updates:
            self._users_col(is_class10).update_one({"id": user_doc.get("id")}, {"$set": updates})
        return profile

    def _summary(self, user_doc: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        progress = profile.get("progress", {}) or {}
        streak = profile.get("streak", {}) or {}
        weekly = progress.get("weekly", {}) or {}
        return {
            "user_id": user_doc.get("id"),
            "name": user_doc.get("name"),
            "username": profile.get("username", user_doc.get("id")),
            "avatar_url": profile.get("avatar_url", ""),
            "status": profile.get("status", "offline"),
            "title": profile.get("title", ""),
            "level": int(progress.get("level", 1) or 1),
            "xp": int(progress.get("xp", 0) or 0),
            "current_streak": int(streak.get("current", 0) or 0),
            "best_streak": int(streak.get("best", 0) or 0),
            "wins": int(progress.get("wins", 0) or 0),
            "weekly_xp": int(weekly.get("xp", 0) or 0),
            "weekly_wins": int(weekly.get("wins", 0) or 0),
            "weekly_sessions": int(weekly.get("sessions", 0) or 0),
            "last_seen_at": profile.get("last_seen_at"),
        }

    def _push_activity(
        self,
        user_id: str,
        is_class10: bool,
        activity_type: str,
        message: str,
        visibility: str = "friends",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if visibility not in ALLOWED_PRIVACY:
            visibility = "friends"
        activity = {
            "activity_id": str(uuid4()),
            "type": activity_type,
            "message": message,
            "visibility": visibility,
            "metadata": metadata or {},
            "created_at": utc_now_iso(),
        }
        self._users_col(is_class10).update_one(
            {"id": user_id},
            {"$push": {"profile.activity_feed": {"$each": [activity], "$position": 0, "$slice": 50}}},
        )

    def get_profile(self, requester_id: str, target_user_id: Optional[str] = None) -> Dict[str, Any]:
        target_id = target_user_id or requester_id
        target_user, is_class10 = self._get_user_with_class(target_id)
        if not target_user or is_class10 is None:
            raise ValueError("user not found")

        profile = self._ensure_profile(target_user, is_class10)
        is_self = requester_id == target_id
        is_friend = False
        if not is_self:
            requester = user_repo.get_user(requester_id, is_class10)
            requester_friends = (requester or {}).get("friends", []) or []
            is_friend = target_id in requester_friends

        privacy = str((profile.get("privacy", {}) or {}).get("activity", "friends"))
        can_view_activity = is_self or privacy == "public" or (privacy == "friends" and is_friend)

        progress = profile.get("progress", {}) or {}
        streak = profile.get("streak", {}) or {}
        badges = profile.get("badges", []) or []
        unlocked_badges = [badge for badge in badges if not badge.get("is_locked")]
        data = {
            "user_id": target_user.get("id"),
            "name": target_user.get("name"),
            "standard": int(target_user.get("standard", 9) or 9),
            "division": target_user.get("division"),
            "username": profile.get("username", target_user.get("id")),
            "display_name": profile.get("display_name", target_user.get("name", "")),
            "avatar_url": profile.get("avatar_url", ""),
            "banner_url": profile.get("banner_url", ""),
            "bio": profile.get("bio", ""),
            "country": profile.get("country", ""),
            "timezone": profile.get("timezone", ""),
            "title": profile.get("title", ""),
            "theme": profile.get("theme", "default"),
            "name_style": profile.get("name_style", "default"),
            "music_snippet": profile.get("music_snippet", ""),
            "status": profile.get("status", "offline"),
            "privacy": profile.get("privacy", {"activity": "friends"}),
            "showcase_badges": profile.get("showcase_badges", [])[:3],
            "badges": badges,
            "unlocked_badges": unlocked_badges,
            "streak": {
                "current": int(streak.get("current", 0) or 0),
                "best": int(streak.get("best", 0) or 0),
                "last_active_date": streak.get("last_active_date"),
            },
            "progress": {
                "xp": int(progress.get("xp", 0) or 0),
                "level": int(progress.get("level", 1) or 1),
                "to_next_level": 100 - (int(progress.get("xp", 0) or 0) % 100),
                "sessions": int(progress.get("sessions", 0) or 0),
                "solved_items": int(progress.get("solved_items", 0) or 0),
                "wins": int(progress.get("wins", 0) or 0),
                "weekly": progress.get("weekly", {}),
            },
            "activity_feed": (profile.get("activity_feed", []) or [])[:25] if can_view_activity else [],
            "friend_count": len(target_user.get("friends", []) or []),
            "is_self": is_self,
            "is_friend": is_friend,
            "can_view_activity": can_view_activity,
            "last_seen_at": profile.get("last_seen_at"),
        }
        if is_self:
            data["friend_code"] = profile.get("friend_code")
        return data

    def update_profile(self, requester_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        profile = self._ensure_profile(user, is_class10)

        updates: Dict[str, Any] = {}
        username = payload.get("username")
        if username is not None:
            normalized = str(username).strip().lower()
            if not re.fullmatch(r"[a-z0-9_]{3,24}", normalized):
                raise ValueError("username must be 3-24 chars and use a-z, 0-9, underscore")
            if normalized != str(profile.get("username", "")).lower():
                existing = self._users_col(is_class10).find_one(
                    {"profile.username": normalized, "id": {"$ne": requester_id}},
                    {"_id": 1},
                )
                if existing:
                    raise ValueError("username already in use")
            updates["profile.username"] = normalized

        for field in [
            "display_name",
            "avatar_url",
            "banner_url",
            "bio",
            "country",
            "timezone",
            "title",
            "theme",
            "name_style",
            "music_snippet",
        ]:
            if field in payload:
                updates[f"profile.{field}"] = str(payload.get(field, "") or "").strip()

        if "status" in payload:
            status = str(payload.get("status", "")).strip().lower()
            if status not in ALLOWED_STATUS:
                raise ValueError("status must be online/studying/challenge/offline")
            updates["profile.status"] = status
            updates["profile.last_seen_at"] = utc_now_iso()

        if "privacy" in payload:
            activity = str(((payload.get("privacy") or {}).get("activity", "friends"))).strip().lower()
            if activity not in ALLOWED_PRIVACY:
                raise ValueError("privacy.activity must be public/friends/private")
            updates["profile.privacy.activity"] = activity

        if updates:
            self._users_col(is_class10).update_one({"id": requester_id}, {"$set": updates})

        return self.get_profile(requester_id, requester_id)

    def set_status(self, requester_id: str, status: str) -> Dict[str, Any]:
        normalized = str(status).strip().lower()
        if normalized not in ALLOWED_STATUS:
            raise ValueError("status must be online/studying/challenge/offline")

        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        self._ensure_profile(user, is_class10)
        self._users_col(is_class10).update_one(
            {"id": requester_id},
            {"$set": {"profile.status": normalized, "profile.last_seen_at": utc_now_iso()}},
        )
        return {"status": normalized}

    def set_showcase_badges(self, requester_id: str, badge_ids: List[str]) -> Dict[str, Any]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        profile = self._ensure_profile(user, is_class10)
        unlocked = {
            str(item.get("id"))
            for item in (profile.get("badges", []) or [])
            if not item.get("is_locked") and item.get("id")
        }
        cleaned: List[str] = []
        for badge_id in badge_ids or []:
            value = str(badge_id).strip()
            if value in unlocked and value not in cleaned:
                cleaned.append(value)
            if len(cleaned) == 3:
                break

        self._users_col(is_class10).update_one(
            {"id": requester_id},
            {"$set": {"profile.showcase_badges": cleaned}},
        )
        return {"showcase_badges": cleaned}

    def search_users(self, requester_id: str, query: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")

        search = str(query or "").strip()
        filters: Dict[str, Any] = {"teacher": False, "id": {"$ne": requester_id}}
        if search:
            escaped = re.escape(search)
            regex = {"$regex": escaped, "$options": "i"}
            filters["$or"] = [
                {"id": regex},
                {"name": regex},
                {"profile.username": regex},
                {"profile.friend_code": {"$regex": f"^{escaped}$", "$options": "i"}},
            ]

        docs = self._users_col(is_class10).find(filters).limit(max(1, min(limit, 50)))
        requester_friends = set(user.get("friends", []) or [])

        results: List[Dict[str, Any]] = []
        for doc in docs:
            profile = self._ensure_profile(doc, is_class10)
            item = self._summary(doc, profile)
            item["friend_code"] = profile.get("friend_code")
            item["is_friend"] = item["user_id"] in requester_friends
            results.append(item)
        return results

    def _resolve_identifier(self, requester_id: str, identifier: str) -> tuple[Dict[str, Any], bool]:
        requester, is_class10 = self._get_user_with_class(requester_id)
        if not requester or is_class10 is None:
            raise ValueError("user not found")
        value = str(identifier or "").strip()
        if not value:
            raise ValueError("identifier is required")

        target = self._users_col(is_class10).find_one({"id": value, "teacher": False})
        if not target:
            target = self._users_col(is_class10).find_one({"profile.friend_code": value.upper(), "teacher": False})
        if not target:
            target = self._users_col(is_class10).find_one(
                {"profile.username": {"$regex": f"^{re.escape(value)}$", "$options": "i"}, "teacher": False}
            )
        if not target:
            raise ValueError("target user not found")
        return target, is_class10

    def send_friend_request(self, requester_id: str, identifier: str) -> Dict[str, Any]:
        target, is_class10 = self._resolve_identifier(requester_id, identifier)
        target_id = str(target.get("id"))
        if target_id == requester_id:
            raise ValueError("cannot send request to yourself")

        requester = self._users_col(is_class10).find_one({"id": requester_id})
        requester_friends = set((requester or {}).get("friends", []) or [])
        if target_id in requester_friends:
            raise ValueError("already friends")

        requests = self._requests_col(is_class10)
        reverse = requests.find_one({"from_user_id": target_id, "to_user_id": requester_id, "status": "pending"})
        if reverse:
            requests.update_one(
                {"request_id": reverse.get("request_id")},
                {"$set": {"status": "accepted", "responded_at": utc_now_iso(), "updated_at": utc_now_iso()}},
            )
            self._users_col(is_class10).update_one({"id": requester_id}, {"$addToSet": {"friends": target_id}})
            self._users_col(is_class10).update_one({"id": target_id}, {"$addToSet": {"friends": requester_id}})
            return {"auto_accepted": True, "friend_id": target_id}

        existing = requests.find_one({"from_user_id": requester_id, "to_user_id": target_id, "status": "pending"})
        if existing:
            raise ValueError("friend request already pending")

        request_id = str(uuid4())
        requests.insert_one(
            {
                "request_id": request_id,
                "from_user_id": requester_id,
                "to_user_id": target_id,
                "status": "pending",
                "created_at": utc_now_iso(),
                "updated_at": utc_now_iso(),
            }
        )
        self._push_activity(
            requester_id,
            is_class10,
            "friend-request",
            f"Sent a friend request to {target_id}.",
            metadata={"to_user_id": target_id},
        )
        return {"request_id": request_id, "to_user_id": target_id, "status": "pending", "auto_accepted": False}

    def get_friend_requests(self, requester_id: str) -> Dict[str, List[Dict[str, Any]]]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        requests = self._requests_col(is_class10)
        incoming_docs = list(requests.find({"to_user_id": requester_id, "status": "pending"}).sort("created_at", DESCENDING))
        outgoing_docs = list(requests.find({"from_user_id": requester_id, "status": "pending"}).sort("created_at", DESCENDING))

        def map_doc(doc: Dict[str, Any], peer_field: str) -> Dict[str, Any]:
            peer_id = str(doc.get(peer_field, ""))
            peer_doc = self._users_col(is_class10).find_one({"id": peer_id})
            if not peer_doc:
                peer = {"user_id": peer_id}
            else:
                peer_profile = self._ensure_profile(peer_doc, is_class10)
                peer = self._summary(peer_doc, peer_profile)
            return {
                "request_id": doc.get("request_id"),
                "status": doc.get("status"),
                "created_at": doc.get("created_at"),
                "peer": peer,
            }

        return {
            "incoming": [map_doc(doc, "from_user_id") for doc in incoming_docs],
            "outgoing": [map_doc(doc, "to_user_id") for doc in outgoing_docs],
        }

    def respond_friend_request(self, requester_id: str, request_id: str, action: str) -> Dict[str, Any]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        normalized_action = str(action or "").strip().lower()
        if normalized_action not in {"accept", "decline"}:
            raise ValueError("action must be accept or decline")

        requests = self._requests_col(is_class10)
        doc = requests.find_one({"request_id": request_id, "to_user_id": requester_id, "status": "pending"})
        if not doc:
            raise ValueError("friend request not found")

        from_user_id = str(doc.get("from_user_id"))
        status = "accepted" if normalized_action == "accept" else "declined"
        requests.update_one(
            {"request_id": request_id},
            {"$set": {"status": status, "responded_at": utc_now_iso(), "updated_at": utc_now_iso()}},
        )
        if status == "accepted":
            self._users_col(is_class10).update_one({"id": requester_id}, {"$addToSet": {"friends": from_user_id}})
            self._users_col(is_class10).update_one({"id": from_user_id}, {"$addToSet": {"friends": requester_id}})
            self._push_activity(requester_id, is_class10, "friend", f"You and {from_user_id} are now friends.")

        return {"request_id": request_id, "status": status, "friend_id": from_user_id if status == "accepted" else None}

    def get_friends(self, requester_id: str) -> List[Dict[str, Any]]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        friend_ids = user.get("friends", []) or []
        output: List[Dict[str, Any]] = []
        for friend_id in friend_ids:
            doc = self._users_col(is_class10).find_one({"id": friend_id})
            if not doc:
                continue
            profile = self._ensure_profile(doc, is_class10)
            output.append(self._summary(doc, profile))
        output.sort(key=lambda item: str(item.get("username", "")).lower())
        return output

    def remove_friend(self, requester_id: str, friend_id: str) -> Dict[str, Any]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        self._users_col(is_class10).update_one({"id": requester_id}, {"$pull": {"friends": friend_id}})
        self._users_col(is_class10).update_one({"id": friend_id}, {"$pull": {"friends": requester_id}})
        self._push_activity(
            requester_id,
            is_class10,
            "friend",
            f"Removed {friend_id} from friends.",
            metadata={"friend_id": friend_id},
        )
        return {"removed": True, "friend_id": friend_id}

    def get_friend_leaderboard(self, requester_id: str, metric: str = "xp") -> List[Dict[str, Any]]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        metric_key = str(metric or "xp").strip().lower()
        if metric_key not in {"xp", "wins", "streak"}:
            metric_key = "xp"

        ids = [requester_id] + list(user.get("friends", []) or [])
        rows: List[Dict[str, Any]] = []
        for user_id in dict.fromkeys(ids):
            doc = self._users_col(is_class10).find_one({"id": user_id})
            if not doc:
                continue
            profile = self._ensure_profile(doc, is_class10)
            summary = self._summary(doc, profile)
            if metric_key == "xp":
                score = int(summary.get("weekly_xp", 0) or 0)
            elif metric_key == "wins":
                score = int(summary.get("weekly_wins", 0) or 0)
            else:
                score = int(summary.get("current_streak", 0) or 0)
            rows.append({"user": summary, "metric": metric_key, "score": score})

        rows.sort(key=lambda item: (-int(item.get("score", 0)), str((item.get("user") or {}).get("username", "")).lower()))
        for idx, row in enumerate(rows, 1):
            row["rank"] = idx
        return rows

    def create_challenge(
        self,
        requester_id: str,
        title: str,
        goal_type: str,
        goal_value: int,
        participant_ids: List[str],
        end_date: Optional[str],
    ) -> Dict[str, Any]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        allowed = {"xp", "wins", "streak", "sessions"}
        goal = str(goal_type or "xp").strip().lower()
        if goal not in allowed:
            raise ValueError("goal_type must be xp/wins/streak/sessions")

        unique = [requester_id]
        for user_id in participant_ids or []:
            value = str(user_id).strip()
            if value and value not in unique:
                unique.append(value)
        if len(unique) < 2:
            raise ValueError("challenge needs at least 2 participants")

        friends = set(user.get("friends", []) or [])
        for user_id in unique:
            if user_id != requester_id and user_id not in friends:
                raise ValueError(f"{user_id} is not your friend")

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("end_date must be an ISO datetime") from exc
        else:
            end_dt = datetime.now(timezone.utc) + timedelta(days=7)

        challenge = {
            "challenge_id": str(uuid4()),
            "title": str(title or "").strip() or "Weekly Challenge",
            "goal_type": goal,
            "goal_value": max(1, int(goal_value or 1)),
            "participant_ids": unique,
            "created_by": requester_id,
            "created_at": utc_now_iso(),
            "end_date": end_dt.astimezone(timezone.utc).isoformat(),
            "status": "active",
        }
        self._challenges_col(is_class10).insert_one(challenge)
        self._push_activity(
            requester_id,
            is_class10,
            "challenge",
            f"Created challenge '{challenge['title']}'.",
            metadata={"challenge_id": challenge["challenge_id"]},
        )
        return challenge

    def get_challenges(self, requester_id: str) -> List[Dict[str, Any]]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        docs = list(self._challenges_col(is_class10).find({"participant_ids": requester_id}).sort("created_at", DESCENDING))
        now = datetime.now(timezone.utc)
        rows: List[Dict[str, Any]] = []
        for doc in docs:
            goal_type = str(doc.get("goal_type", "xp"))
            goal_value = int(doc.get("goal_value", 1) or 1)
            participants = []
            all_done = True
            for pid in doc.get("participant_ids", []) or []:
                peer = self._users_col(is_class10).find_one({"id": pid})
                if not peer:
                    continue
                profile = self._ensure_profile(peer, is_class10)
                summary = self._summary(peer, profile)
                if goal_type == "xp":
                    progress = int(summary.get("weekly_xp", 0) or 0)
                elif goal_type == "wins":
                    progress = int(summary.get("weekly_wins", 0) or 0)
                elif goal_type == "sessions":
                    progress = int(summary.get("weekly_sessions", 0) or 0)
                else:
                    progress = int(summary.get("current_streak", 0) or 0)
                completed = progress >= goal_value
                all_done = all_done and completed
                participants.append({"user": summary, "progress": progress, "completed": completed})

            status = str(doc.get("status", "active"))
            try:
                end_dt = datetime.fromisoformat(str(doc.get("end_date", "")).replace("Z", "+00:00"))
            except ValueError:
                end_dt = now
            if status == "active" and (all_done or now >= end_dt):
                status = "completed"
                self._challenges_col(is_class10).update_one(
                    {"challenge_id": doc.get("challenge_id")},
                    {"$set": {"status": "completed", "completed_at": utc_now_iso()}},
                )

            rows.append(
                {
                    "challenge_id": doc.get("challenge_id"),
                    "title": doc.get("title"),
                    "goal_type": goal_type,
                    "goal_value": goal_value,
                    "status": status,
                    "created_by": doc.get("created_by"),
                    "created_at": doc.get("created_at"),
                    "end_date": doc.get("end_date"),
                    "participants": participants,
                }
            )
        return rows

    def create_squad(self, requester_id: str, name: str, member_ids: List[str], goal: Dict[str, Any]) -> Dict[str, Any]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        members = [requester_id]
        for member in member_ids or []:
            value = str(member).strip()
            if value and value not in members:
                members.append(value)
        if len(members) < 2:
            raise ValueError("squad needs at least 2 members")

        friends = set(user.get("friends", []) or [])
        for member in members:
            if member != requester_id and member not in friends:
                raise ValueError(f"{member} is not your friend")

        clean_goal = {
            "title": str((goal or {}).get("title", "Weekly Study Goal")).strip() or "Weekly Study Goal",
            "type": str((goal or {}).get("type", "sessions")).strip().lower(),
            "target": max(1, int((goal or {}).get("target", 5) or 5)),
            "deadline": str((goal or {}).get("deadline", "")).strip() or None,
            "note": str((goal or {}).get("note", "")).strip(),
        }
        squad = {
            "squad_id": str(uuid4()),
            "name": str(name or "").strip() or "Study Squad",
            "owner_user_id": requester_id,
            "member_ids": members,
            "goal": clean_goal,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        self._squads_col(is_class10).insert_one(squad)
        return squad

    def get_squads(self, requester_id: str) -> List[Dict[str, Any]]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")

        docs = list(self._squads_col(is_class10).find({"member_ids": requester_id}).sort("updated_at", DESCENDING))
        rows: List[Dict[str, Any]] = []
        for doc in docs:
            members = []
            for user_id in doc.get("member_ids", []) or []:
                member_doc = self._users_col(is_class10).find_one({"id": user_id})
                if not member_doc:
                    continue
                member_profile = self._ensure_profile(member_doc, is_class10)
                members.append(self._summary(member_doc, member_profile))
            rows.append(
                {
                    "squad_id": doc.get("squad_id"),
                    "name": doc.get("name"),
                    "owner_user_id": doc.get("owner_user_id"),
                    "goal": doc.get("goal", {}),
                    "members": members,
                    "created_at": doc.get("created_at"),
                    "updated_at": doc.get("updated_at"),
                }
            )
        return rows

    def update_squad_goal(self, requester_id: str, squad_id: str, goal: Dict[str, Any]) -> Dict[str, Any]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")

        squad = self._squads_col(is_class10).find_one({"squad_id": squad_id})
        if not squad:
            raise ValueError("squad not found")
        if str(squad.get("owner_user_id")) != requester_id:
            raise ValueError("only squad owner can update goal")

        clean_goal = {
            "title": str((goal or {}).get("title", "Weekly Study Goal")).strip() or "Weekly Study Goal",
            "type": str((goal or {}).get("type", "sessions")).strip().lower(),
            "target": max(1, int((goal or {}).get("target", 5) or 5)),
            "deadline": str((goal or {}).get("deadline", "")).strip() or None,
            "note": str((goal or {}).get("note", "")).strip(),
        }
        self._squads_col(is_class10).update_one(
            {"squad_id": squad_id},
            {"$set": {"goal": clean_goal, "updated_at": utc_now_iso()}},
        )
        return {"squad_id": squad_id, "goal": clean_goal}

    def send_nudge(self, requester_id: str, friend_id: str, nudge_type: str, message: str) -> Dict[str, Any]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        friend = self._users_col(is_class10).find_one({"id": friend_id})
        if not friend:
            raise ValueError("friend not found")
        if friend_id not in (user.get("friends", []) or []):
            raise ValueError("you can only nudge friends")

        nudge = {
            "nudge_id": str(uuid4()),
            "from_user_id": requester_id,
            "to_user_id": friend_id,
            "type": str(nudge_type or "study").strip().lower() or "study",
            "message": str(message or "").strip() or "Your friend invited you to study.",
            "read": False,
            "created_at": utc_now_iso(),
        }
        self._nudges_col(is_class10).insert_one(nudge)
        sender_profile = self._ensure_profile(user, is_class10)
        sender_stats = sender_profile.get("nudge_stats", {}) or {"sent": 0, "received": 0}
        sender_stats["sent"] = int(sender_stats.get("sent", 0) or 0) + 1
        sender_profile["nudge_stats"] = sender_stats
        if int(sender_stats.get("sent", 0) or 0) >= 10:
            sender_profile["badges"] = upsert_badge(sender_profile.get("badges", []) or [], "helper-signal")
        self._users_col(is_class10).update_one({"id": requester_id}, {"$set": {"profile": sender_profile}})

        friend_profile = self._ensure_profile(friend, is_class10)
        friend_stats = friend_profile.get("nudge_stats", {}) or {"sent": 0, "received": 0}
        friend_stats["received"] = int(friend_stats.get("received", 0) or 0) + 1
        friend_profile["nudge_stats"] = friend_stats
        self._users_col(is_class10).update_one({"id": friend_id}, {"$set": {"profile": friend_profile}})

        self._push_activity(requester_id, is_class10, "nudge", f"Nudged {friend_id} to join a study session.")
        return nudge

    def get_nudges(self, requester_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        query: Dict[str, Any] = {"to_user_id": requester_id}
        if unread_only:
            query["read"] = False
        docs = list(self._nudges_col(is_class10).find(query).sort("created_at", DESCENDING).limit(50))
        rows: List[Dict[str, Any]] = []
        for doc in docs:
            from_user_id = str(doc.get("from_user_id", ""))
            from_doc = self._users_col(is_class10).find_one({"id": from_user_id})
            from_summary = {"user_id": from_user_id}
            if from_doc:
                from_profile = self._ensure_profile(from_doc, is_class10)
                from_summary = self._summary(from_doc, from_profile)
            rows.append(
                {
                    "nudge_id": doc.get("nudge_id"),
                    "type": doc.get("type"),
                    "message": doc.get("message"),
                    "read": bool(doc.get("read", False)),
                    "created_at": doc.get("created_at"),
                    "from_user": from_summary,
                }
            )
        return rows

    def mark_nudge_read(self, requester_id: str, nudge_id: str) -> Dict[str, Any]:
        user, is_class10 = self._get_user_with_class(requester_id)
        if not user or is_class10 is None:
            raise ValueError("user not found")
        result = self._nudges_col(is_class10).update_one(
            {"nudge_id": nudge_id, "to_user_id": requester_id},
            {"$set": {"read": True, "read_at": utc_now_iso()}},
        )
        return {"updated": result.matched_count > 0}

    def update_progress_after_exam(
        self,
        user_id: str,
        *,
        subject: str,
        exam_id: str,
        score: int,
        total_questions: int,
        percentage: float,
        is_test: bool,
    ) -> None:
        user, is_class10 = self._get_user_with_class(user_id)
        if not user or is_class10 is None:
            return
        profile = self._ensure_profile(user, is_class10)
        progress = profile.get("progress", {}) or {}
        streak = update_streak(profile.get("streak", {}) or {})

        base_xp = max(10, int(score) * 8)
        bonus_xp = 20 if is_test else 0
        xp_gain = base_xp + bonus_xp
        win_gain = 1 if float(percentage) >= 80.0 else 0

        progress["xp"] = int(progress.get("xp", 0) or 0) + xp_gain
        progress["level"] = compute_level_from_xp(progress["xp"])
        progress["sessions"] = int(progress.get("sessions", 0) or 0) + 1
        progress["solved_items"] = int(progress.get("solved_items", 0) or 0) + max(0, int(total_questions))
        progress["wins"] = int(progress.get("wins", 0) or 0) + win_gain
        progress["weekly"] = update_weekly_progress(progress.get("weekly", {}), xp_gain, win_gain, 1)

        badges = profile.get("badges", []) or []
        attempted = int(((user.get("stats", {}) or {}).get("attempted", 0) or 0))
        if attempted >= 10:
            badges = upsert_badge(badges, "ranked-rookie")
        if is_test:
            badges = upsert_badge(badges, "event-sprinter")
        if int(streak.get("current", 0) or 0) >= 7:
            badges = upsert_badge(badges, "streak-keeper")
        profile["badges"] = badges
        profile["streak"] = streak
        profile["progress"] = progress
        profile["last_seen_at"] = utc_now_iso()

        self._users_col(is_class10).update_one({"id": user_id}, {"$set": {"profile": profile}})
        self._push_activity(
            user_id,
            is_class10,
            "exam",
            f"Completed {subject} exam ({score}/{total_questions}, {float(percentage):.1f}%).",
            metadata={"exam_id": exam_id, "xp_gain": xp_gain, "is_test": is_test},
        )


social_service = SocialService()
