from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional

from services.leaderboard_service import LeaderboardService
from services.test_database_service import TestDatabaseService
from services.upload_database_service import UploadDatabaseService
from services.user_stats_service import UserStatsService
from utils.mongo_utils import convert_objectid_to_str

from .base import DatabaseClient, WriteQueue
from .exam_repository import ExamRepository
from .leaderboard_service import LeaderboardRepository
from .mistake_replay_repository import MistakeReplayRepository
from .question_report_repository import QuestionReportRepository
from .static_content_repository import StaticContentRepository
from .test_repository import TestRepository
from .upload_repository import UploadRepository
from .user_repository import UserRepository

@dataclass
class _RepositoryContainer:
    db_client: DatabaseClient
    write_queue: WriteQueue
    user_repo: UserRepository
    exam_repo: ExamRepository
    replay_repo: MistakeReplayRepository
    test_repo: TestRepository
    leaderboard_repo: LeaderboardRepository
    leaderboard_service: LeaderboardService
    user_stats_service: UserStatsService
    test_database_service: TestDatabaseService
    upload_database_service: UploadDatabaseService
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
    replay = MistakeReplayRepository(db_client, write_queue)
    test = TestRepository(db_client, write_queue)
    leaderboard_repo = LeaderboardRepository(db_client)
    leaderboard = LeaderboardService(leaderboard_repo)
    user_stats = UserStatsService(user)
    test_database_service = TestDatabaseService(test)
    uploads = UploadRepository(db_client)
    upload_database_service = UploadDatabaseService(uploads)
    reports = QuestionReportRepository(db_client)
    static_content = StaticContentRepository(db_client)
    return _RepositoryContainer(
        db_client=db_client,
        write_queue=write_queue,
        user_repo=user,
        exam_repo=exam,
        replay_repo=replay,
        test_repo=test,
        leaderboard_repo=leaderboard_repo,
        leaderboard_service=leaderboard,
        user_stats_service=user_stats,
        test_database_service=test_database_service,
        upload_database_service=upload_database_service,
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
replay_repo = _LazyProxy("replay_repo")
test_repo = _LazyProxy("test_repo")
leaderboard_repo = _LazyProxy("leaderboard_repo")
leaderboard_service = _LazyProxy("leaderboard_service")
user_stats_service = _LazyProxy("user_stats_service")
test_database_service = _LazyProxy("test_database_service")
upload_database_service = _LazyProxy("upload_database_service")
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
    "MistakeReplayRepository",
    "TestRepository",
    "LeaderboardRepository",
    "LeaderboardService",
    "user_repo",
    "exam_repo",
    "replay_repo",
    "test_repo",
    "leaderboard_repo",
    "leaderboard_service",
    "user_stats_service",
    "test_database_service",
    "upload_database_service",
    "upload_repo",
    "question_report_repo",
    "static_content_repo",
    "convert_objectid_to_str",
    "preload_caches",
]
