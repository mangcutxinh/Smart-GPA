from __future__ import annotations
"""
SmartGPA – Admin Router
Endpoints quản lý học kỳ, danh sách môn học, phân công giảng viên.
Chỉ Admin mới có quyền truy cập.
"""
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
import os
from uuid import uuid4
from datetime import datetime, timezone

from app.core.dependencies import require_role
from app.core.security import hash_password
from app.models.schemas import (
    UserRole,
    SemesterConfig, SemesterOut,
    CourseConfig,
    AssignmentConfig, AssignmentOut,
    UnitConfig, MajorConfig,
    UserCreate, UserOut, LecturerUpdate,
    ProjectInfoUpdate, TimelineUpdateCreate, AdminGradeUpdate,
    WarningSendRequest, GradingRulesUpdate
)
from app.db.real_db import (
    CURRENT_SEMESTER, COURSES_DB, ASSIGNMENTS_DB, USERS_DB,
    DEPARTMENTS_DB, INSTITUTES_DB, MAJORS_DB,
    ACTIVITY_LOGS, PROJECT_INFO, TIMELINE_UPDATES, WARNING_ACTIONS,
    SCORE_HISTORY_DB, GRADING_RULES_DB
)
from app.db.databricks_db import MOCK_GOLD_DB, sync_gold_to_silver

router = APIRouter(prefix="/admin", tags=["Admin Management"])

_admin_dep = Depends(require_role(UserRole.ADMIN))


def _save_db():
    try:
        from app.db.persistence import save_db_to_disk
        save_db_to_disk()
    except Exception as e:
        import logging
        logging.getLogger("smartgpa.admin").error(f"Loi khi sao luu database: {e}")



def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _append_admin_event(actor: UserOut, action: str, subject_id: str, subject_name: str, details: str) -> dict:
    event = {
        "id": f"act_{uuid4().hex[:8]}",
        "actor_email": actor.email,
        "actor_name": actor.full_name,
        "action": action,
        "subject_id": subject_id,
        "subject_name": subject_name,
        "details": details,
        "timestamp": _now_str(),
    }
    ACTIVITY_LOGS.append(event)
    TIMELINE_UPDATES.append({
        "id": f"tl_{uuid4().hex[:8]}",
        "title": subject_name,
        "category": action,
        "details": details,
        "actor_email": actor.email,
        "timestamp": event["timestamp"],
    })
    _save_db()
    return event


@router.get("/overview", summary="Tong quan quan tri toan bo du an")
def get_admin_overview(current_user: UserOut = _admin_dep):
    lecturers = [u for u in USERS_DB.values() if u.get("role") == "lecturer"]
    students = [u for u in USERS_DB.values() if u.get("role") == "student"]
    warnings_count = sum(1 for r in MOCK_GOLD_DB.values() if r.get("status_canh_bao") == "Nguy co")
    return {
        "project": PROJECT_INFO,
        "counts": {
            "students": len(students),
            "lecturers": len(lecturers),
            "admins": sum(1 for u in USERS_DB.values() if u.get("role") == "admin"),
            "courses": len(COURSES_DB),
            "assignments": len(ASSIGNMENTS_DB),
            "score_records": len(MOCK_GOLD_DB),
            "warnings": warnings_count,
            "timeline_updates": len(TIMELINE_UPDATES),
            "score_history_events": len(SCORE_HISTORY_DB),
        },
        "current_semester": CURRENT_SEMESTER,
        "latest_updates": list(reversed(TIMELINE_UPDATES))[:10],
    }


@router.get("/project-info", summary="Lay thong tin tong quan du an")
def get_project_info(current_user: UserOut = _admin_dep):
    return PROJECT_INFO


@router.put("/project-info", summary="Cap nhat thong tin tong quan du an")
def update_project_info(body: ProjectInfoUpdate, current_user: UserOut = _admin_dep):
    updates = body.model_dump(exclude_none=True)
    PROJECT_INFO.update(updates)
    PROJECT_INFO["last_updated"] = datetime.now(timezone.utc).isoformat()
    event = _append_admin_event(current_user, "project_update", "project", "Cap nhat thong tin du an", str(updates))
    return {"project": PROJECT_INFO, "event": event}


@router.get("/timeline", summary="Lay timeline cap nhat du an")
def get_timeline(category: str | None = None, current_user: UserOut = _admin_dep):
    rows = TIMELINE_UPDATES
    if category:
        rows = [r for r in rows if r.get("category") == category]
    return list(reversed(rows))


@router.post("/timeline", summary="Them moc timeline cap nhat")
def add_timeline_update(body: TimelineUpdateCreate, current_user: UserOut = _admin_dep):
    item = {
        "id": f"tl_{uuid4().hex[:8]}",
        "title": body.title,
        "category": body.category,
        "details": body.details,
        "actor_email": current_user.email,
        "timestamp": _now_str(),
    }
    TIMELINE_UPDATES.append(item)
    return item


