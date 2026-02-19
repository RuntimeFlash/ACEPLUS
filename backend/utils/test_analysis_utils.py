import json
from typing import Dict, Any, Optional, List
from db import exam_repo, test_repo
from utils.data_utils import load_json_file

def get_test_analysis_data(test_id: str, current_user: str, is_class10: bool, division: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive test analysis data for a given test.

    Args:
        test_id: The ID of the test to analyze
        current_user: The user ID of the teacher requesting analysis
        is_class10: Whether this is for class 10 students
        division: Optional division filter (A, B, C, D) or "non_participants"

    Returns:
        Dictionary containing test analysis data or None if unauthorized/not found
    """

    # Verify teacher access
    teachers_data = load_json_file("teachers.json")
    if not teachers_data or current_user not in teachers_data:
        return None

    # Get the test data
    test_data = test_repo.get_test(test_id, is_class10)
    if not test_data:
        return None

    # Verify the teacher created this test
    if test_data.get("created_by") != current_user:
        return None

    # Get all exams for this test
    standard = 10 if is_class10 else 9
    exam_col = exam_repo._col_by_params(standard=standard)

    # Find all exams for this test
    test_exams = list(exam_col.find({
        "test": True,
        "exam-id": {"$regex": f"^{test_id}-"},
        "is_submitted": True
    }))

    # Get student data for the standard
    student_info = json.loads(open("data/class10_students.json").read()) if is_class10 else json.loads(open("data/students.json").read())

    # Calculate statistics
    class_stats = {}
    student_performance = []
    completed_students = set()
    
    # Initialize question-wise statistics
    total_questions = len(test_data.get("questions", []))
    question_stats = []
    for i in range(total_questions):
        question_stats.append({
            "question_number": i + 1,
            "correct_count": 0,
            "total_count": 0,
            "percentage": 0.0
        })

    for exam in test_exams:
        user_id = exam["userId"]
        completed_students.add(user_id)

        # Get student info
        student_info_data = student_info.get(user_id, {})
        student_name = student_info_data.get("name", "Unknown")
        student_div = student_info_data.get("div", "Unknown")

        # Calculate score
        score = exam.get("score", 0)
        # total_questions is already defined above
        percentage = exam.get("percentage", 0)

        student_record = {
            "user_id": user_id,
            "name": student_name,
            "division": student_div,
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage
        }
        
        # Update question-wise statistics
        results = exam.get("results", [])
        for i, result in enumerate(results):
            if i < len(question_stats):
                question_stats[i]["total_count"] += 1
                if result.get("is_correct", False):
                    question_stats[i]["correct_count"] += 1

        # If division filter is specified, only include students from that division
        # For non_participants view, we'll filter later
        if division is None or division == "non_participants" or student_div == division:
            student_performance.append(student_record)

        # Update class statistics (only for overall view or division-specific view)
        if division is None or division == student_div:
            if student_div not in class_stats:
                class_stats[student_div] = {
                    "total_students": 0,
                    "total_score": 0,
                    "total_percentage": 0,
                    "scores": []
                }

            class_stats[student_div]["total_students"] += 1
            class_stats[student_div]["total_score"] += score
            class_stats[student_div]["total_percentage"] += percentage
            class_stats[student_div]["scores"].append(score)

    # Calculate class averages
    for div, stats in class_stats.items():
        if stats["total_students"] > 0:
            stats["average_score"] = round(stats["total_score"] / stats["total_students"], 2)
            stats["average_percentage"] = round(stats["total_percentage"] / stats["total_students"], 2)
            stats["highest_score"] = max(stats["scores"])
            stats["lowest_score"] = min(stats["scores"])

    # Find non-participating students
    assigned_students = test_data.get("students", [])
    assigned_division = test_data.get("division")

    all_non_participating = []

    if assigned_students:
        # Specific students were assigned
        for student_id in assigned_students:
            if student_id not in completed_students:
                student_info_data = student_info.get(student_id, {})
                all_non_participating.append({
                    "user_id": student_id,
                    "name": student_info_data.get("name", "Unknown"),
                    "division": student_info_data.get("div", "Unknown")
                })
    elif assigned_division:
        # All students in a division were assigned
        for student_id, student_info_data in student_info.items():
            if student_info_data.get("div") == assigned_division and student_id not in completed_students:
                all_non_participating.append({
                    "user_id": student_id,
                    "name": student_info_data.get("name", "Unknown"),
                    "division": student_info_data.get("div", "Unknown")
                })
    else:
        # All students were assigned (no specific assignment)
        for student_id, student_info_data in student_info.items():
            if student_id not in completed_students:
                all_non_participating.append({
                    "user_id": student_id,
                    "name": student_info_data.get("name", "Unknown"),
                    "division": student_info_data.get("div", "Unknown")
                })

    # Filter non-participating students by division if needed
    non_participating = []
    if division == "non_participants":
        non_participating = all_non_participating
    elif division is not None:
        # Filter non-participating students by specific division
        non_participating = [student for student in all_non_participating if student["division"] == division]
    else:
        # For overall view, show all non-participating students
        non_participating = all_non_participating
    
    # Calculate question percentages
    for question in question_stats:
        if question["total_count"] > 0:
            question["percentage"] = round((question["correct_count"] / question["total_count"]) * 100, 2)
    
    # Calculate overall statistics
    total_participants = len(student_performance)
    if total_participants > 0:
        overall_stats = {
            "total_participants": total_participants,
            "total_non_participants": len(non_participating),
            "average_score": round(sum(p["score"] for p in student_performance) / total_participants, 2),
            "average_percentage": round(sum(p["percentage"] for p in student_performance) / total_participants, 2),
            "highest_score": max(p["score"] for p in student_performance),
            "lowest_score": min(p["score"] for p in student_performance)
        }
    else:
        overall_stats = {
            "total_participants": 0,
            "total_non_participants": len(non_participating),
            "average_score": 0,
            "average_percentage": 0,
            "highest_score": 0,
            "lowest_score": 0
        }

    # Sort student performance by percentage (descending)
    student_performance.sort(key=lambda x: x["percentage"], reverse=True)

    # If requesting a specific division view, filter class_stats to only include that division
    if division is not None and division != "non_participants" and division in class_stats:
        filtered_class_stats = {division: class_stats[division]}
    elif division is not None and division != "non_participants":
        # Division specified but no data for it
        filtered_class_stats = {}
    else:
        # For overall view or non_participants view, show all class stats
        filtered_class_stats = class_stats

    return {
        "test_info": {
            "test_id": test_id,
            "test_name": test_data.get("test_name"),
            "subject": test_data.get("subject"),
            "standard": test_data.get("standard"),
            "total_questions": len(test_data.get("questions", []))
        },
        "overall_stats": overall_stats,
        "class_stats": filtered_class_stats,
        "student_performance": student_performance,
        "non_participating": non_participating,
        "question_stats": question_stats
    }