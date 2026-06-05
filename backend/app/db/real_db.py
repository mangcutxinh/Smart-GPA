"""
SmartGPA – Real Database (CSV-backed In-Memory Store)
Đọc dữ liệu sinh viên thực từ các file CSV:
  - bang_diem_DHKHDL19A.csv  (lớp A – Khoa học dữ liệu)
  - bang_diem_DHKHDL19B.csv  (lớp B – Khoa học dữ liệu)

Sinh viên đăng nhập bằng MSSV (ví dụ: 23100001), mật khẩu chung: Sv@123
Khi có Databricks → ưu tiên Databricks. Khi không có → dùng dữ liệu CSV này.
"""

from typing import Optional
import csv
import os
import re
import unicodedata
from datetime import datetime, timezone
from uuid import uuid4

from app.core.security import hash_password

# ─── Paths ────────────────────────────────────────────────────
_DB_DIR = os.path.dirname(__file__)
_CSV_FILES = {
    "DHKHDL19A": os.path.join(_DB_DIR, "bang_diem_DHKHDL19A.csv"),
    "DHKHDL19B": os.path.join(_DB_DIR, "bang_diem_DHKHDL19B.csv"),
}

# ─── Password mặc định cho sinh viên ─────────────────────────
DEFAULT_STUDENT_PASSWORD = "Sv@123"

# ─── In-memory Stores ─────────────────────────────────────────
USERS_DB: dict = {}           # key = mssv (lowercase)
BLACKLIST: set = set()
PASSWORD_RESET_OTPS: dict = {}

# Ánh xạ mã môn thực tế sang mã môn nội bộ của hệ thống
COURSE_ID_MAP: dict[str, str] = {
    "2101680": "INT1001",  # Nhập môn Khoa học Dữ liệu
    "2101539": "INT1001",  # Nhập môn Khoa học Dữ liệu (mã thay thế)
    "2101622": "INT1003",  # Lập trình Python căn bản / Nhập môn lập trình
    "2101409": "INT1306",  # Cấu trúc Dữ liệu & Giải thuật
    "2101436": "INT1100",  # Cơ sở Dữ liệu / Hệ cơ sở dữ liệu
    "2101864": "INT1200",  # Xác suất Thống kê
    "2101435": "INT1410",  # Mạng máy tính & Bảo mật
    "2101831": "INT2001",  # Máy học / Học máy
    "2101891": "INT2002",  # Khai phá Dữ liệu
    "2101886": "INT2400",  # Phân tích Dữ liệu lớn (Big Data)
    "2101850": "INT2300",  # Học sâu (Deep Learning)
    "2101444": "INT2004",  # Xử lý Ngôn ngữ Tự nhiên
    "2101894": "INT2005",  # Thị giác Máy tính
    "2132001": "420300319257",  # Kỹ năng làm việc nhóm
}