@router.get("/users", summary="Quan ly toan bo tai khoan nguoi dung")
def get_users(role: str | None = None, current_user: UserOut = _admin_dep):
    users = []
    for user in USERS_DB.values():
        if role and user.get("role") != role:
            continue
        users.append({k: v for k, v in user.items() if k != "password_hash"})
    return users


# ─── SEMESTER ─────────────────────────────────────────────────

@router.get("/semester", response_model=SemesterOut, summary="Lấy học kỳ hiện tại")
def get_semester(_=_admin_dep):
    return CURRENT_SEMESTER


@router.put("/semester", response_model=SemesterOut, summary="Cập nhật học kỳ")
def update_semester(body: SemesterConfig, _=_admin_dep):
    CURRENT_SEMESTER["ma_hoc_ky"] = body.ma_hoc_ky.strip()
    CURRENT_SEMESTER["nam_hoc"] = body.nam_hoc.strip()
    CURRENT_SEMESTER["display"] = f"{body.ma_hoc_ky.strip()} {body.nam_hoc.strip()}"
    _save_db()
    return CURRENT_SEMESTER


@router.post("/semester/reset", response_model=dict, summary="Reset phân công cho học kỳ mới")
def reset_semester(body: SemesterConfig, _=_admin_dep):
    """Cập nhật học kỳ mới và xóa toàn bộ phân công cũ (giữ danh sách môn học)."""
    CURRENT_SEMESTER["ma_hoc_ky"] = body.ma_hoc_ky.strip()
    CURRENT_SEMESTER["nam_hoc"] = body.nam_hoc.strip()
    CURRENT_SEMESTER["display"] = f"{body.ma_hoc_ky.strip()} {body.nam_hoc.strip()}"
    ASSIGNMENTS_DB.clear()
    _save_db()
    return {"message": f"Đã chuyển sang học kỳ mới: {CURRENT_SEMESTER['display']}. Toàn bộ phân công đã được xóa.", "hoc_ky": CURRENT_SEMESTER["display"]}


# ─── COURSES ──────────────────────────────────────────────────

@router.get("/courses", summary="Lấy danh sách môn học")
def get_courses(_=_admin_dep):
    return COURSES_DB


@router.post("/courses/import", summary="Nhập khẩu danh sách môn học từ file chương trình khung (.csv)")
def import_courses(file: UploadFile = File(...), _=_admin_dep):
    # Check extension
    filename = file.filename or ""
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext != ".csv":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Định dạng file không hợp lệ. Chỉ chấp nhận file chương trình khung định dạng .csv"
        )
        
    try:
        contents = file.file.read()
        decoded = contents.decode("utf-8-sig")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Không thể đọc mã hóa của file: {str(e)}"
        )
        
    reader = csv.DictReader(io.StringIO(decoded))
    headers = [h.strip() for h in reader.fieldnames or []]
    
    required_cols = ["id", "name", "type", "credits"]
    missing_cols = [col for col in required_cols if col not in headers]
    if missing_cols:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Thiếu các cột bắt buộc trong file CSV: {', '.join(missing_cols)}"
        )
        
    imported_count = 0
    errors = []
    import csv as csv_mod
    import io as io_mod
    
    for idx, row in enumerate(reader, start=2):
        try:
            cid = (row.get("id") or "").strip()
            name = (row.get("name") or "").strip()
            ctype = (row.get("type") or "").strip().lower()
            credits_str = (row.get("credits") or "").strip()
            
            if not cid or not name or not ctype or not credits_str:
                errors.append(f"Dòng {idx}: Thiếu thông tin bắt buộc (mã môn, tên môn, loại hoặc số TC).")
                continue
                
            if ctype not in ["ly_thuyet", "thuc_hanh", "tich_hop"]:
                errors.append(f"Dòng {idx}: Loại học phần '{ctype}' không hợp lệ. Phải là ly_thuyet, thuc_hanh hoặc tich_hop.")
                continue
                
            credits_val = int(credits_str)
            chi_lt = int(row.get("chi_lt") or (credits_val if ctype == "ly_thuyet" else 0))
            chi_th = int(row.get("chi_th") or (credits_val if ctype == "thuc_hanh" else 0))
            faculty_id = (row.get("faculty_id") or "").strip() or None
            major_id = (row.get("major_id") or "").strip() or None
            
            # Check duplicate course ID
            dup_found = False
            for c in COURSES_DB:
                if c["id"] == cid:
                    c["name"] = name
                    c["type"] = ctype
                    c["credits"] = credits_val
                    c["chi_lt"] = chi_lt
                    c["chi_th"] = chi_th
                    c["faculty_id"] = faculty_id
                    c["major_id"] = major_id
                    dup_found = True
                    break
                    
            if not dup_found:
                COURSES_DB.append({
                    "id": cid,
                    "name": name,
                    "type": ctype,
                    "credits": credits_val,
                    "chi_lt": chi_lt,
                    "chi_th": chi_th,
                    "faculty_id": faculty_id,
                    "major_id": major_id,
                    "is_compulsory": row.get("is_compulsory", "true").strip().lower() in ["true", "1", "yes"]
                })
            imported_count += 1
            
        except Exception as ex:
            errors.append(f"Dòng {idx}: Lỗi định dạng dữ liệu ({str(ex)})")
            
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Dữ liệu tệp chứa một số dòng lỗi.", "errors": errors[:15]}
        )
        
    _save_db()
    return {
        "message": f"Nhập tệp chương trình khung thành công! Đã đồng bộ {imported_count} môn học.",
        "imported_count": imported_count
    }


