#!/usr/bin/env python3
"""
One-shot index creation for AcePlus MongoDB.

On Vercel/serverless, repositories intentionally skip create_index on cold start
(each index ensure is a network round-trip; dozens of them add multi-second latency).

Run this once after deploy / schema changes:

  ENSURE_INDEXES=1 python api/scripts/ensure_indexes.py

Requires MONGODB_URI, MONGODB_DB_CLASS9, MONGODB_DB_CLASS10 in the environment.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

api_dir = Path(__file__).resolve().parents[1]
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Force index creation even when SERVERLESS/VERCEL are set in the shell.
os.environ["ENSURE_INDEXES"] = "1"


def main() -> None:
    from db.base import DatabaseClient, WriteQueue
    from db.exam_repository import ExamRepository
    from db.mistake_replay_repository import MistakeReplayRepository
    from db.question_report_repository import QuestionReportRepository
    from db.static_content_repository import StaticContentRepository
    from db.test_repository import TestRepository
    from db.upload_repository import UploadRepository
    from db.user_repository import UserRepository
    from services.social_service import SocialService

    print("Connecting to MongoDB and ensuring indexes...")
    client = DatabaseClient()
    wq = WriteQueue(client, worker_count=0)

    UserRepository(client, wq).ensure_indexes()
    print("  ✓ Users")
    ExamRepository(client, wq).ensure_indexes()
    print("  ✓ Exams")
    TestRepository(client, wq).ensure_indexes()
    print("  ✓ Tests")
    MistakeReplayRepository(client, wq).ensure_indexes()
    print("  ✓ MistakeReplay")
    UploadRepository(client).ensure_indexes()
    print("  ✓ Uploads")
    QuestionReportRepository(client).ensure_indexes()
    print("  ✓ QuestionReports")
    StaticContentRepository(client).ensure_indexes()
    print("  ✓ StaticContent")

    # Social indexes (friends / challenges / squads / nudges)
    SocialService()._ensure_indexes()
    print("  ✓ Social collections")

    print("Done. Indexes are ready for serverless traffic.")


if __name__ == "__main__":
    main()
