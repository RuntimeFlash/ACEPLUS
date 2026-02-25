import os
import time
from datetime import datetime, timedelta, timezone

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def cleanup_old_files(upload_folder):
    current_time = time.time()
    one_hour = 60 * 60

    for filename in os.listdir(upload_folder):
        filepath = os.path.join(upload_folder, filename)
        # Get file creation time
        file_time = os.path.getctime(filepath)
        if current_time - file_time > one_hour:
            try:
                os.remove(filepath)
                print(f"Deleted old file: {filename}")
            except Exception as e:
                print(f"Error deleting file {filename}: {e}")

def delete_unsubmitted_exams(exam_repo):
    """Delete exams that are not submitted and older than 7 days."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

    # For both class 9 and class 10 exams
    for is_class10 in [False, True]:
        col = exam_repo._col_by_params(is_class10=is_class10)

        # Primary path: indexed date comparison.
        result = col.delete_many(
            {
                "is_submitted": False,
                "timestamp_dt": {"$lt": cutoff_date},
            }
        )
        if result.deleted_count:
            print(f"Deleted {result.deleted_count} unsubmitted exams (timestamp_dt) for class10={is_class10}")

        # Legacy fallback for documents missing timestamp_dt.
        legacy_exams = col.find(
            {
                "is_submitted": False,
                "timestamp_dt": {"$exists": False},
            },
            {"exam-id": 1, "timestamp": 1},
        )
        for exam in legacy_exams:
            timestamp_str = exam.get("timestamp")
            if not timestamp_str:
                continue
            try:
                exam_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
            except Exception:
                continue
            if exam_timestamp >= cutoff_date:
                continue
            exam_repo.delete_exam(exam["exam-id"], is_class10)