@router.post("/courses", summary="Thêm môn học mới")
def add_course(body: CourseConfig, _=_admin_dep):
    # Kiểm tra trùng mã môn
    if any(c["id"] == body.id for c in COURSES_DB):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã môn '{body.id}' đã tồn tại."
        )
    course = body.model_dump()
    COURSES_DB.append(course)
    _save_db()
    return {"message": f"Đã thêm môn học '{body.name}' ({body.id}) thành công.", "course": course}


@router.put("/courses/{course_id}", summary="Cập nhật môn học")
def update_course(course_id: str, body: CourseConfig, _=_admin_dep):
    for i, c in enumerate(COURSES_DB):
        if c["id"] == course_id:
            COURSES_DB[i] = body.model_dump()
            _save_db()
            return {"message": f"Đã cập nhật môn '{course_id}'.", "course": COURSES_DB[i]}
    raise HTTPException(status_code=404, detail=f"Không tìm thấy môn '{course_id}'.")


@router.delete("/courses/{course_id}", summary="Xóa môn học")
def delete_course(course_id: str, _=_admin_dep):
    for i, c in enumerate(COURSES_DB):
        if c["id"] == course_id:
            COURSES_DB.pop(i)
            # Xóa các phân công liên quan
            to_remove = [a for a in ASSIGNMENTS_DB if a["ma_mon"] == course_id]
            for a in to_remove:
                ASSIGNMENTS_DB.remove(a)
            _save_db()
            return {"message": f"Đã xóa môn '{course_id}' và {len(to_remove)} phân công liên quan."}
    raise HTTPException(status_code=404, detail=f"Không tìm thấy môn '{course_id}'.")


# ─── ASSIGNMENTS ──────────────────────────────────────────────

@router.get("/assignments", summary="Lấy danh sách phân công")
def get_assignments(lecturer_id: str = None, _=_admin_dep):
    if lecturer_id:
        return [a for a in ASSIGNMENTS_DB if a["lecturer_id"] == lecturer_id]
    return ASSIGNMENTS_DB


@router.post("/assignments", response_model=AssignmentOut, summary="Thêm phân công giảng viên")
def add_assignment(body: AssignmentConfig, _=_admin_dep):
    # Kiểm tra môn tồn tại
    if not any(c["id"] == body.ma_mon for c in COURSES_DB):
        raise HTTPException(status_code=400, detail=f"Môn '{body.ma_mon}' không tồn tại trong danh sách.")
    # Kiểm tra giảng viên tồn tại
    lecturer_found = any(
        u.get("lecturer_id") == body.lecturer_id
        for u in USERS_DB.values()
    )
    if not lecturer_found:
        raise HTTPException(status_code=400, detail=f"Giảng viên '{body.lecturer_id}' không tồn tại.")
    # Kiểm tra trùng phân công
    if any(
        a["lecturer_id"] == body.lecturer_id and
        a["ma_mon"] == body.ma_mon and
        a["ma_lop"] == body.ma_lop
        for a in ASSIGNMENTS_DB
    ):
        raise HTTPException(status_code=400, detail="Phân công này đã tồn tại.")

    assignment = {
        "id": f"asgn_{str(uuid4())[:8]}",
        "lecturer_id": body.lecturer_id,
        "ma_mon": body.ma_mon,
        "ma_lop": body.ma_lop,
        "hoc_ky": CURRENT_SEMESTER["display"]
    }
    ASSIGNMENTS_DB.append(assignment)
    _save_db()
    return assignment