# Danh sách môn học – Toàn bộ chương trình ngành KHDL (8 học kỳ)
COURSES_DB: list = [
    # ─── Học kỳ 1 ──────────────────────────────────────────────
    {"id": "INT1001", "name": "Nhập môn Khoa học Dữ liệu", "type": "tich_hop", "credits": 3, "chi_lt": 2, "chi_th": 1, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 1},
    {"id": "INT1002", "name": "Toán học cho Khoa học Dữ liệu", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 1},
    {"id": "INT1003", "name": "Lập trình Python căn bản", "type": "tich_hop", "credits": 3, "chi_lt": 2, "chi_th": 1, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 1},
    {"id": "GDQP102", "name": "Giáo dục Quốc phòng", "type": "ly_thuyet", "credits": 2, "chi_lt": 2, "chi_th": 0, "faculty_id": "KHCB", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 1},
    {"id": "420300319257", "name": "Kỹ năng làm việc nhóm", "type": "ly_thuyet", "credits": 2, "chi_lt": 2, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": False, "hoc_ky": 1},
    # ─── Học kỳ 2 ──────────────────────────────────────────────
    {"id": "INT1100", "name": "Cơ sở Dữ liệu", "type": "tich_hop", "credits": 3, "chi_lt": 2, "chi_th": 1, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 2},
    {"id": "INT1200", "name": "Xác suất Thống kê", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 2},
    {"id": "INT1306", "name": "Cấu trúc Dữ liệu & Giải thuật", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 2},
    {"id": "INT1340", "name": "Thực hành Lập trình Dữ liệu", "type": "thuc_hanh", "credits": 3, "chi_lt": 0, "chi_th": 3, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 2},
    {"id": "INT1410", "name": "Mạng máy tính & Bảo mật", "type": "tich_hop", "credits": 3, "chi_lt": 2, "chi_th": 1, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 2},
    # ─── Học kỳ 3 ──────────────────────────────────────────────
    {"id": "INT2001", "name": "Học máy", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 3},
    {"id": "INT2002", "name": "Khai phá Dữ liệu", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 3},
    {"id": "INT2003", "name": "Trực quan hóa Dữ liệu", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 3},
    {"id": "INT2100", "name": "Kho Dữ liệu & OLAP", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 3},
    {"id": "INT2200", "name": "Thực hành Khoa học Dữ liệu", "type": "thuc_hanh", "credits": 3, "chi_lt": 0, "chi_th": 3, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 3},
    # ─── Học kỳ 4 ──────────────────────────────────────────────
    {"id": "INT2004", "name": "Xử lý Ngôn ngữ Tự nhiên", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 4},
    {"id": "INT2005", "name": "Thị giác Máy tính", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 4},
    {"id": "INT2300", "name": "Học sâu (Deep Learning)", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 4},
    {"id": "INT2400", "name": "Phân tích Dữ liệu lớn (Big Data)", "type": "tich_hop", "credits": 3, "chi_lt": 2, "chi_th": 1, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 4},
    {"id": "INT2500", "name": "Đồ án nhập môn KHDL", "type": "thuc_hanh", "credits": 3, "chi_lt": 0, "chi_th": 3, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 4},
    # ─── Học kỳ 5 ──────────────────────────────────────────────
    {"id": "INT3001", "name": "Trí tuệ Nhân tạo ứng dụng", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 5},
    {"id": "INT3002", "name": "MLOps & Data Engineering", "type": "tich_hop", "credits": 3, "chi_lt": 2, "chi_th": 1, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 5},
    {"id": "INT3003", "name": "Phân tích Kinh doanh Dữ liệu", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 5},
    {"id": "INT3004", "name": "Đồ án Chuyên ngành 1", "type": "thuc_hanh", "credits": 4, "chi_lt": 0, "chi_th": 4, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 5},
    {"id": "INT3005", "name": "Thống kê nâng cao", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 5},
    # ─── Học kỳ 6 ──────────────────────────────────────────────
    {"id": "INT3100", "name": "Học tăng cường (RL)", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 6},
    {"id": "INT3200", "name": "Kiến trúc Dữ liệu DN", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 6},
    {"id": "INT3300", "name": "Đồ án Chuyên ngành 2", "type": "thuc_hanh", "credits": 4, "chi_lt": 0, "chi_th": 4, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 6},
    {"id": "INT3400", "name": "Bảo mật Dữ liệu", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 6},
    {"id": "INT3500", "name": "AI trong Y tế & Xã hội", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": False, "hoc_ky": 6},
    # ─── Học kỳ 7 (ĐANG HỌC – chưa có cuối kỳ) ─────────────────────
    {"id": "INT4001", "name": "Đồ án Tốt nghiệp 1", "type": "thuc_hanh", "credits": 6, "chi_lt": 0, "chi_th": 6, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 7},
    {"id": "INT4002", "name": "Seminar Khoa học Dữ liệu", "type": "ly_thuyet", "credits": 2, "chi_lt": 2, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 7},
    {"id": "INT4003", "name": "Chuyên đề tự chọn 1", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": False, "hoc_ky": 7},
    # ─── Học kỳ 8 (TƯƠNG LAI – chưa bắt đầu) ────────────────────────
    {"id": "INT4100", "name": "Đồ án Tốt nghiệp 2", "type": "thuc_hanh", "credits": 9, "chi_lt": 0, "chi_th": 9, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 8},
    {"id": "INT4200", "name": "Chuyên đề tự chọn 2", "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": False, "hoc_ky": 8},
    {"id": "INT4300", "name": "Kiểm tra đầu ra (Capstone)", "type": "ly_thuyet", "credits": 2, "chi_lt": 2, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 8},
    # ─── Học kỳ 9 (TƯƠNG LAI – chưa bắt đầu) ────────────────────────
    {"id": "INT5001", "name": "Bảo vệ Đồ án Tốt nghiệp", "type": "thuc_hanh", "credits": 9, "chi_lt": 0, "chi_th": 9, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 9},
    {"id": "INT5002", "name": "Kiểm định Chuẩn đầu ra Ngoại ngữ", "type": "ly_thuyet", "credits": 2, "chi_lt": 2, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 9},
    {"id": "INT5003", "name": "Thực tập Tốt nghiệp Doanh nghiệp", "type": "thuc_hanh", "credits": 3, "chi_lt": 0, "chi_th": 3, "faculty_id": "CNTT", "major_id": "KHDL", "is_compulsory": True, "hoc_ky": 9},
]

# Phân công giảng viên – GV1001 dạy HK1-4, GV2002 dạy HK5-8, cả 2 lờp A và B
_ALL_COURSES = [c["id"] for c in COURSES_DB]  # Temporary reference
ASSIGNMENTS_DB: list = []
# Sill be populated after COURSES_DB is available
# We'll fill it in _seed_assignments() below

# Admin & activity stores
ACTIVITY_LOGS: list = []
TIMELINE_UPDATES: list = []
WARNING_ACTIONS: list = []
SCORE_HISTORY_DB: list = []

PROJECT_INFO: dict = {
    "name": "SmartGPA",
    "description": "Hệ thống quản lý điểm, cảnh báo học vụ và dự báo điểm mục tiêu.",
    "owner": "Admin Đào Tạo",
    "status": "active",
    "last_updated": datetime.now(timezone.utc).isoformat(),
}

GRADING_RULES_DB: dict = {
    "version": "2026.06",
    "theory_weights": {
        "diem_thuong_ky": 0.2,
        "diem_giua_ky": 0.3,
        "diem_cuoi_ky": 0.5,
    },
    "practice_min_pass": 3.0,
    "integrated_default_credits": {
        "so_chi_lt": 2,
        "so_chi_th": 1,
    },
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

CURRENT_SEMESTER: dict = {
    "ma_hoc_ky": "HKII",
    "nam_hoc": "2025-2026",
    "display": "HKII 2025-2026",
}

DEPARTMENTS_DB: list[dict] = [
    {"id": "CNCK", "name": "Khoa Công nghệ Cơ khí", "type": "khoa"},
    {"id": "CNTT", "name": "Khoa Công nghệ thông tin", "type": "khoa"},
    {"id": "CND", "name": "Khoa Công nghệ Điện", "type": "khoa"},
    {"id": "CNDT", "name": "Khoa Công nghệ Điện tử", "type": "khoa"},
    {"id": "CNDL", "name": "Khoa Công nghệ Động lực", "type": "khoa"},
    {"id": "CNNL", "name": "Khoa Công nghệ Nhiệt - Lạnh", "type": "khoa"},
    {"id": "CNMTT", "name": "Khoa Công nghệ May - Thời trang", "type": "khoa"},
    {"id": "CNHH", "name": "Khoa Công nghệ Hóa học", "type": "khoa"},
    {"id": "KHCB", "name": "Khoa Khoa học Cơ bản", "type": "khoa"},
    {"id": "LKHCT", "name": "Khoa Luật và Khoa học chính trị", "type": "khoa"},
    {"id": "NN", "name": "Khoa Ngoại ngữ", "type": "khoa"},
    {"id": "QTKD", "name": "Khoa Quản trị Kinh doanh", "type": "khoa"},
    {"id": "TMDL", "name": "Khoa Thương mại - Du lịch", "type": "khoa"},
    {"id": "KTXD", "name": "Khoa Kỹ thuật Xây dựng", "type": "khoa"},
    {"id": "KHSK", "name": "Khoa Khoa học Sức khỏe", "type": "khoa"}
]

INSTITUTES_DB: list[dict] = [
    {"id": "DTQTSDH", "name": "Viện Đào tạo Quốc tế và Sau đại học", "type": "vien"},
    {"id": "TCKT", "name": "Viện Tài chính - Kế toán", "type": "vien"},
    {"id": "CNSHTP", "name": "Viện Công nghệ Sinh học và Thực phẩm", "type": "vien"},
    {"id": "KHCNQLMT", "name": "Viện Khoa học Công nghệ và Quản lý Môi trường", "type": "vien"}
]

MAJORS_DB: list[dict] = [
    # 1. Khoa Công nghệ Cơ khí
    {"id": "CNKT_CK", "name": "Công nghệ kỹ thuật cơ khí", "faculty_id": "CNCK"},
    {"id": "CNCTM", "name": "Công nghệ chế tạo máy", "faculty_id": "CNCK"},
    # 2. Khoa Công nghệ thông tin
    {"id": "CNTT_MAJ", "name": "Công nghệ thông tin", "faculty_id": "CNTT"},
    {"id": "KTPM", "name": "Kỹ thuật phần mềm", "faculty_id": "CNTT"},
    {"id": "KHMT", "name": "Khoa học máy tính", "faculty_id": "CNTT"},
    {"id": "HTTT", "name": "Hệ thống thông tin", "faculty_id": "CNTT"},
    {"id": "TTNT", "name": "Chuyên ngành Trí tuệ nhân tạo", "faculty_id": "CNTT"},
    {"id": "KHDL", "name": "Chuyên ngành Khoa học dữ liệu", "faculty_id": "CNTT"},
    {"id": "CNTT_EN", "name": "Công nghệ thông tin (Tăng cường tiếng Anh)", "faculty_id": "CNTT"},
    {"id": "KTPM_EN", "name": "Kỹ thuật phần mềm (Tăng cường tiếng Anh)", "faculty_id": "CNTT"},
    {"id": "KHMT_EN", "name": "Khoa học máy tính (Tăng cường tiếng Anh)", "faculty_id": "CNTT"},
    {"id": "HTTT_EN", "name": "Hệ thống thông tin (Tăng cường tiếng Anh)", "faculty_id": "CNTT"},
    {"id": "KHDL_EN", "name": "Chuyên ngành Khoa học dữ liệu (Tăng cường tiếng Anh)", "faculty_id": "CNTT"},
    # 3. Khoa Công nghệ Điện
    {"id": "CNKT_DDD", "name": "Công nghệ kỹ thuật điện, điện tử", "faculty_id": "CND"},
    {"id": "NLTT", "name": "Năng lượng tái tạo", "faculty_id": "CND"},
    {"id": "DHN", "name": "Điện hạt nhân", "faculty_id": "CND"},
    # 4. Khoa Công nghệ Điện tử
    {"id": "DTCN", "name": "Điện tử công nghiệp", "faculty_id": "CNDT"},
    {"id": "KTVT", "name": "Kỹ thuật viễn thông", "faculty_id": "CNDT"},
    {"id": "IOT_TTNT", "name": "IOT và Trí tuệ nhân tạo ứng dụng", "faculty_id": "CNDT"},
    {"id": "KTRDD", "name": "Kỹ thuật Radar - Dẫn đường", "faculty_id": "CNDT"},
    {"id": "CNKT_MT", "name": "Công nghệ kỹ thuật máy tính", "faculty_id": "CNDT"},
    {"id": "KTTKVM", "name": "Kỹ thuật thiết kế vi mạch", "faculty_id": "CNDT"},
    # 5. Khoa Công nghệ Động lực
    {"id": "CNKT_CDT", "name": "Công nghệ kỹ thuật cơ điện tử", "faculty_id": "CNDL"},
    {"id": "CNKT_OT", "name": "Công nghệ kỹ thuật ô tô", "faculty_id": "CNDL"},
    {"id": "CNKT_OTD", "name": "Công nghệ kỹ thuật ô tô điện", "faculty_id": "CNDL"},
    # 6. Khoa Công nghệ Nhiệt - Lạnh
    {"id": "CNKT_N", "name": "Công nghệ kỹ thuật nhiệt", "faculty_id": "CNNL"},
    {"id": "CNKT_NL", "name": "Công nghệ kỹ thuật năng lượng", "faculty_id": "CNNL"},
    {"id": "QLNL", "name": "Quản lý năng lượng", "faculty_id": "CNNL"},
    # 7. Khoa Công nghệ May - Thời trang
    {"id": "CNDM", "name": "Công nghệ dệt, may", "faculty_id": "CNMTT"},
    {"id": "TKTT", "name": "Thiết kế thời trang", "faculty_id": "CNMTT"},
    # 8. Khoa Công nghệ Hóa học
    {"id": "CNKT_HH", "name": "Công nghệ kỹ thuật hóa học", "faculty_id": "CNHH"},
    {"id": "KTHPT", "name": "Kỹ thuật hóa phân tích", "faculty_id": "CNHH"},
    {"id": "CNHD", "name": "Công nghệ hóa dược", "faculty_id": "CNHH"},
    {"id": "DBCL_ATTP", "name": "Đảm bảo chất lượng và An toàn thực phẩm", "faculty_id": "CNHH"},
    # 9. Khoa Khoa học Cơ bản
    {"id": "KHCB_GENERAL", "name": "Giảng dạy các môn học cơ bản", "faculty_id": "KHCB"},
    # 10. Khoa Luật và Khoa học chính trị
    {"id": "LKT", "name": "Luật kinh tế", "faculty_id": "LKHCT"},
    # 11. Khoa Ngoại ngữ
    {"id": "NNA", "name": "Ngôn ngữ Anh", "faculty_id": "NN"},
    {"id": "NNTQ", "name": "Ngôn ngữ Trung Quốc", "faculty_id": "NN"},
    # 12. Khoa Quản trị Kinh doanh
    {"id": "QTKD_MAJ", "name": "Quản trị kinh doanh", "faculty_id": "QTKD"},
    {"id": "QTNNL", "name": "Quản trị nguồn nhân lực", "faculty_id": "QTKD"},
    {"id": "LOGISTICS", "name": "Logistics và Quản lý chuỗi cung ứng", "faculty_id": "QTKD"},
    {"id": "MARKETING", "name": "Marketing", "faculty_id": "QTKD"},
    {"id": "DIGITAL_MARKETING", "name": "Digital Marketing", "faculty_id": "QTKD"},
    {"id": "KDQT", "name": "Kinh doanh quốc tế", "faculty_id": "QTKD"},
    {"id": "TMDT", "name": "Thương mại điện tử", "faculty_id": "QTKD"},
    # 13. Khoa Thương mại - Du lịch
    {"id": "QTDVDLLH", "name": "Quản trị dịch vụ du lịch và lữ hành", "faculty_id": "TMDL"},
    {"id": "QTKS", "name": "Quản trị khách sạn", "faculty_id": "TMDL"},
    {"id": "QTNH", "name": "Quản trị nhà hàng và dịch vụ ăn uống", "faculty_id": "TMDL"},
    # 14. Khoa Kỹ thuật Xây dựng
    {"id": "KTXD_MAJ", "name": "Kỹ thuật xây dựng", "faculty_id": "KTXD"},
    {"id": "XDCD", "name": "Xây dựng cầu đường", "faculty_id": "KTXD"},
    {"id": "KTCTDS", "name": "Kỹ thuật công trình đường sắt", "faculty_id": "KTXD"},
    {"id": "QLXD", "name": "Quản lý xây dựng", "faculty_id": "KTXD"},
    # 15. Khoa Khoa học Sức khỏe
    {"id": "DH", "name": "Dược học", "faculty_id": "KHSK"},
    {"id": "DD_KHTP", "name": "Dinh dưỡng và Khoa học thực phẩm", "faculty_id": "KHSK"}
]


# ─── Helper: chuẩn hóa tên thành username ─────────────────────
def _remove_accents(s: str) -> str:
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    return s.replace("đ", "d").replace("Đ", "D")


def build_student_username(student_id: str, full_name: str) -> str:
    clean = _remove_accents(full_name).lower()
    words = [w for w in re.split(r"\s+", clean) if w]
    ten_part = "".join(words[-2:]) if len(words) >= 2 else (words[0] if words else "sv")
    return f"{student_id.strip().lower()}.{ten_part}"


def user_login_key(user: dict) -> str:
    """Key dùng để index trong USERS_DB — ưu tiên username (= MSSV lowercase)."""
    return str(user.get("username") or user.get("email", "")).strip().lower()


def find_user_by_login(identity: str) -> Optional[dict]:
    """Tìm user theo MSSV, username, hoặc email."""
    login = identity.strip().lower()

    # Tra thẳng key
    if login in USERS_DB:
        return USERS_DB[login]

    # Tìm theo email / student_id
    for user in USERS_DB.values():
        if str(user.get("email", "")).strip().lower() == login:
            return user
        if str(user.get("student_id", "")).strip().lower() == login:
            return user
        if str(user.get("username", "")).strip().lower() == login:
            return user
    return None


# ─── Parse header CSV → thông tin môn học ─────────────────────
_HEADER_RE = re.compile(
    r"\[Học kỳ (\d+)\]\s+(\w+)\s*-\s*(.+?)\s*\((\d+)TC\)_Điểm hệ 10",
    re.IGNORECASE,
)

def _parse_courses_from_headers(headers: list) -> list:
    """Trích xuất danh sách môn học duy nhất từ header CSV."""
    seen = set()
    courses = []
    for h in headers:
        m = _HEADER_RE.match(h.strip())
        if m:
            hoc_ky_num, ma_mon, ten_mon, tc_str = m.groups()
            if ma_mon in seen:
                continue
            seen.add(ma_mon)
            credits = int(tc_str)
            courses.append({
                "id": ma_mon,
                "name": ten_mon.strip(),
                "type": "ly_thuyet",   # mặc định; có thể mở rộng sau
                "credits": credits,
                "chi_lt": credits,
                "chi_th": 0,
                "faculty_id": "CNTT",
                "major_id": "KHDL",
                "is_compulsory": True,
                "hoc_ky": int(hoc_ky_num),
            })
    return courses


# ─── Load dữ liệu từ CSV ──────────────────────────────────────
def _load_csv_data():
    """
    Đọc tất cả file CSV, populate:
    - USERS_DB   (sinh viên)
    - COURSES_DB (môn học – bổ sung thêm từ CSV, không xóa seed tĩnh)
    - MOCK_GOLD_DB (điểm – import lazy để tránh circular)
    """
    from app.db.databricks_db import MOCK_GOLD_DB

    # Index các môn học đã seed sẵn để không bị trùng
    existing_course_ids = {c["id"] for c in COURSES_DB}
    all_courses_seen: dict = {c["id"]: c for c in COURSES_DB}
    password_hash = hash_password(DEFAULT_STUDENT_PASSWORD)

    for lop, csv_path in _CSV_FILES.items():
        if not os.path.exists(csv_path):
            # CSV không tồn tại – bỏ qua, dùng seed tĩnh
            continue

        with open(csv_path, encoding="utf-8-sig", errors="replace") as f:
            reader = csv.reader(f)
            raw_headers = next(reader)

        # Lấy danh sách môn từ header
        parsed_courses = _parse_courses_from_headers(raw_headers)
        for c in parsed_courses:
            if c["id"] not in all_courses_seen:
                all_courses_seen[c["id"]] = c
                COURSES_DB.append(c)

        # Map: cột index → (ma_mon, loai_col)
        col_map: dict = {}
        for i, h in enumerate(raw_headers):
            if i < 6:
                continue  # bỏ qua STT, MSSV, họ tên, …
            h_strip = h.strip()
            m = re.match(r"\[Học kỳ \d+\]\s+(\w+)\s*-\s*.+_(.+)$", h_strip, re.IGNORECASE)
            if m:
                ma_mon, loai = m.group(1), m.group(2).strip()
                col_map[i] = (ma_mon, loai)

        # Đọc từng dòng sinh viên
        with open(csv_path, encoding="utf-8-sig", errors="replace") as f:
            reader = csv.reader(f)
            next(reader)  # bỏ header
            for row in reader:
                if len(row) < 6 or not row[1].strip():
                    continue
                mssv = row[1].strip()
                ho_ten = row[2].strip()
                gioi_tinh = row[3].strip()
                ngay_sinh = row[4].strip()
                lop_hoc = row[5].strip()

                username = mssv.lower()  # login = MSSV

                # Thêm sinh viên vào USERS_DB (nếu chưa có)
                if username not in USERS_DB:
                    USERS_DB[username] = {
                        "id": str(uuid4()),
                        "email": f"{username}@student.smartgpa.edu",
                        "username": username,
                        "password_hash": password_hash,
                        "full_name": ho_ten,
                        "role": "student",
                        "is_active": True,
                        "created_at": datetime.now(timezone.utc),
                        "student_id": mssv,
                        "faculty_id": "CNTT",
                        "major_id": "KHDL",
                        "lop_hoc": lop_hoc,
                        "gioi_tinh": gioi_tinh,
                        "ngay_sinh": ngay_sinh,
                        "notifications": [],
                        "must_change_password": False,
                        "email_verified": True,
                    }

                # Điểm từng môn → MOCK_GOLD_DB
                scores_by_mon: dict = {}
                for i, val in enumerate(row):
                    if i not in col_map:
                        continue
                    ma_mon, loai = col_map[i]
                    if ma_mon not in scores_by_mon:
                        scores_by_mon[ma_mon] = {}
                    val_stripped = val.strip()
                    scores_by_mon[ma_mon][loai] = val_stripped

                for ma_mon, cols in scores_by_mon.items():
                    diem_10_str = cols.get("Điểm hệ 10", "")
                    diem_chu = cols.get("Điểm chữ", "")
                    diem_4_str = cols.get("Điểm hệ 4", "")
                    ket_qua = cols.get("Kết quả", "")

                    # Bỏ qua nếu không có điểm
                    if not diem_10_str:
                        continue

                    try:
                        diem_10 = float(diem_10_str)
                    except ValueError:
                        continue

                    try:
                        diem_4 = float(diem_4_str)
                    except ValueError:
                        diem_4 = 0.0

                    # Xác định tín chỉ từ COURSES_DB
                    course_info = all_courses_seen.get(ma_mon, {})
                    tong_so_chi = course_info.get("credits", 2)
                    chi_lt = course_info.get("chi_lt", tong_so_chi)
                    chi_th = course_info.get("chi_th", 0)

                    status_canh_bao = "Nguy co" if diem_10 < 4.0 else "An toan"

                    key = (mssv, ma_mon)
                    if key not in MOCK_GOLD_DB:
                        MOCK_GOLD_DB[key] = {
                            "student_id": mssv,
                            "student_name": ho_ten,
                            "ma_mon": ma_mon,
                            "ten_mon": course_info.get("name", ma_mon),
                            "ma_lop_hoc_phan": lop_hoc,
                            "diem_tong_ket": diem_10,
                            "diem_chu": diem_chu,
                            "diem_he_4": diem_4,
                            "ket_qua": ket_qua,
                            # Chia điểm tổng kết thành các thành phần (ước tính)
                            "diem_thong_thuong": [],
                            "diem_giua_ky": None,
                            "diem_cuoi_ky": diem_10,  # coi điểm tổng kết là điểm cuối kỳ
                            "loai_hoc_phan": "ly_thuyet",
                            "so_chi_lt": chi_lt,
                            "so_chi_th": chi_th,
                            "tong_so_chi": tong_so_chi,
                            "hoc_ky": course_info.get("hoc_ky", 1),
                            "status_canh_bao": status_canh_bao,
                        }


# ─── Seed admin mặc định ──────────────────────────────────────
def _seed_admin():
    admin_key = "admin"
    if admin_key not in USERS_DB:
        USERS_DB[admin_key] = {
            "id": str(uuid4()),
            "email": "admin@smartgpa.edu",
            "username": "admin",
            "password_hash": hash_password("Admin@123"),
            "full_name": "Admin Đào Tạo",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "notifications": [],
            "must_change_password": False,
            "email_verified": True,
        }


def _seed_demo_users():
    demo_accounts = [
        {
            "id": str(uuid4()),
            "email": "student@smartgpa.edu",
            "password_hash": hash_password("Sv@123"),
            "full_name": "Nguyễn Văn An",
            "role": "student",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "student_id": "SV123456",
            "faculty_id": "CNTT",
            "major_id": "KTPM",
            "notifications": [],
        },
        {
            "id": str(uuid4()),
            "email": "thaoanh.sv1001@gmail.com",
            "password_hash": hash_password("Sv@123"),
            "full_name": "Nguyễn Thảo Anh",
            "role": "student",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "student_id": "SV1001",
            "faculty_id": "CNTT",
            "major_id": "KTPM",
            "notifications": [],
        },
        {
            "id": str(uuid4()),
            "email": "haivy.sv1002@gmail.com",
            "password_hash": hash_password("Sv@123"),
            "full_name": "Vũ Hải Vy",
            "role": "student",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "student_id": "SV1002",
            "faculty_id": "CNTT",
            "major_id": "KTPM",
            "notifications": [],
        },
        {
            "id": str(uuid4()),
            "email": "thibinh.gv1001@smartgpa.edu",
            "password_hash": hash_password("Gv@123"),
            "full_name": "TS. Trần Thị Bình",
            "role": "lecturer",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "lecturer_id": "GV1001",
            "faculty_id": "CNTT",
            "notifications": [],
        },
        {
            "id": str(uuid4()),
            "email": "minhtriet.gv1002@smartgpa.edu",
            "password_hash": hash_password("Gv@123"),
            "full_name": "TS. Nguyễn Minh Triết",
            "role": "lecturer",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "lecturer_id": "GV1002",
            "faculty_id": "CNTT",
            "notifications": [],
        },
        {
            "id": str(uuid4()),
            "email": "admin@smartgpa.edu",
            "password_hash": hash_password("Admin@123"),
            "full_name": "Admin Đào Tạo",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "notifications": [],
        },
    ]
    for user in demo_accounts:
        user.setdefault("username", user["email"])
        user.setdefault("must_change_password", False)
        user.setdefault("email_verified", bool(user.get("email")))
        USERS_DB[user_login_key(user)] = user


def _seed_assignments_and_students():
    """
    Seed:
    1. ASSIGNMENTS_DB — GV1001 dạy HK1-4 (lớp A+B), GV1002 dạy HK5-9 (lớp A+B)
    2. USERS_DB — 50 SV lớp DHKHDL19A + 48 SV lớp DHKHDL19B
    3. MOCK_GOLD_DB — điểm cho tất cả SV:
       - HK1-6: có đủ diem_thong_thuong, diem_giua_ky, diem_cuoi_ky
       - HK7 (đang học): chỉ có diem_thong_thuong, diem_giua_ky (diem_cuoi_ky = None)
       - HK8-9 (tương lai): không có records
    """
    import random
    import hashlib
    from app.db.databricks_db import MOCK_GOLD_DB

    # ─── Danh sách 50 SV lớp DHKHDL19A ──────────────────────────────
    students_A = [
        ("23677361", "Nguyễn Tuấn Anh",          "Nam", "23/12/2005", "DHKHDL19A"),
        ("23667351", "Trương Tuấn Bình",          "Nam", "30/05/2005", "DHKHDL19A"),
        ("23634031", "Trần Vĩnh Cơ",             "Nam", "11/04/2005", "DHKHDL19A"),
        ("23634051", "Lê Huỳnh Tấn Đạt",         "Nam", "25/11/2005", "DHKHDL19A"),
        ("23631971", "Nguyễn Xuân Đình",          "Nam", "23/12/2005", "DHKHDL19A"),
        ("23636521", "Phạm Thành Đô",             "Nam", "08/02/2005", "DHKHDL19A"),
        ("23640661", "Lê Văn Dũng",               "Nam", "08/05/2005", "DHKHDL19A"),
        ("23650821", "Nguyễn Tiến Dũng",          "Nam", "05/04/2005", "DHKHDL19A"),
        ("23646941", "Võ Khương Duy",             "Nam", "04/07/2005", "DHKHDL19A"),
        ("23634731", "Nguyễn Cẩm Hà",            "Nữ",  "14/09/2005", "DHKHDL19A"),
        ("23663871", "Huỳnh Nhật Hảo",           "Nam", "05/07/2005", "DHKHDL19A"),
        ("23674431", "Trần Nhựt Hảo",            "Nam", "29/08/2005", "DHKHDL19A"),
        ("23642061", "Huỳnh Võ Tấn Hiên",        "Nam", "15/09/2005", "DHKHDL19A"),
        ("23632591", "Trịnh Quang Hiên",          "Nam", "17/08/2005", "DHKHDL19A"),
        ("23632141", "Lê Đức Hoà",               "Nam", "19/06/2005", "DHKHDL19A"),
        ("23635051", "Nguyễn Minh Hoàng",         "Nam", "20/08/2005", "DHKHDL19A"),
        ("23666491", "Lê Trung Hữu",             "Nam", "02/01/2005", "DHKHDL19A"),
        ("23001095", "Lê Quang Huy",             "Nam", "29/10/2005", "DHKHDL19A"),
        ("23670201", "Nguyễn Anh Huy",           "Nam", "20/08/2005", "DHKHDL19A"),
        ("23001115", "Nguyễn Khánh Huy",         "Nam", "27/04/2005", "DHKHDL19A"),
        ("23635041", "Nguyễn Minh Huy",          "Nam", "04/03/2005", "DHKHDL19A"),
        ("23674141", "Phan Gia Huy",             "Nam", "28/01/2005", "DHKHDL19A"),
        ("23637731", "Trần Quốc Huy",            "Nam", "02/11/2005", "DHKHDL19A"),
        ("23634341", "Nguyễn Hà Mạnh Khang",     "Nam", "28/01/2005", "DHKHDL19A"),
        ("23660931", "Nguyễn Trần Phúc Khang",   "Nam", "02/11/2005", "DHKHDL19A"),
        ("23673611", "Phan Khánh Khoa",           "Nam", "31/01/2005", "DHKHDL19A"),
        ("23631351", "Lục Vỹ Kiệt",              "Nam", "27/01/2005", "DHKHDL19A"),
        ("23655711", "Trần Anh Kiệt",            "Nam", "21/03/2005", "DHKHDL19A"),
        ("23636491", "Trần Hoàng Xuân Lộc",      "Nam", "05/10/2005", "DHKHDL19A"),
        ("23636861", "Lê Quang Long",            "Nam", "02/11/2005", "DHKHDL19A"),
        ("23001025", "Bùi Đức Mạnh",             "Nam", "30/11/2005", "DHKHDL19A"),
        ("23646891", "Võ Lê Hoàng Minh",         "Nam", "14/07/2005", "DHKHDL19A"),
        ("23630761", "Hoàng Trọng Nghĩa",         "Nam", "18/12/2005", "DHKHDL19A"),
        ("23643121", "Lê Văn Nguyên",            "Nam", "18/12/2005", "DHKHDL19A"),
        ("23672291", "Võ Đại Phát",              "Nam", "19/11/2005", "DHKHDL19A"),
        ("23001305", "Nguyễn Di Phi",            "Nam", "15/09/2005", "DHKHDL19A"),
        ("23001015", "Vũ Hoàng Phúc",            "Nam", "15/09/2005", "DHKHDL19A"),
        ("23644201", "Trương Thanh Phụng",        "Nam", "14/10/2004", "DHKHDL19A"),
        ("23640781", "Nguyễn Duy Quân",          "Nam", "28/09/2005", "DHKHDL19A"),
        ("23650801", "Nguyễn Huỳnh Nhật Tân",    "Nam", "01/07/2005", "DHKHDL19A"),
        ("23670311", "Ngô Phước Thiên",           "Nam", "18/02/2004", "DHKHDL19A"),
        ("23643081", "Phạm Thị Anh Thư",         "Nữ",  "23/01/2005", "DHKHDL19A"),
        ("23001005", "Nguyễn Hữu Thuận",         "Nam", "30/04/2005", "DHKHDL19A"),
        ("23673681", "Trần Nhật Tiến",           "Nam", "29/07/2005", "DHKHDL19A"),
        ("23672111", "Phạm Ngọc Toàn",           "Nam", "30/04/2005", "DHKHDL19A"),
        ("23676071", "Nguyễn Thị Quỳnh Trang",   "Nữ",  "29/07/2005", "DHKHDL19A"),
        ("23673721", "Kim Đức Trí",              "Nam", "05/09/2005", "DHKHDL19A"),
        ("23001185", "Chu Minh Tuấn",            "Nam", "05/09/2005", "DHKHDL19A"),
        ("23644831", "Đỗ Lê Vinh",              "Nam", "07/05/2005", "DHKHDL19A"),
        ("23001205", "Nguyễn Thế Vũ",           "Nam", "07/05/2005", "DHKHDL19A"),
    ]

    # ─── Danh sách 48 SV lớp DHKHDL19B ──────────────────────────────
    students_B = [
        ("23695481", "Muhammad Arifil",           "Nam", "07/02/2005", "DHKHDL19B"),
        ("23723801", "La Thiên Bảo",             "Nam", "02/05/2005", "DHKHDL19B"),
        ("23720061", "Lê Gia Bảo",              "Nam", "13/06/2005", "DHKHDL19B"),
        ("23716711", "Nguyễn Quốc Đăng",         "Nam", "20/06/2005", "DHKHDL19B"),
        ("23724811", "Bùi Thành Đạt",           "Nam", "12/07/2004", "DHKHDL19B"),
        ("23686521", "Lê Minh Đạt",             "Nam", "25/11/2005", "DHKHDL19B"),
        ("23719201", "Bùi Trường Định",          "Nam", "30/03/2005", "DHKHDL19B"),
        ("23732881", "Nguyễn Bá Đức",           "Nam", "13/07/2005", "DHKHDL19B"),
        ("23726261", "Ngũ Minh Duy",            "Nam", "18/05/2005", "DHKHDL19B"),
        ("23694641", "Hồ Long Giang",           "Nam", "19/12/2005", "DHKHDL19B"),
        ("23705991", "Nguyễn Vũ Hà",           "Nam", "25/11/2005", "DHKHDL19B"),
        ("23668291", "Nguyễn Văn Hùng",          "Nam", "18/10/2005", "DHKHDL19B"),
        ("23727381", "Lê Ngọc Huy",             "Nam", "03/01/2005", "DHKHDL19B"),
        ("23729241", "Trần Lê Quang Huy",        "Nam", "08/07/2005", "DHKHDL19B"),
        ("23722301", "Nguyễn Tấn Khang",         "Nam", "14/10/2005", "DHKHDL19B"),
        ("23713631", "Trịnh Trần Phúc Khang",    "Nam", "19/06/2005", "DHKHDL19B"),
        ("23711381", "Khuất Quốc Khánh",         "Nam", "02/03/2005", "DHKHDL19B"),
        ("23703471", "Huỳnh Đăng Khoa",          "Nam", "02/02/2005", "DHKHDL19B"),
        ("23690481", "Nguyễn Trung Kiên",         "Nam", "24/04/2005", "DHKHDL19B"),
        ("23718591", "Nguyễn Hoàng Nam",          "Nam", "08/07/2005", "DHKHDL19B"),
        ("23719511", "Trần Thị Kim Ngân",         "Nữ",  "20/09/2005", "DHKHDL19B"),
        ("23709251", "Võ Thanh Nhã",             "Nam", "28/08/2005", "DHKHDL19B"),
        ("23698431", "Lê Trần Quang Nhân",        "Nam", "26/09/2005", "DHKHDL19B"),
        ("23697331", "Nguyễn Trường Phát",        "Nam", "01/09/2005", "DHKHDL19B"),
        ("23725131", "Dương Hồng Phong",          "Nam", "31/01/2005", "DHKHDL19B"),
        ("23696981", "Vũ Ngọc Thu Phương",        "Nữ",  "07/02/2005", "DHKHDL19B"),
        ("23703521", "Mai Văn Quân",             "Nam", "14/06/2005", "DHKHDL19B"),
        ("23693061", "Trần Minh Quân",           "Nam", "26/04/2005", "DHKHDL19B"),
        ("23715111", "Trần Quốc Sang",           "Nam", "27/06/2005", "DHKHDL19B"),
        ("23682371", "Lăng Hoàng Sơn",           "Nam", "25/01/2005", "DHKHDL19B"),
        ("23724311", "Hồ Nguyễn Tấn Tài",        "Nam", "16/02/2005", "DHKHDL19B"),
        ("23705311", "Trần Tiến Tài",            "Nam", "25/10/2005", "DHKHDL19B"),
        ("23714171", "Võ Đại Nhật Tân",          "Nam", "02/01/2005", "DHKHDL19B"),
        ("23708371", "Đỗ Nhất Thắng",           "Nam", "26/09/2005", "DHKHDL19B"),
        ("23712461", "Bùi Quang Thành",          "Nam", "26/07/2005", "DHKHDL19B"),
        ("23684241", "Nguyễn Thị Phương Thảo",   "Nữ",  "03/08/2005", "DHKHDL19B"),
        ("23725051", "Trương Thế Hải Thịnh",      "Nam", "06/08/2005", "DHKHDL19B"),
        ("23689481", "Phạm Trần Minh Tiến",       "Nam", "27/02/2005", "DHKHDL19B"),
        ("23710141", "Nguyễn Minh Trí",          "Nam", "10/02/2005", "DHKHDL19B"),
        ("23720331", "Võ Minh Trí",             "Nam", "11/04/2005", "DHKHDL19B"),
        ("23722031", "Nguyễn Ngọc Anh Tú",       "Nam", "04/06/2005", "DHKHDL19B"),
        ("23707921", "Bùi Quang Tuyến",          "Nam", "02/10/2005", "DHKHDL19B"),
        ("23737251", "Trương Đặng Hoàng Tuyến",   "Nam", "10/06/2005", "DHKHDL19B"),
        ("23719241", "Đặng Hồng Tỷ",            "Nam", "20/12/2005", "DHKHDL19B"),
        ("23712661", "Lê Nhật Việt",            "Nam", "14/05/2005", "DHKHDL19B"),
        ("23730321", "Cao Anh Vũ",              "Nam", "15/08/2005", "DHKHDL19B"),
        ("23715831", "Trần Gia Vỹ",             "Nam", "20/10/2005", "DHKHDL19B"),
        ("23712271", "Lê Thị Hồng Yến",         "Nữ",  "20/12/2005", "DHKHDL19B"),
    ]

    # ─── Seed ASSIGNMENTS_DB ──────────────────────────────────────────
    hk_map = {
        1: "HKI",  2: "HKII",  3: "HKIII", 4: "HKIV",
        5: "HKV",  6: "HKVI",  7: "HKVII", 8: "HKVIII",
        9: "HKIX",
    }
    for course in COURSES_DB:
        hk = course["hoc_ky"]
        gv = "GV1001" if hk <= 4 else "GV1002"
        for lop in ["DHKHDL19A", "DHKHDL19B"]:
            asgn_id = f"asgn_{course['id']}_{lop}"
            if not any(a["id"] == asgn_id for a in ASSIGNMENTS_DB):
                ASSIGNMENTS_DB.append({
                    "id": asgn_id,
                    "lecturer_id": gv,
                    "ma_mon": course["id"],
                    "ten_mon": course["name"],
                    "ma_lop": lop,
                    "hoc_ky": f"{hk_map[hk]} 2025-2026",
                    "hoc_ky_num": hk,
                })

    # ─── Seed USERS_DB + MOCK_GOLD_DB ────────────────────────────────
    password_hash = hash_password(DEFAULT_STUDENT_PASSWORD)
    all_students = students_A + students_B

    def _grade_letter(tong: float):
        """Trả về (diem_chu, diem_he_4)"""
        if tong >= 9.0:  return ("A+", 4.0)
        if tong >= 8.5:  return ("A",  4.0)
        if tong >= 8.0:  return ("B+", 3.5)
        if tong >= 7.0:  return ("B",  3.0)
        if tong >= 6.5:  return ("C+", 2.5)
        if tong >= 5.5:  return ("C",  2.0)
        if tong >= 5.0:  return ("D+", 1.5)
        if tong >= 4.0:  return ("D",  1.0)
        return ("F", 0.0)

    for mssv, ho_ten, gioi_tinh, ngay_sinh, lop in all_students:
        username = mssv.lower()

        if username not in USERS_DB:
            USERS_DB[username] = {
                "id": str(uuid4()),
                "email": f"{username}@student.smartgpa.edu",
                "username": username,
                "password_hash": password_hash,
                "full_name": ho_ten,
                "role": "student",
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "student_id": mssv,
                "faculty_id": "CNTT",
                "major_id": "KHDL",
                "lop_hoc": lop,
                "gioi_tinh": gioi_tinh,
                "ngay_sinh": ngay_sinh,
                "notifications": [],
                "must_change_password": False,
                "email_verified": True,
            }

        # Điểm ổn định theo MSSV (deterministic)
        seed_val = int(hashlib.md5(mssv.encode()).hexdigest(), 16) % (2 ** 32)
        rng = random.Random(seed_val)

        for course in COURSES_DB:
            hk = course["hoc_ky"]
            loai = course["type"]
            ma_mon = course["id"]
            ten_mon = course["name"]

            # HK8-9: chưa bắt đầu – không tạo record
            if hk >= 8:
                rng.random()  # consume entropy để seed nhất quán
                continue

            is_current = (hk == 7)  # HK7: đang học, thiếu cuối kỳ

            key = (mssv, ma_mon)
            if key in MOCK_GOLD_DB:
                continue  # không ghi đè dữ liệu đã có

            base = rng.uniform(5.5, 9.5)

            if loai == "ly_thuyet":
                tk1 = round(min(10.0, base + rng.uniform(-0.5, 0.5)), 1)
                tk2 = round(min(10.0, base + rng.uniform(-0.5, 0.5)), 1)
                gk  = round(min(10.0, base + rng.uniform(-0.3, 0.8)), 1)

                if is_current:
                    ck = None; tong = None; diem_chu = None; diem_he4 = None; ket_qua = None
                    status = "An toan" if gk >= 4.0 else "Nguy co"
                else:
                    ck = round(min(10.0, base + rng.uniform(-0.5, 1.0)), 1)
                    tong = round(0.2 * ((tk1 + tk2) / 2.0) + 0.3 * gk + 0.5 * ck, 1)
                    tong = min(10.0, tong)
                    if ck < 3.0 or tong < 4.0:
                        diem_chu, diem_he4 = "F", 0.0
                        ket_qua = "Khong dat"
                        status = "Nguy co"
                    else:
                        diem_chu, diem_he4 = _grade_letter(tong)
                        ket_qua = "Dat"
                        status = "An toan"

                MOCK_GOLD_DB[key] = {
                    "student_id": mssv, "student_name": ho_ten,
                    "ma_mon": ma_mon, "ten_mon": ten_mon,
                    "ma_lop_hoc_phan": lop, "loai_hoc_phan": "ly_thuyet",
                    "so_chi_lt": course["chi_lt"], "so_chi_th": 0,
                    "tong_so_chi": course["credits"],
                    "diem_thong_thuong": [tk1, tk2], "diem_giua_ky": gk,
                    "diem_cuoi_ky": ck, "diem_tong_ket": tong,
                    "diem_chu": diem_chu, "diem_he_4": diem_he4,
                    "ket_qua": ket_qua, "hoc_ky": hk, "status_canh_bao": status,
                }

            elif loai == "thuc_hanh":
                th_list = [round(min(10.0, base + rng.uniform(-1.0, 1.0)), 1) for _ in range(3)]
                avg_th = round(sum(th_list) / len(th_list), 1)

                if is_current:
                    ck = None; tong = None; diem_chu = None; diem_he4 = None; ket_qua = None
                    status = "An toan" if avg_th >= 4.0 else "Nguy co"
                else:
                    ck = avg_th; tong = ck
                    if tong < 4.0:
                        diem_chu, diem_he4 = "F", 0.0
                        ket_qua = "Khong dat"
                        status = "Nguy co"
                    else:
                        diem_chu, diem_he4 = _grade_letter(tong)
                        ket_qua = "Dat"
                        status = "An toan"

                MOCK_GOLD_DB[key] = {
                    "student_id": mssv, "student_name": ho_ten,
                    "ma_mon": ma_mon, "ten_mon": ten_mon,
                    "ma_lop_hoc_phan": lop, "loai_hoc_phan": "thuc_hanh",
                    "so_chi_lt": 0, "so_chi_th": course["chi_th"],
                    "tong_so_chi": course["credits"],
                    "diem_thong_thuong": [], "diem_giua_ky": None,
                    "diem_thuc_hanh_hien_tai": th_list,
                    "diem_cuoi_ky": ck, "diem_tong_ket": tong,
                    "diem_chu": diem_chu, "diem_he_4": diem_he4,
                    "ket_qua": ket_qua, "hoc_ky": hk, "status_canh_bao": status,
                }

            else:  # tich_hop
                chi_lt = course["chi_lt"]
                tk_lt  = [round(min(10.0, base + rng.uniform(-0.5, 0.5)), 1) for _ in range(max(chi_lt, 2))]
                gk_lt  = round(min(10.0, base + rng.uniform(-0.3, 0.7)), 1)
                th_val = round(min(10.0, base + rng.uniform(-0.5, 1.0)), 1)

                if is_current:
                    ck = None; tong = None; diem_chu = None; diem_he4 = None; ket_qua = None
                    status = "An toan" if th_val >= 4.0 else "Nguy co"
                else:
                    ck = round(min(10.0, base + rng.uniform(-0.5, 1.0)), 1)
                    tk_avg = round(sum(tk_lt) / len(tk_lt), 1)
                    lt_score = 0.2 * tk_avg + 0.3 * gk_lt + 0.5 * ck
                    tong = round((lt_score * 2.0 + th_val * 1.0) / 3.0, 1)
                    tong = min(10.0, tong)
                    if ck < 3.0 or th_val < 3.0 or tong < 4.0:
                        diem_chu, diem_he4 = "F", 0.0
                        ket_qua = "Khong dat"
                        status = "Nguy co"
                    else:
                        diem_chu, diem_he4 = _grade_letter(tong)
                        ket_qua = "Dat"
                        status = "An toan"

                MOCK_GOLD_DB[key] = {
                    "student_id": mssv, "student_name": ho_ten,
                    "ma_mon": ma_mon, "ten_mon": ten_mon,
                    "ma_lop_hoc_phan": lop, "loai_hoc_phan": "tich_hop",
                    "so_chi_lt": chi_lt, "so_chi_th": course["chi_th"],
                    "tong_so_chi": course["credits"],
                    "diem_thong_thuong": [], "diem_giua_ky": None,
                    "diem_thuong_ky_lt_list": tk_lt,
                    "diem_giua_ky_lt": gk_lt, "diem_thuc_hanh_tich_hop": th_val,
                    "diem_cuoi_ky": ck, "diem_tong_ket": tong,
                    "diem_chu": diem_chu, "diem_he_4": diem_he4,
                    "ket_qua": ket_qua, "hoc_ky": hk, "status_canh_bao": status,
                }


# ─── Bootstrap khi import module ──────────────────────────────
_load_csv_data()
_seed_admin()
_seed_demo_users()
_seed_assignments_and_students()
