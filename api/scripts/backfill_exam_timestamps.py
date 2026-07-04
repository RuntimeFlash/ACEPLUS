import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne


def _parse_legacy_ts(value):
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _env_or_fail(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required env var: {name}")
    return value


def main():
    backend_env = Path(__file__).resolve().parents[1] / ".env"
    if backend_env.exists():
        load_dotenv(backend_env)

    mongo_uri = _env_or_fail("MONGODB_URI")
    db9_name = _env_or_fail("MONGODB_DB_CLASS9")
    db10_name = _env_or_fail("MONGODB_DB_CLASS10")

    client = MongoClient(mongo_uri)
    db_names = [("class9", db9_name), ("class10", db10_name)]

    for label, db_name in db_names:
        db = client[db_name]
        users_col = db["Users"]
        exams_col = db["Exams"]

        users_result = users_col.update_many(
            {"teacher": {"$exists": False}},
            {"$set": {"teacher": False}},
        )

        ts_ops = []
        sub_ts_ops = []
        skipped_timestamp = 0
        skipped_submission = 0

        cursor = exams_col.find(
            {"timestamp_dt": {"$exists": False}},
            {"_id": 1, "timestamp": 1},
        )
        for doc in cursor:
            parsed = _parse_legacy_ts(doc.get("timestamp"))
            if not parsed:
                skipped_timestamp += 1
                continue
            ts_ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": {"timestamp_dt": parsed}}))

        cursor = exams_col.find(
            {
                "submission_timestamp_dt": {"$exists": False},
                "submission_timestamp": {"$exists": True},
            },
            {"_id": 1, "submission_timestamp": 1},
        )
        for doc in cursor:
            parsed = _parse_legacy_ts(doc.get("submission_timestamp"))
            if not parsed:
                skipped_submission += 1
                continue
            sub_ts_ops.append(
                UpdateOne({"_id": doc["_id"]}, {"$set": {"submission_timestamp_dt": parsed}})
            )

        updated_timestamp = 0
        updated_submission = 0
        if ts_ops:
            result = exams_col.bulk_write(ts_ops, ordered=False)
            updated_timestamp = result.modified_count
        if sub_ts_ops:
            result = exams_col.bulk_write(sub_ts_ops, ordered=False)
            updated_submission = result.modified_count

        print(
            f"[{label}] users_teacher_backfilled={users_result.modified_count} "
            f"timestamp_dt_backfilled={updated_timestamp} timestamp_parse_skipped={skipped_timestamp} "
            f"submission_timestamp_dt_backfilled={updated_submission} submission_parse_skipped={skipped_submission}"
        )


if __name__ == "__main__":
    main()