@router.delete("/assignments/{assignment_id}", summary="Xóa phân công")
def delete_assignment(assignment_id: str, _=_admin_dep):
    for i, a in enumerate(ASSIGNMENTS_DB):
        if a["id"] == assignment_id:
            ASSIGNMENTS_DB.pop(i)
            _save_db()
            return {"message": f"Đã xóa phân công '{assignment_id}'."}
    raise HTTPException(status_code=404, detail=f"Không tìm thấy phân công '{assignment_id}'.")


# ─── LECTURER INFO (Public-ish for frontend) ──────────────────

@router.get("/lecturers", summary="Lấy danh sách giảng viên (để hiển thị phân công)")
def get_lecturers(_=_admin_dep):
    return [
        {"lecturer_id": u["lecturer_id"], "full_name": u["full_name"], "email": u["email"], "faculty_id": u.get("faculty_id")}
        for u in USERS_DB.values()
        if u.get("role") == "lecturer" and u.get("lecturer_id")
    ]


@router.post("/lecturers", response_model=UserOut, summary="Thêm giảng viên mới")
def add_lecturer(body: UserCreate, current_user: UserOut = _admin_dep):
    if body.role != UserRole.LECTURER:
        raise HTTPException(status_code=400, detail="Endpoint nay chi tao tai khoan giang vien.")

    # Check email duplicate
    if body.email in USERS_DB:
        raise HTTPException(status_code=400, detail="Email này đã tồn tại trên hệ thống.")
    
    # Lecturer ID duplicate check
    if not body.lecturer_id:
        raise HTTPException(status_code=400, detail="Yêu cầu nhập Mã giảng viên (lecturer_id).")
    
    if any(u.get("lecturer_id") == body.lecturer_id for u in USERS_DB.values()):
        raise HTTPException(status_code=400, detail=f"Mã giảng viên '{body.lecturer_id}' đã được sử dụng.")
        
    # Faculty exist check (must be one of 15 departments or 4 institutes)
    if body.faculty_id:
        faculty_exists = any(d["id"] == body.faculty_id for d in DEPARTMENTS_DB) or any(v["id"] == body.faculty_id for v in INSTITUTES_DB)
        if not faculty_exists:
            raise HTTPException(status_code=400, detail=f"Khoa/Viện '{body.faculty_id}' không tồn tại.")

    new_user = {
        "id": str(uuid4()),
        "email": body.email,
        "username": body.email,
        "password_hash": hash_password(body.password),
        "full_name": body.full_name,
        "role": "lecturer",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "lecturer_id": body.lecturer_id,
        "faculty_id": body.faculty_id,
        "notifications": [],
        "must_change_password": False,
        "email_verified": True,
    }
    USERS_DB[body.email] = new_user
    _append_admin_event(current_user, "lecturer_create", body.lecturer_id, body.full_name, f"Them tai khoan giang vien {body.email}")
    return new_user


@router.put("/lecturers/{lecturer_id}", response_model=UserOut, summary="Cập nhật giảng viên")
def update_lecturer(lecturer_id: str, body: LecturerUpdate, current_user: UserOut = _admin_dep):
    # Find user
    target_user = None
    target_email = None
    for email, u in USERS_DB.items():
        if u.get("role") == "lecturer" and u.get("lecturer_id") == lecturer_id:
            target_user = u
            target_email = email
            break
            
    if not target_user:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy giảng viên '{lecturer_id}'.")
        
    # Check email duplicate if changed
    if body.email != target_email and body.email in USERS_DB:
        raise HTTPException(status_code=400, detail="Email mới đã được sử dụng bởi người dùng khác.")
        
    # Faculty exist check
    if body.faculty_id:
        faculty_exists = any(d["id"] == body.faculty_id for d in DEPARTMENTS_DB) or any(v["id"] == body.faculty_id for v in INSTITUTES_DB)
        if not faculty_exists:
            raise HTTPException(status_code=400, detail=f"Khoa/Viện '{body.faculty_id}' không tồn tại.")
            
    # Update fields
    target_user["full_name"] = body.full_name
    target_user["email"] = body.email
    target_user["username"] = body.email
    target_user["faculty_id"] = body.faculty_id
    
    # If email changed, we must re-key USERS_DB
    if body.email != target_email:
        USERS_DB[body.email] = USERS_DB.pop(target_email)
    _append_admin_event(current_user, "lecturer_update", lecturer_id, body.full_name, f"Cap nhat tai khoan giang vien {lecturer_id}")
        
    return target_user


