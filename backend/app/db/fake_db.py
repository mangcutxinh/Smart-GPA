"""
SmartGPA – In-Memory Database (Development / Testing)
Thay thế Databricks khi chạy local. Seed sẵn 4 tài khoản demo.

Khi tích hợp Databricks thật: swap module này bằng databricks_db.py
"""
from datetime import datetime, timezone
from uuid import uuid4

from app.core.security import hash_password

# ─── Users store: {email: user_dict} ─────────────────────────
USERS_DB: dict[str, dict] = {}

# ─── Blacklisted refresh tokens (logout) ─────────────────────
BLACKLIST: set[str] = set()
PASSWORD_RESET_OTPS: dict[str, dict] = {}


import unicodedata
import re

def remove_accents(input_str: str) -> str:
    """Helper: Loại bỏ dấu tiếng Việt"""
    s = ''.join(c for c in unicodedata.normalize('NFD', input_str) if unicodedata.category(c) != 'Mn')
    s = s.replace('đ', 'd').replace('Đ', 'd')
    return s

def normalize_name_to_username(full_name: str) -> str:
    """Helper: Chuẩn hóa họ tên thành ten không dấu liền nhau (lấy tối đa 2 từ cuối)"""
    clean = remove_accents(full_name).lower()
    words = [w for w in re.split(r'\s+', clean) if w]
    if len(words) >= 2:
        ten_part = "".join(words[-2:])
    elif len(words) == 1:
        ten_part = words[0]
    else:
        ten_part = "sv"
    return ten_part


def build_student_username(student_id: str, full_name: str) -> str:
    return f"{student_id.strip().lower()}.{normalize_name_to_username(full_name)}"


def find_user_by_login(identity: str) -> dict | None:
    login = identity.strip().lower()
    user = USERS_DB.get(login)
    if user:
        return user
    for candidate in USERS_DB.values():
        if str(candidate.get("email", "")).strip().lower() == login:
            return candidate
        if str(candidate.get("username", "")).strip().lower() == login:
            return candidate
        if candidate.get("role") == "student" and str(candidate.get("student_id", "")).strip().lower() == login:
            return candidate
    return None


def user_login_key(user: dict) -> str:
    return str(user.get("username") or user.get("email", "")).strip().lower()


def _seed_demo_users() -> None:
    """Seed tài khoản demo phù hợp danh sách Databricks & cấu hình khóa môn học"""
    demo_accounts = [
        {
            "id": str(uuid4()),
            "email": "student@smartgpa.edu",
            "password_hash": hash_password("password123"),
            "full_name": "Nguyễn Văn An",
            "role": "student",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "student_id": "SV123456",
            "faculty_id": "CNTT",
            "major_id": "KTPM",
            "notifications": []
        },
        {
            "id": str(uuid4()),
            "email": "thaoanh.sv1001@gmail.com",
            "password_hash": hash_password("password123"),
            "full_name": "Nguyễn Thảo Anh",
            "role": "student",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "student_id": "SV1001",
            "faculty_id": "CNTT",
            "major_id": "KTPM",
            "notifications": []
        },
        {
            "id": str(uuid4()),
            "email": "haivy.sv1002@gmail.com",
            "password_hash": hash_password("password123"),
            "full_name": "Vũ Hải Vy",
            "role": "student",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "student_id": "SV1002",
            "faculty_id": "CNTT",
            "major_id": "KTPM",
            "notifications": []
        },
        {
            "id": str(uuid4()),
            "email": "thibinh.gv1001@smartgpa.edu",
            "password_hash": hash_password("password123"),
            "full_name": "TS. Trần Thị Bình",
            "role": "lecturer",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "lecturer_id": "GV1001",
            "faculty_id": "CNTT",
            "notifications": []
        },
        {
            "id": str(uuid4()),
            "email": "minhtriet.gv1002@smartgpa.edu",
            "password_hash": hash_password("password123"),
            "full_name": "TS. Nguyễn Minh Triết",
            "role": "lecturer",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "lecturer_id": "GV1002",
            "faculty_id": "CNTT",
            "notifications": []
        },
        {
            "id": str(uuid4()),
            "email": "admin@smartgpa.edu",
            "password_hash": hash_password("password123"),
            "full_name": "Admin Đào Tạo",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "notifications": []
        },
    ]
    for user in demo_accounts:
        user.setdefault("username", user["email"])
        user.setdefault("must_change_password", False)
        user.setdefault("email_verified", bool(user.get("email")))
        USERS_DB[user_login_key(user)] = user


# Seed ngay khi import module
_seed_demo_users()


