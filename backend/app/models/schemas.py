"""
SmartGPA – Pydantic Schemas (Request / Response Models)
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─────────────────────────────────────────────────────────────
# User & Auth Schemas
# ─────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    STUDENT = "student"
    LECTURER = "lecturer"
    ADMIN = "admin"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    faculty_id: Optional[str] = None
    lecturer_id: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Mật khẩu phải có ít nhất 6 ký tự")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Họ tên không được để trống")
        return v.strip()


class UserLogin(BaseModel):
    email: str = Field(..., description="Email hoac username dang nhap")
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    student_id: Optional[str] = None
    lecturer_id: Optional[str] = None
    subjects: Optional[List[str]] = None  # Danh sách mã môn giảng viên được phân công
    faculty_id: Optional[str] = None
    major_id: Optional[str] = None
    must_change_password: bool = False
    email_verified: bool = False

    model_config = {"from_attributes": True}



class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False
    username: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordOtpRequest(BaseModel):
    username: str
    email: EmailStr


class PasswordOtpResponse(BaseModel):
    message: str
    username: str
    email: str
    dev_otp: Optional[str] = None


class PasswordChangeWithOtp(BaseModel):
    username: str
    otp: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Mat khau moi phai co it nhat 6 ky tu")
        return v


# ─────────────────────────────────────────────────────────────
# Simulation Engine Schemas
# ─────────────────────────────────────────────────────────────

class HocPhanType(str, Enum):
    LY_THUYET = "ly_thuyet"   # Học phần Lý thuyết
    THUC_HANH = "thuc_hanh"   # Học phần Thực hành
    TICH_HOP = "tich_hop"     # Học phần Tích hợp (LT + TH)


class DiemChuTarget(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D_PLUS = "D+"
    D = "D"


class SimulationRequest(BaseModel):
    """
    Yêu cầu tính điểm ngược (Inverse Calculation Engine).
    Sinh viên chọn mục tiêu điểm chữ → hệ thống tính điểm cần đạt.
    """
    loai_hoc_phan: HocPhanType
    muc_tieu: DiemChuTarget  # Điểm chữ mục tiêu (A+, A, B+, ...)

    # ── Số tín chỉ (Dành cho Lý thuyết và Thực hành để kiểm tra số cột điểm) ──
    so_tin_chi: Optional[int] = None

    # ── Lý thuyết: ĐTB_TK = sum(diem_thuong_ky_list) / so_tin_chi ──
    diem_thuong_ky_list: Optional[List[float]] = None   # Danh sách các điểm thường kỳ
    diem_thuong_ky: Optional[float] = None              # Điểm thường kỳ cũ (tương thích ngược)
    diem_giua_ky: Optional[float] = None                # Điểm giữa kỳ (0–10)

    # ── Thực hành: T = mean(TH_1, ..., TH_x) ──
    diem_thuc_hanh_hien_tai: Optional[List[float]] = None  # Các điểm TH đã có
    tong_so_buoi: Optional[int] = None                     # Tổng số buổi TH (tương thích ngược)

    # ── Tích hợp: T = (T_LT×chi_lt + T_TH×chi_th) / tong_chi ──
    so_chi_lt: Optional[int] = None                # Số tín chỉ lý thuyết
    so_chi_th: Optional[int] = None                # Số tín chỉ thực hành
    diem_thuc_hanh_tich_hop: Optional[float] = None  # Điểm TH đã tính
    # Nếu muốn đi sâu hơn: tính CK của nhánh LT
    diem_thuong_ky_lt_list: Optional[List[float]] = None # Danh sách điểm thường kỳ LT
    diem_thuong_ky_lt: Optional[float] = None           # Điểm thường kỳ LT cũ (tương thích ngược)
    diem_giua_ky_lt: Optional[float] = None

    @field_validator("diem_thuong_ky", "diem_giua_ky", "diem_thuc_hanh_tich_hop",
                     "diem_thuong_ky_lt", "diem_giua_ky_lt", mode="before")
    @classmethod
    def score_range(cls, v):
        if v is not None and not (0.0 <= v <= 10.0):
            raise ValueError("Điểm phải trong khoảng 0.0 – 10.0")
        return v

    @field_validator("diem_thuong_ky_list", "diem_thuc_hanh_hien_tai", "diem_thuong_ky_lt_list", mode="before")
    @classmethod
    def score_list_range(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Đầu vào phải là một danh sách")
            for score in v:
                if score is not None and not (0.0 <= score <= 10.0):
                    raise ValueError("Điểm trong danh sách phải trong khoảng 0.0 – 10.0")
        return v


class SimulationResult(BaseModel):
    """Kết quả tính điểm ngược từ Simulation Engine"""
    loai_hoc_phan: str
    muc_tieu: str
    diem_muc_tieu_nguong: float       # Ngưỡng điểm tối thiểu của mục tiêu
    diem_can_dat: Optional[float]     # Điểm cần đạt (None nếu bất khả thi)
    is_kha_thi: bool                  # Có khả thi không
    message: str                      # Thông điệp trả về
    chi_tiet: dict                    # Chi tiết tính toán


class ScoreMappingItem(BaseModel):
    """Một dòng trong bảng quy đổi điểm"""
    diem_10_min: float
    diem_10_max: float
    diem_he_4: float
    diem_chu: str
    loai_danh_gia: str  # "Đạt" / "Không Đạt"


class SimulationCalcRequest(BaseModel):
    """Yêu cầu giả lập tích hợp bảng Gold Databricks"""
    student_id: str
    ma_mon: str
    diem_chu_muc_tieu: DiemChuTarget


class ActivityLogOut(BaseModel):
    """Schema nhật ký hoạt động hệ thống"""
    id: str
    actor_email: str
    actor_name: str
    action: str  # "upload" hoặc "edit"
    subject_id: str
    subject_name: str
    details: str
    timestamp: str


class GradeEditRequest(BaseModel):
    """Yêu cầu sửa điểm học viên"""
    student_id: str
    ma_mon: str
    diem_thong_thuong_list: Optional[List[float]] = None
    diem_giua_ky: Optional[float] = None
    diem_thuc_hanh_hien_tai: Optional[List[float]] = None
    diem_thuc_hanh_tich_hop: Optional[float] = None


class PredictRiskRequest(BaseModel):
    """Yêu cầu dự đoán xác suất rớt từ ML model"""
    diem_thuong_ky: float
    diem_giua_ky: float


class EmailWarningRequest(BaseModel):
    """Yêu cầu gửi email cảnh báo học vụ khẩn cấp"""
    student_id: str
    student_name: str
    ma_mon: str
    ten_mon: str
    reason: str
    fail_risk: float





# -----------------------------------------------------------------
# Admin Management Schemas
# -----------------------------------------------------------------

class SemesterConfig(BaseModel):
    ma_hoc_ky: str
    nam_hoc: str


class SemesterOut(BaseModel):
    ma_hoc_ky: str
    nam_hoc: str
    display: str


class CourseConfig(BaseModel):
    id: str
    name: str
    type: str
    credits: int
    chi_lt: int = 0
    chi_th: int = 0
    faculty_id: Optional[str] = None
    major_id: Optional[str] = None
    is_compulsory: bool = True


class AssignmentConfig(BaseModel):
    lecturer_id: str
    ma_mon: str
    ma_lop: str


class AssignmentOut(BaseModel):
    id: str
    lecturer_id: str
    ma_mon: str
    ma_lop: str
    hoc_ky: str


class UnitConfig(BaseModel):
    id: str
    name: str
    type: str  # "khoa" or "vien"


class MajorConfig(BaseModel):
    id: str
    name: str
    faculty_id: str


class LecturerUpdate(BaseModel):
    full_name: str
    email: EmailStr
    faculty_id: Optional[str] = None


class ProjectInfoUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None


class TimelineUpdateCreate(BaseModel):
    title: str
    category: str = "project"
    details: str


class AdminGradeUpdate(BaseModel):
    diem_thong_thuong: Optional[List[float]] = None
    diem_giua_ky: Optional[float] = None
    diem_cuoi_ky: Optional[float] = None
    diem_thuc_hanh_hien_tai: Optional[List[float]] = None
    diem_thuc_hanh_tich_hop: Optional[float] = None
    diem_thuong_ky_lt_list: Optional[List[float]] = None
    diem_giua_ky_lt: Optional[float] = None
    reason: Optional[str] = None


class WarningSendRequest(BaseModel):
    student_id: str
    student_name: str
    ma_mon: str
    ten_mon: str
    reason: str
    fail_risk: float
    channel: str = "in_app"


class GradingRulesUpdate(BaseModel):
    version: Optional[str] = None
    theory_weights: Optional[dict] = None
    practice_min_pass: Optional[float] = None
    integrated_default_credits: Optional[dict] = None
    grade_mapping: Optional[List[dict]] = None