@router.delete("/lecturers/{lecturer_id}", summary="Xóa giảng viên")
def delete_lecturer(lecturer_id: str, current_user: UserOut = _admin_dep):
    target_email = None
    for email, u in USERS_DB.items():
        if u.get("role") == "lecturer" and u.get("lecturer_id") == lecturer_id:
            target_email = email
            break
            
    if not target_email:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy giảng viên '{lecturer_id}'.")
        
    # Remove assignments
    to_remove = [a for a in ASSIGNMENTS_DB if a["lecturer_id"] == lecturer_id]
    for a in to_remove:
        ASSIGNMENTS_DB.remove(a)
        
    deleted_user = USERS_DB.pop(target_email)
    _append_admin_event(current_user, "lecturer_delete", lecturer_id, deleted_user.get("full_name", lecturer_id), f"Xoa tai khoan giang vien {target_email}; xoa {len(to_remove)} phan cong")
    return {"message": f"Đã xóa giảng viên '{lecturer_id}' và {len(to_remove)} phân công liên quan thành công."}

from pydantic import BaseModel, EmailStr
from typing import Optional

class StudentCreateBody(BaseModel):
    student_id: str
    email: EmailStr
    password: str = "Sv@123"
    full_name: str
    faculty_id: Optional[str] = "CNTT"
    major_id: Optional[str] = "KHDL"
    lop_hoc: Optional[str] = "DHKHDL19A"
    gioi_tinh: Optional[str] = "Nam"
    ngay_sinh: Optional[str] = ""

class StudentUpdateBody(BaseModel):
    email: EmailStr
    full_name: str
    faculty_id: Optional[str] = None
    major_id: Optional[str] = None
    lop_hoc: Optional[str] = None
    gioi_tinh: Optional[str] = None
    ngay_sinh: Optional[str] = None
    is_active: Optional[bool] = None

# ─── STUDENT INFO CRUD ────────────────────────────────────────

@router.get("/students", summary="Lấy danh sách sinh viên")
def get_students(_=_admin_dep):
    return [
        {
            "id": u["id"],
            "student_id": u["student_id"],
            "full_name": u["full_name"],
            "email": u["email"],
            "username": u["username"],
            "faculty_id": u.get("faculty_id"),
            "major_id": u.get("major_id"),
            "lop_hoc": u.get("lop_hoc"),
            "gioi_tinh": u.get("gioi_tinh"),
            "ngay_sinh": u.get("ngay_sinh"),
            "is_active": u.get("is_active", True)
        }
        for u in USERS_DB.values()
        if u.get("role") == "student" and u.get("student_id")
    ]


@router.post("/students", response_model=UserOut, summary="Thêm sinh viên mới")
def add_student(body: StudentCreateBody, current_user: UserOut = _admin_dep):
    if body.email in USERS_DB:
        raise HTTPException(status_code=400, detail="Email này đã tồn tại trên hệ thống.")
    
    if any(u.get("student_id") == body.student_id for u in USERS_DB.values()):
        raise HTTPException(status_code=400, detail=f"Mã sinh viên '{body.student_id}' đã tồn tại.")

    username = body.student_id.lower()
    if username in USERS_DB:
         raise HTTPException(status_code=400, detail=f"Username '{username}' đã tồn tại.")

    new_user = {
        "id": str(uuid4()),
        "email": body.email,
        "username": username,
        "password_hash": hash_password(body.password),
        "full_name": body.full_name,
        "role": "student",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "student_id": body.student_id,
        "faculty_id": body.faculty_id,
        "major_id": body.major_id,
        "lop_hoc": body.lop_hoc,
        "gioi_tinh": body.gioi_tinh,
        "ngay_sinh": body.ngay_sinh,
        "notifications": [],
        "must_change_password": False,
        "email_verified": True,
    }
    USERS_DB[username] = new_user
    _append_admin_event(current_user, "student_create", body.student_id, body.full_name, f"Them tai khoa sinh vien {body.email}")
    return new_user


@router.put("/students/{student_id}", response_model=UserOut, summary="Cập nhật sinh viên")
def update_student(student_id: str, body: StudentUpdateBody, current_user: UserOut = _admin_dep):
    target_user = None
    target_username = None
    for username, u in USERS_DB.items():
        if u.get("role") == "student" and u.get("student_id") == student_id:
            target_user = u
            target_username = username
            break
            
    if not target_user:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy sinh viên '{student_id}'.")
        
    if body.email != target_user.get("email") and body.email in USERS_DB:
        raise HTTPException(status_code=400, detail="Email mới đã được sử dụng bởi người dùng khác.")
        
    target_user["full_name"] = body.full_name
    target_user["email"] = body.email
    if body.faculty_id is not None:
        target_user["faculty_id"] = body.faculty_id
    if body.major_id is not None:
        target_user["major_id"] = body.major_id
    if body.lop_hoc is not None:
        target_user["lop_hoc"] = body.lop_hoc
    if body.gioi_tinh is not None:
        target_user["gioi_tinh"] = body.gioi_tinh
    if body.ngay_sinh is not None:
        target_user["ngay_sinh"] = body.ngay_sinh
    if body.is_active is not None:
        target_user["is_active"] = body.is_active
    
    _append_admin_event(current_user, "student_update", student_id, body.full_name, f"Cap nhat tai khoan sinh vien {student_id}")
    return target_user


