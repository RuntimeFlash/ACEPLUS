import json
import os

def _default_data_root():
    configured = os.getenv("BACKEND_DATA_DIR")
    if configured:
        return configured
    backend_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    repo_root = os.path.dirname(backend_dir)
    return os.path.join(repo_root, "Legacy Json Qs")

def load_json_file(filename, data_path="data"):
    try:
        from db import static_content_repo

        mongo_content = static_content_repo.get_json(filename)
        if mongo_content is not None:
            return mongo_content
    except Exception:
        # Keep local-file fallback for migration/bootstrap scenarios.
        pass

    if os.path.isabs(data_path):
        base_dir = data_path
    else:
        default_root = _default_data_root()
        normalized_data_path = str(data_path).replace("\\", "/").strip().strip("/")
        if normalized_data_path in ("", "data", "./data", "backend/data"):
            base_dir = default_root
        else:
            base_dir = os.path.join(default_root, normalized_data_path)

    full_path = os.path.normpath(os.path.join(base_dir, filename))
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        print(f"Current working directory: {os.getcwd()}")
        return None

def calculate_lesson_analytics(questions, selected_answers):
    """
    Calculate per-lesson analytics using l-id or lesson field from questions

    Args:
        questions: List of question dictionaries containing l-id or lesson
        selected_answers: List of user's selected answers

    Returns:
        dict: Lesson-wise analytics with scores and details
    """
    lesson_analytics = {}

    for i, (question, selected_answer) in enumerate(zip(questions, selected_answers)):
        if "l-id" in question:
            lesson_id = question["l-id"].split("Q")[0]
        elif "lesson" in question:
            lesson_id = f"L{question['lesson']}"
        else:
            print(f"Skipping question {i+1}: No lesson identification")
            continue

        if lesson_id not in lesson_analytics:
            lesson_analytics[lesson_id] = {
                "lesson_name": f"Lesson {lesson_id[1:]}",
                "questions_total": 0,
                "questions_correct": 0,
                "percentage": 0,
            }

        lesson_analytics[lesson_id]["questions_total"] += 1
        if selected_answer["option"] == question.get("answer"):
            lesson_analytics[lesson_id]["questions_correct"] += 1

    for lesson_id, lesson in lesson_analytics.items():
        lesson["percentage"] = (
            lesson["questions_correct"] / lesson["questions_total"]
        ) * 100

    return lesson_analytics

def decode_unicode(obj):
    if isinstance(obj, str):
        try:
            decoded = json.loads(f'"{obj}"')
            return decoded
        except json.JSONDecodeError as e:
            print(f"Failed to decode string: {obj} : {e}")
            return obj
    elif isinstance(obj, dict):
        return {
            decode_unicode(key): decode_unicode(value) for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [decode_unicode(element) for element in obj]
    return obj
