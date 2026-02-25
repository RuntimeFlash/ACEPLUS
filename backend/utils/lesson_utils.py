import os
from typing import List
from utils.data_utils import load_json_file

def lesson2filepath(subject, lesson, class10=False):
    subject_lower = subject.lower()
    if subject != "SS":
        lesson_number = lesson[0]
    base_folder = "lessons10" if class10 else "lessons"
    if subject == "SS":
        lesson_number=lesson[1]
        prefix = lesson[0]
        rel_path = f"{base_folder}/{subject_lower}/{prefix}.{lesson_number}.json"
    elif subject == "Science":
        rel_path = f"{base_folder}/{subject_lower}/lesson-{lesson_number}.json"
    elif subject == "Math":
        rel_path = f"{base_folder}/{subject_lower}/lesson{lesson_number}.json"
    else:
        rel_path = f"{base_folder}/{subject_lower}/lesson{lesson_number}.json"

    # Primary source is Mongo static content.
    return f"mongo://{rel_path}"


def get_all_lessons_for_subject(subject: str, class10: bool = False) -> List[str]:
    """Fetches all lessons for a given subject from the data files."""
    lessons_file = "lessons10.json" if class10 else "lessons.json"
    lessons = load_json_file(lessons_file) or {}
    return lessons.get(subject, [])


def get_all_subjects(class10: bool = False) -> List[str]:
    """Fetches all subjects from the data files."""
    lessons_file = "lessons10.json" if class10 else "lessons.json"
    lessons = load_json_file(lessons_file) or {}
    return list(lessons.keys())