@router.delete("/students/{student_id}", summary="Xóa sinh viên")
def delete_student(student_id: str, current_user: UserOut = _admin_dep):
    target_username = None
    for username, u in USERS_DB.items():
        if u.get("role") == "student" and u.get("student_id") == student_id:
            target_username = username
            break
            
    if not target_username:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy sinh viên '{student_id}'.")
        
    keys_to_delete = [k for k in MOCK_GOLD_DB if isinstance(k, tuple) and k[0] == student_id]
    for k in keys_to_delete:
        MOCK_GOLD_DB.pop(k, None)
        
    deleted_user = USERS_DB.pop(target_username)
    _append_admin_event(current_user, "student_delete", student_id, deleted_user.get("full_name", student_id), f"Xoa tai khoan sinh vien {student_id}; xoa {len(keys_to_delete)} ban ghi diem")
    return {"message": f"Đã xóa sinh viên '{student_id}' và {len(keys_to_delete)} bản ghi điểm liên quan thành công."}


# ─── DEPARTMENTS ──────────────────────────────────────────────

@router.get("/departments", summary="Lấy danh sách khoa")
def get_departments(_=_admin_dep):
    return DEPARTMENTS_DB


@router.post("/departments", summary="Thêm khoa mới")
def add_department(body: UnitConfig, _=_admin_dep):
    if any(d["id"] == body.id for d in DEPARTMENTS_DB):
        raise HTTPException(status_code=400, detail=f"Mã khoa '{body.id}' đã tồn tại.")
    dept = body.model_dump()
    DEPARTMENTS_DB.append(dept)
    _save_db()
    return dept


@router.put("/departments/{dept_id}", summary="Cập nhật thông tin khoa")
def update_department(dept_id: str, body: UnitConfig, _=_admin_dep):
    for i, d in enumerate(DEPARTMENTS_DB):
        if d["id"] == dept_id:
            DEPARTMENTS_DB[i] = body.model_dump()
            _save_db()
            return DEPARTMENTS_DB[i]
    raise HTTPException(status_code=404, detail=f"Không tìm thấy khoa '{dept_id}'.")


@router.delete("/departments/{dept_id}", summary="Xóa khoa")
def delete_department(dept_id: str, _=_admin_dep):
    for i, d in enumerate(DEPARTMENTS_DB):
        if d["id"] == dept_id:
            DEPARTMENTS_DB.pop(i)
            # Remove linked majors
            to_remove_majors = [m for m in MAJORS_DB if m["faculty_id"] == dept_id]
            for m in to_remove_majors:
                MAJORS_DB.remove(m)
            _save_db()
            return {"message": f"Đã xóa khoa '{dept_id}' và {len(to_remove_majors)} ngành học trực thuộc."}
    raise HTTPException(status_code=404, detail=f"Không tìm thấy khoa '{dept_id}'.")


# ─── INSTITUTES ───────────────────────────────────────────────

@router.get("/institutes", summary="Lấy danh sách viện")
def get_institutes(_=_admin_dep):
    return INSTITUTES_DB


@router.post("/institutes", summary="Thêm viện mới")
def add_institute(body: UnitConfig, _=_admin_dep):
    if any(v["id"] == body.id for v in INSTITUTES_DB):
        raise HTTPException(status_code=400, detail=f"Mã viện '{body.id}' đã tồn tại.")
    inst = body.model_dump()
    INSTITUTES_DB.append(inst)
    _save_db()
    return inst


@router.put("/institutes/{inst_id}", summary="Cập nhật thông tin viện")
def update_institute(inst_id: str, body: UnitConfig, _=_admin_dep):
    for i, v in enumerate(INSTITUTES_DB):
        if v["id"] == inst_id:
            INSTITUTES_DB[i] = body.model_dump()
            _save_db()
            return INSTITUTES_DB[i]
    raise HTTPException(status_code=404, detail=f"Không tìm thấy viện '{inst_id}'.")


@router.delete("/institutes/{inst_id}", summary="Xóa viện")
def delete_institute(inst_id: str, _=_admin_dep):
    for i, v in enumerate(INSTITUTES_DB):
        if v["id"] == inst_id:
            INSTITUTES_DB.pop(i)
            # Remove linked majors
            to_remove_majors = [m for m in MAJORS_DB if m["faculty_id"] == inst_id]
            for m in to_remove_majors:
                MAJORS_DB.remove(m)
            _save_db()
            return {"message": f"Đã xóa viện '{inst_id}' và {len(to_remove_majors)} ngành học trực thuộc."}
    raise HTTPException(status_code=404, detail=f"Không tìm thấy viện '{inst_id}'.")