# ─── System Activity Audit Logs Store ──────────────────────────
# Stores history of lecturer and admin activities (grades upload, edits)
ACTIVITY_LOGS: list[dict] = []
TIMELINE_UPDATES: list[dict] = []
WARNING_ACTIONS: list[dict] = []
SCORE_HISTORY_DB: list[dict] = []
PROJECT_INFO: dict = {
    "name": "SmartGPA",
    "description": "He thong quan ly diem, canh bao hoc vu va du bao diem muc tieu.",
    "owner": "Admin Dao Tao",
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

def _seed_demo_activities() -> None:
    """Seed một vài hoạt động thực tế để admin kiểm tra lịch sử"""
    import datetime
    now = datetime.datetime.now()
    
    logs = [
        {
            "id": "act_1",
            "actor_email": "thibinh.gv1001@smartgpa.edu",
            "actor_name": "TS. Trần Thị Bình",
            "action": "upload",
            "subject_id": "INT1001",
            "subject_name": "Lập trình Python (Tích hợp)",
            "details": "Nạp bảng điểm lớp L01 qua file CSV thành công (đồng bộ 45 sinh viên vào Delta Gold Table).",
            "timestamp": (now - datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "id": "act_2",
            "actor_email": "thibinh.gv1001@smartgpa.edu",
            "actor_name": "TS. Trần Thị Bình",
            "action": "edit",
            "subject_id": "INT1001",
            "subject_name": "Lập trình Python (Tích hợp)",
            "details": "Chỉnh sửa điểm thành phần cho Sinh viên SV1001: Cập nhật Giữa kỳ Lý thuyết = 8.0 (trước đó là 5.0).",
            "timestamp": (now - datetime.timedelta(hours=1, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "id": "act_3",
            "actor_email": "admin@smartgpa.edu",
            "actor_name": "Admin Đào Tạo",
            "action": "upload",
            "subject_id": "GDQP102",
            "subject_name": "Giáo dục quốc phòng*",
            "details": "Nạp tệp điểm thô học phần quân sự GDQP102 qua API (hệ thống tự động kích hoạt Delta Pipeline làm tròn 0.1).",
            "timestamp": (now - datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    ACTIVITY_LOGS.extend(logs)
    TIMELINE_UPDATES.extend([
        {
            "id": "tl_1",
            "title": "Khoi tao du an SmartGPA",
            "category": "project",
            "details": "Tao backend, auth, simulation va seed du lieu demo.",
            "actor_email": "admin@smartgpa.edu",
            "timestamp": (now - datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
        },
        {
            "id": "tl_2",
            "title": "Ket noi Databricks pipeline",
            "category": "data",
            "details": "Upload diem kich hoat job Bronze/Silver/Gold tren Databricks.",
            "actor_email": "admin@smartgpa.edu",
            "timestamp": (now - datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
        },
    ])

# Seed activities immediately
_seed_demo_activities()


# ─── Semester Configuration ────────────────────────────────────
# Admin cập nhật mỗi đầu học kỳ mới
CURRENT_SEMESTER: dict = {
    "ma_hoc_ky": "HKII",
    "nam_hoc": "2025-2026",
    "display": "HKII 2025-2026"
}


# ─── Departments & Institutes DB (Khoa, Viện) ─────────────────
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

# ─── Majors DB (Ngành/Chuyên ngành) ───────────────────────────
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
    {"id": "DD_KHTP", "name": "Dinh dưỡng và Khoa học thực phẩm", "faculty_id": "KHSK"},

    # ─── VIỆN ───
    # 1. Viện Đào tạo Quốc tế và Sau đại học
    {"id": "DTQT_EN", "name": "Chương trình tăng cường tiếng Anh", "faculty_id": "DTQTSDH"},
    {"id": "DTQT_EN_FULL", "name": "Chương trình Tiếng Anh toàn phần (ngành *)", "faculty_id": "DTQTSDH"},
    {"id": "DTQT_TALENT", "name": "Chương trình Kỹ sư/Cử nhân tài năng (ngành **, ***)", "faculty_id": "DTQTSDH"},
    # 2. Viện Tài chính - Kế toán
    {"id": "KT", "name": "Kế toán", "faculty_id": "TCKT"},
    {"id": "KIMT", "name": "Kiểm toán", "faculty_id": "TCKT"},
    {"id": "KT_ACCA", "name": "Kế toán tích hợp chứng chỉ quốc tế ACCA", "faculty_id": "TCKT"},
    {"id": "KIMT_ICAEW", "name": "Kiểm toán tích hợp chứng chỉ quốc tế ICAEW", "faculty_id": "TCKT"},
    {"id": "TC", "name": "Tài chính ngân hàng (Chuyên ngành Tài chính)", "faculty_id": "TCKT"},
    {"id": "NH", "name": "Tài chính ngân hàng (Chuyên ngành Ngân hàng)", "faculty_id": "TCKT"},
    {"id": "CNTC", "name": "Công nghệ tài chính", "faculty_id": "TCKT"},
    # 3. Viện Công nghệ Sinh học và Thực phẩm
    {"id": "CNTP", "name": "Công nghệ thực phẩm", "faculty_id": "CNSHTP"},
    {"id": "CNSH", "name": "Công nghệ sinh học", "faculty_id": "CNSHTP"},
    # 4. Viện Khoa học Công nghệ và Quản lý Môi trường
    {"id": "QLDD", "name": "Quản lý đất đai (Chuyên ngành Quản lý đất đai)", "faculty_id": "KHCNQLMT"},
    {"id": "KTTNTN", "name": "Quản lý đất đai (Chuyên ngành Kinh tế tài nguyên thiên nhiên)", "faculty_id": "KHCNQLMT"},
    {"id": "QLTNMT", "name": "Quản lý tài nguyên và môi trường", "faculty_id": "KHCNQLMT"},
    {"id": "CNKTMT", "name": "Công nghệ kỹ thuật môi trường", "faculty_id": "KHCNQLMT"}
]


# ─── Courses DB (môn học) ──────────────────────────────────────
# Admin quản lý: thêm/sửa/xóa môn học. Mỗi học kỳ có thể cập nhật.
COURSES_DB: list[dict] = [
    {"id": "INT1001", "name": "Lập trình Python",                           "type": "tich_hop",  "credits": 3, "chi_lt": 2, "chi_th": 1, "faculty_id": "CNTT", "major_id": "CNTT_MAJ", "is_compulsory": True},
    {"id": "INT1002", "name": "Cơ sở dữ liệu",                             "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "HTTT", "is_compulsory": True},
    {"id": "GDQP102", "name": "Giáo dục quốc phòng*",                      "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "KHCB", "major_id": None, "is_compulsory": False},
    {"id": "mon_1",   "name": "Cấu trúc dữ liệu & Giải thuật",             "type": "ly_thuyet", "credits": 3, "chi_lt": 3, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KTPM", "is_compulsory": True},
    {"id": "mon_2",   "name": "Mạng máy tính",                             "type": "ly_thuyet", "credits": 2, "chi_lt": 2, "chi_th": 0, "faculty_id": "CNTT", "major_id": "KHMT", "is_compulsory": True},
    {"id": "mon_3",   "name": "Thực hành Hệ điều hành",                    "type": "thuc_hanh", "credits": 2, "chi_lt": 0, "chi_th": 2, "faculty_id": "CNTT", "major_id": "KTPM", "is_compulsory": True},
    {"id": "mon_4",   "name": "Thực hành Lập trình hướng đối tượng",       "type": "thuc_hanh", "credits": 3, "chi_lt": 0, "chi_th": 3, "faculty_id": "CNTT", "major_id": "KTPM", "is_compulsory": True},
]


# ─── Assignments DB (phân công giảng viên – lớp – môn) ────────
# Admin phân công: giảng viên nào dạy môn nào, lớp nào, trong học kỳ nào
ASSIGNMENTS_DB: list[dict] = [
    {"id": "asgn_1", "lecturer_id": "GV1001", "ma_mon": "INT1001", "ma_lop": "L01", "hoc_ky": "HKII 2025-2026"},
    {"id": "asgn_2", "lecturer_id": "GV1001", "ma_mon": "INT1002", "ma_lop": "L01", "hoc_ky": "HKII 2025-2026"},
    {"id": "asgn_3", "lecturer_id": "GV1001", "ma_mon": "mon_1",   "ma_lop": "L02", "hoc_ky": "HKII 2025-2026"},
    {"id": "asgn_4", "lecturer_id": "GV1002", "ma_mon": "mon_2",   "ma_lop": "L01", "hoc_ky": "HKII 2025-2026"},
    {"id": "asgn_5", "lecturer_id": "GV1002", "ma_mon": "mon_3",   "ma_lop": "L01", "hoc_ky": "HKII 2025-2026"},
    {"id": "asgn_6", "lecturer_id": "GV1002", "ma_mon": "mon_4",   "ma_lop": "L01", "hoc_ky": "HKII 2025-2026"},
    {"id": "asgn_7", "lecturer_id": "GV1002", "ma_mon": "GDQP102", "ma_lop": "L01", "hoc_ky": "HKII 2025-2026"},
]
