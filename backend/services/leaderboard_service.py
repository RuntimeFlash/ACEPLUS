from __future__ import annotations

from typing import Any, Dict, Optional

from utils.date_utils import current_month_key
from utils.leaderboard_utils import entry_from_user_for_month, generate_version, sort_entries


class LeaderboardService:
    def __init__(self, leaderboard_repo: Any) -> None:
        self.leaderboard_repo = leaderboard_repo

    def _build_snapshot_for_month(self, standard: int, month_key: str) -> Dict[str, Any]:
        entries = []
        users = self.leaderboard_repo.list_users_for_standard(standard)
        for user in users:
            if user.get("teacher"):
                continue
            entry = entry_from_user_for_month(user, month_key)
            if entry:
                entries.append(entry)

        sort_entries(entries)
        return self.leaderboard_repo.upsert_monthly_snapshot(
            standard=standard,
            month_key=month_key,
            entries=entries,
            version=generate_version(month_key),
        )

    def get_or_build_monthly(
        self,
        standard: int,
        month_key: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        mk = month_key or current_month_key()
        doc = self.leaderboard_repo.get_monthly_snapshot(standard, mk)
        if not doc:
            doc = self._build_snapshot_for_month(standard, mk)

        entries = list(doc.get("entries", []))
        total_count = len(entries)
        start_idx = max(0, (page - 1) * page_size)
        end_idx = min(total_count, start_idx + page_size)
        paged_entries = [dict(entry) for entry in entries[start_idx:end_idx]]
        for i, entry in enumerate(paged_entries, 1):
            entry["rank"] = start_idx + i

        return {
            "version": doc.get("version"),
            "month": mk,
            "standard": standard,
            "total_count": total_count,
            "entries": paged_entries,
        }

    def preload_current_month_leaderboard(self) -> None:
        print("Pre-loading current month leaderboard...")
        month_key = current_month_key()
        for standard in (9, 10):
            try:
                doc = self.leaderboard_repo.get_monthly_snapshot(standard, month_key)
                if not doc:
                    self._build_snapshot_for_month(standard, month_key)
            except Exception as exc:
                print(f"Error pre-loading leaderboard for standard {standard}: {exc}")
        print("Finished pre-loading leaderboard.")

    def update_on_submission(self, user_id: str, standard: int, month_key: Optional[str] = None) -> None:
        mk = month_key or current_month_key()
        doc = self.leaderboard_repo.get_monthly_snapshot(standard, mk)
        if not doc:
            doc = self._build_snapshot_for_month(standard, mk)

        user = self.leaderboard_repo.get_user_for_standard(standard, user_id)
        if not user or user.get("teacher"):
            return

        updated_entry = entry_from_user_for_month(user, mk)
        if updated_entry is None:
            return

        entries = list(doc.get("entries", []))
        replaced = False
        for idx, entry in enumerate(entries):
            if entry.get("userId") == user_id:
                entries[idx] = updated_entry
                replaced = True
                break
        if not replaced:
            entries.append(updated_entry)

        sort_entries(entries)
        version = doc.get("version") or generate_version(mk)
        self.leaderboard_repo.upsert_monthly_snapshot(
            standard=standard,
            month_key=mk,
            entries=entries,
            version=version,
        )