# ─── MAJORS ───────────────────────────────────────────────────

@router.get("/majors", summary="Lấy danh sách ngành/chuyên ngành")
def get_majors(_=_admin_dep):
    return MAJORS_DB


@router.post("/majors", summary="Thêm ngành/chuyên ngành mới")
def add_major(body: MajorConfig, _=_admin_dep):
    if any(m["id"] == body.id for m in MAJORS_DB):
        raise HTTPException(status_code=400, detail=f"Mã ngành '{body.id}' đã tồn tại.")
    
    # Verify faculty_id exists
    faculty_exists = any(d["id"] == body.faculty_id for d in DEPARTMENTS_DB) or any(v["id"] == body.faculty_id for v in INSTITUTES_DB)
    if not faculty_exists:
        raise HTTPException(status_code=400, detail=f"Mã khoa/viện '{body.faculty_id}' không tồn tại.")
        
    major = body.model_dump()
    MAJORS_DB.append(major)
    _save_db()
    return major


@router.put("/majors/{major_id}", summary="Cập nhật thông tin ngành")
def update_major(major_id: str, body: MajorConfig, _=_admin_dep):
    for i, m in enumerate(MAJORS_DB):
        if m["id"] == major_id:
            # Verify faculty_id exists
            faculty_exists = any(d["id"] == body.faculty_id for d in DEPARTMENTS_DB) or any(v["id"] == body.faculty_id for v in INSTITUTES_DB)
            if not faculty_exists:
                raise HTTPException(status_code=400, detail=f"Mã khoa/viện '{body.faculty_id}' không tồn tại.")
            MAJORS_DB[i] = body.model_dump()
            _save_db()
            return MAJORS_DB[i]
    raise HTTPException(status_code=404, detail=f"Không tìm thấy ngành '{major_id}'.")


# --- GRADES / WARNINGS / RULES ---

@router.get("/grades", summary="Tra cuu bang diem Admin")
def get_admin_grades(student_id: str | None = None, ma_mon: str | None = None, current_user: UserOut = _admin_dep):
    rows = []
    for (sid, subject), record in MOCK_GOLD_DB.items():
        if student_id and sid.upper() != student_id.upper():
            continue
        if ma_mon and subject.upper() != ma_mon.upper():
            continue
        rows.append(record)
    return rows


@router.put("/grades/{student_id}/{ma_mon}", summary="Admin sua bang diem va luu lich su diem")
def update_admin_grade(student_id: str, ma_mon: str, body: AdminGradeUpdate, current_user: UserOut = _admin_dep):
    key = (student_id, ma_mon)
    old_record = dict(MOCK_GOLD_DB.get(key, {
        "student_id": student_id,
        "ma_mon": ma_mon,
        "diem_thong_thuong": [],
        "diem_giua_ky": None,
        "diem_cuoi_ky": None,
        "loai_hoc_phan": "ly_thuyet",
        "so_chi_lt": 2,
        "so_chi_th": 0,
        "tong_so_chi": 2,
        "status_canh_bao": "An toan",
    }))
    record = dict(old_record)
    updates = body.model_dump(exclude_none=True)
    reason = updates.pop("reason", None)
    record.update(updates)

    scores_to_check = []
    for field in ["diem_giua_ky", "diem_cuoi_ky", "diem_thuc_hanh_tich_hop", "diem_giua_ky_lt"]:
        if record.get(field) is not None:
            scores_to_check.append(record[field])
    for field in ["diem_thong_thuong", "diem_thuc_hanh_hien_tai", "diem_thuong_ky_lt_list"]:
        scores_to_check.extend(record.get(field) or [])
    record["status_canh_bao"] = "Nguy co" if scores_to_check and sum(scores_to_check) / len(scores_to_check) < 4.0 else "An toan"

    MOCK_GOLD_DB[key] = record
    sync_gold_to_silver()
    history = {
        "id": f"hist_{uuid4().hex[:8]}",
        "student_id": student_id,
        "ma_mon": ma_mon,
        "old_record": old_record,
        "new_record": record,
        "changed_fields": sorted(updates.keys()),
        "reason": reason or "Admin grade update",
        "actor_email": current_user.email,
        "timestamp": _now_str(),
    }
    SCORE_HISTORY_DB.append(history)
    event = _append_admin_event(
        current_user,
        "grade_update",
        f"{student_id}:{ma_mon}",
        "Sua bang diem",
        f"Sua diem {student_id} mon {ma_mon}; fields={history['changed_fields']}",
    )
    return {"record": record, "history": history, "event": event}


