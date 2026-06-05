"""
SmartGPA – fake_db.py (Compatibility Wrapper)
Toàn bộ logic đã chuyển sang real_db.py.
File này chỉ re-export để các module cũ không bị lỗi import.
"""
from app.db.real_db import (
    USERS_DB,
    BLACKLIST,
    PASSWORD_RESET_OTPS,
    COURSES_DB,
    ASSIGNMENTS_DB,
    ACTIVITY_LOGS,
    TIMELINE_UPDATES,
    WARNING_ACTIONS,
    SCORE_HISTORY_DB,
    PROJECT_INFO,
    GRADING_RULES_DB,
    CURRENT_SEMESTER,
    DEPARTMENTS_DB,
    INSTITUTES_DB,
    MAJORS_DB,
    find_user_by_login,
    user_login_key,
    build_student_username,
)

__all__ = [
    "USERS_DB", "BLACKLIST", "PASSWORD_RESET_OTPS",
    "COURSES_DB", "ASSIGNMENTS_DB",
    "ACTIVITY_LOGS", "TIMELINE_UPDATES", "WARNING_ACTIONS",
    "SCORE_HISTORY_DB", "PROJECT_INFO", "GRADING_RULES_DB",
    "CURRENT_SEMESTER", "DEPARTMENTS_DB", "INSTITUTES_DB", "MAJORS_DB",
    "find_user_by_login", "user_login_key", "build_student_username",
]
