"""
SmartGPA – Pydantic Schemas (Request / Response Models)
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, field_validator


# ─────────────────────────────────────────────────────────────
# User & Auth Schemas
# ─────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    STUDENT = "student"
    LECTURER = "lecturer"
    ADVISOR = "advisor"
    ADMIN = "admin"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole

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
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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