@router.get("/score-history", summary="Xem lich su diem phuc vu du doan")
def get_score_history(student_id: str | None = None, ma_mon: str | None = None, current_user: UserOut = _admin_dep):
    rows = SCORE_HISTORY_DB
    if student_id:
        rows = [r for r in rows if r.get("student_id", "").upper() == student_id.upper()]
    if ma_mon:
        rows = [r for r in rows if r.get("ma_mon", "").upper() == ma_mon.upper()]
    return list(reversed(rows))


@router.get("/warnings", summary="Admin quan ly danh sach canh bao sinh vien")
def get_admin_warnings(current_user: UserOut = _admin_dep):
    warnings = []
    for (student_id, ma_mon), record in MOCK_GOLD_DB.items():
        if record.get("status_canh_bao") == "Nguy co":
            warnings.append({"student_id": student_id, "ma_mon": ma_mon, "record": record})
    return warnings


@router.post("/warnings/send", summary="Admin gui canh bao sinh vien va luu lich su gui")
def send_admin_warning(body: WarningSendRequest, current_user: UserOut = _admin_dep):
    recipient = f"{body.student_id.lower()}@smartgpa.edu"
    for user in USERS_DB.values():
        if user.get("role") == "student" and user.get("student_id") == body.student_id:
            recipient = user.get("email") or recipient
            break

    action = {
        "id": f"warn_{uuid4().hex[:8]}",
        "student_id": body.student_id,
        "student_name": body.student_name,
        "ma_mon": body.ma_mon,
        "ten_mon": body.ten_mon,
        "reason": body.reason,
        "fail_risk": body.fail_risk,
        "channel": body.channel,
        "recipient": recipient,
        "actor_email": current_user.email,
        "timestamp": _now_str(),
    }
    WARNING_ACTIONS.append(action)
    for user in USERS_DB.values():
        if user.get("role") == "student" and user.get("student_id") == body.student_id:
            user.setdefault("notifications", []).append({
                "id": f"noti_{uuid4().hex[:8]}",
                "title": "Canh bao hoc vu",
                "message": f"Admin gui canh bao mon {body.ten_mon} ({body.ma_mon}): {body.reason}. Nguy co: {body.fail_risk}%.",
                "type": "warning",
                "sender": current_user.full_name,
                "timestamp": action["timestamp"],
                "is_read": False,
            })
            break
    event = _append_admin_event(
        current_user,
        "warning_send",
        body.student_id,
        "Gui canh bao sinh vien",
        f"{body.ma_mon}: {body.reason}",
    )
    return {"warning": action, "event": event}


@router.get("/warning-actions", summary="Lich su gui canh bao sinh vien")
def get_warning_actions(student_id: str | None = None, current_user: UserOut = _admin_dep):
    rows = WARNING_ACTIONS
    if student_id:
        rows = [r for r in rows if r.get("student_id", "").upper() == student_id.upper()]
    return list(reversed(rows))


@router.get("/grading-rules", summary="Lay cau hinh cach tinh diem")
def get_grading_rules(current_user: UserOut = _admin_dep):
    from app.services.simulation_service import SCORE_MAPPING
    return {**GRADING_RULES_DB, "grade_mapping": SCORE_MAPPING}


@router.put("/grading-rules", summary="Cap nhat cach tinh diem va bang quy doi diem")
def update_grading_rules(body: GradingRulesUpdate, current_user: UserOut = _admin_dep):
    updates = body.model_dump(exclude_none=True)
    grade_mapping = updates.pop("grade_mapping", None)
    GRADING_RULES_DB.update(updates)
    GRADING_RULES_DB["updated_at"] = datetime.now(timezone.utc).isoformat()
    if grade_mapping is not None:
        from app.services import simulation_service
        simulation_service.SCORE_MAPPING.clear()
        simulation_service.SCORE_MAPPING.extend(grade_mapping)
        simulation_service._SCORE_MAP_DICT.clear()
        simulation_service._SCORE_MAP_DICT.update({item["diem_chu"]: item for item in grade_mapping})
    event = _append_admin_event(
        current_user,
        "grading_rules_update",
        "grading_rules",
        "Cap nhat cach tinh diem",
        str(updates),
    )
    return {"grading_rules": get_grading_rules(current_user), "event": event}


@router.delete("/majors/{major_id}", summary="Xóa ngành")
def delete_major(major_id: str, _=_admin_dep):
    for i, m in enumerate(MAJORS_DB):
        if m["id"] == major_id:
            MAJORS_DB.pop(i)
            _save_db()
            return {"message": f"Đã xóa ngành '{major_id}' thành công."}
    raise HTTPException(status_code=404, detail=f"Không tìm thấy ngành '{major_id}'.")
 
