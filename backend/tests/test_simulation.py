"""
SmartGPA – Test Simulation Engine
Covers:
  - TC-05: Môn Lý thuyết – TK_list=[8.0, 8.0], GK=9.0, mục tiêu A → CK_min = 8.4
  - TC-06: Môn Tích hợp – 2LT+1TH, TH=8.0, mục tiêu A → T_LT_min = 8.8
  - TC-07: Điểm quá thấp → "Bất khả thi"
  - Thực hành: basic & infeasible & liệt thực hành
  - Score map: 9 dòng đầy đủ với dải điểm C/C+ mới
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_student_token() -> str:
    resp = client.post("/auth/login", json={
        "email": "student@smartgpa.edu",
        "password": "password123",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _simulate(payload: dict, token: str | None = None) -> dict:
    """Helper: gọi /simulation/simulate với student token"""
    if token is None:
        token = _get_student_token()
    resp = client.post(
        "/simulation/simulate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp


# ─────────────────────────────────────────────────────────────
# TC-05: Lý thuyết – tính điểm cuối kỳ cần đạt
# ─────────────────────────────────────────────────────────────

class TestTC05LyThuyet:
    """
    TC-05: Môn Lý thuyết, TK_list=[8.0, 8.0], so_tin_chi=2, GK=9.0, mục tiêu A (ngưỡng 8.5)
    ĐTB_TK = 8.0
    CK_min = (8.5 - 0.2×8.0 - 0.3×9.0) / 0.5 = (8.5 - 1.6 - 2.7) / 0.5 = 8.4
    """

    def test_tc05_basic_inverse_ly_thuyet(self):
        resp = _simulate({
            "loai_hoc_phan": "ly_thuyet",
            "muc_tieu": "A",
            "so_tin_chi": 2,
            "diem_thuong_ky_list": [8.0, 8.0],
            "diem_giua_ky": 9.0,
        })
        assert resp.status_code == 200
        data = resp.json()

        assert data["is_kha_thi"] is True
        assert data["diem_muc_tieu_nguong"] == 8.5  # Ngưỡng A = 8.5
        assert data["diem_can_dat"] == 8.4           # CK_min = 8.4
        assert "cuối kỳ" in data["message"].lower() or "điểm" in data["message"].lower()

    def test_tc05_verify_chi_tiet(self):
        """chi_tiet phải có công thức và các điểm thành phần"""
        resp = _simulate({
            "loai_hoc_phan": "ly_thuyet",
            "muc_tieu": "A",
            "so_tin_chi": 2,
            "diem_thuong_ky_list": [8.0, 8.0],
            "diem_giua_ky": 9.0,
        })
        data = resp.json()
        chi_tiet = data["chi_tiet"]

        assert "cong_thuc" in chi_tiet
        assert chi_tiet["diem_thuong_ky_trung_binh"] == 8.0
        assert chi_tiet["diem_giua_ky"] == 9.0

    def test_tc05_target_b_plus(self):
        """Mục tiêu B+ (ngưỡng 8.0): CK = (8.0 - 1.6 - 2.7) / 0.5 = 7.4"""
        resp = _simulate({
            "loai_hoc_phan": "ly_thuyet",
            "muc_tieu": "B+",
            "so_tin_chi": 2,
            "diem_thuong_ky_list": [8.0, 8.0],
            "diem_giua_ky": 9.0,
        })
        data = resp.json()
        assert data["is_kha_thi"] is True
        assert data["diem_muc_tieu_nguong"] == 8.0
        assert data["diem_can_dat"] == pytest.approx(7.4, abs=0.1)

    def test_tc05_invalid_list_length(self):
        """Số đầu điểm không bằng số tín chỉ → lỗi"""
        resp = _simulate({
            "loai_hoc_phan": "ly_thuyet",
            "muc_tieu": "A",
            "so_tin_chi": 3,  # Cần 3 điểm
            "diem_thuong_ky_list": [8.0, 8.0],  # Chỉ truyền 2 điểm
            "diem_giua_ky": 9.0,
        })
        data = resp.json()
        assert data["is_kha_thi"] is False
        assert "bằng đúng số tín chỉ" in data["message"]

    def test_tc05_missing_scores_returns_infeasible(self):
        """Thiếu TK/GK → is_kha_thi = False"""
        resp = _simulate({
            "loai_hoc_phan": "ly_thuyet",
            "muc_tieu": "A",
            # Không có diem_thuong_ky_list, diem_giua_ky
        })
        data = resp.json()
        assert data["is_kha_thi"] is False

    def test_tc05_guaranteed_when_already_passing(self):
        """Điểm TK + GK đã đủ → is_kha_thi True, diem_can_dat = 0.0"""
        resp = _simulate({
            "loai_hoc_phan": "ly_thuyet",
            "muc_tieu": "D",          # Ngưỡng D = 4.0
            "so_tin_chi": 2,
            "diem_thuong_ky_list": [9.0, 9.0],
            "diem_giua_ky": 9.0,
        })
        data = resp.json()
        assert data["is_kha_thi"] is True
        assert data["diem_can_dat"] == 0.0


# ─────────────────────────────────────────────────────────────
# TC-06: Tích hợp – tính điểm nhánh LT cần đạt
# ─────────────────────────────────────────────────────────────

class TestTC06TichHop:
    """
    TC-06: Tích hợp (2LT + 1TH), TH=8.0, mục tiêu A (ngưỡng 8.5)
    T_LT = (8.5×3 - 8.0×1) / 2 = (25.5 - 8.0) / 2 = 8.75
    ceil(8.75 × 10) / 10 = ceil(87.5) / 10 = 88/10 = 8.8
    """

    def test_tc06_basic_inverse_tich_hop(self):
        resp = _simulate({
            "loai_hoc_phan": "tich_hop",
            "muc_tieu": "A",
            "so_chi_lt": 2,
            "so_chi_th": 1,
            "diem_thuc_hanh_tich_hop": 8.0,
        })
        assert resp.status_code == 200
        data = resp.json()

        assert data["is_kha_thi"] is True
        assert data["diem_muc_tieu_nguong"] == 8.5
        assert data["diem_can_dat"] == 8.8  # TC-06 expected
        assert "lý thuyết" in data["message"].lower() or "T_LT" in str(data["chi_tiet"])

    def test_tc06_drill_down_with_lt_scores(self):
        """
        Thêm TK_lt_list=[8.0, 8.0], GK_lt=8.0 → tính sâu hơn CK_lt:
        T_LT_needed = 8.8
        CK_lt = (8.8 - 0.2×8.0 - 0.3×8.0) / 0.5 = (8.8 - 1.6 - 2.4) / 0.5 = 9.6
        """
        resp = _simulate({
            "loai_hoc_phan": "tich_hop",
            "muc_tieu": "A",
            "so_chi_lt": 2,
            "so_chi_th": 1,
            "diem_thuc_hanh_tich_hop": 8.0,
            "diem_thuong_ky_lt_list": [8.0, 8.0],
            "diem_giua_ky_lt": 8.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_kha_thi"] is True
        assert "ck_lt_can_dat_chinh_xac" in data["chi_tiet"]
        assert data["diem_can_dat"] == pytest.approx(9.6, abs=0.1)

    def test_tc06_drill_down_invalid_list_length(self):
        """Điểm thường kỳ LT không bằng số tín chỉ LT → lỗi"""
        resp = _simulate({
            "loai_hoc_phan": "tich_hop",
            "muc_tieu": "A",
            "so_chi_lt": 2,
            "so_chi_th": 1,
            "diem_thuc_hanh_tich_hop": 8.0,
            "diem_thuong_ky_lt_list": [8.0],  # Chỉ truyền 1 điểm trong khi so_chi_lt = 2
            "diem_giua_ky_lt": 8.0,
        })
        data = resp.json()
        assert data["is_kha_thi"] is False
        assert "bằng đúng số tín chỉ lý thuyết" in data["message"]

    def test_tc06_practical_failure_lock(self):
        """Điểm thực hành tích hợp < 3.0 → Liệt thực hành (Khóa phép toán)"""
        resp = _simulate({
            "loai_hoc_phan": "tich_hop",
            "muc_tieu": "A",
            "so_chi_lt": 2,
            "so_chi_th": 1,
            "diem_thuc_hanh_tich_hop": 2.5,  # Liệt thực hành!
        })
        data = resp.json()
        assert data["is_kha_thi"] is False
        assert "LIET THUC HANH" in data["message"]

    def test_tc06_missing_fields_returns_error(self):
        """Thiếu fields bắt buộc → is_kha_thi = False"""
        resp = _simulate({
            "loai_hoc_phan": "tich_hop",
            "muc_tieu": "A",
            # Thiếu so_chi_lt, so_chi_th, diem_thuc_hanh_tich_hop
        })
        data = resp.json()
        assert data["is_kha_thi"] is False

    def test_tc06_equal_credits(self):
        """2LT + 2TH = 4 tổng, TH=7.0, target A (8.5):
        T_LT = (8.5×4 - 7.0×2) / 2 = (34 - 14) / 2 = 10.0"""
        resp = _simulate({
            "loai_hoc_phan": "tich_hop",
            "muc_tieu": "A",
            "so_chi_lt": 2,
            "so_chi_th": 2,
            "diem_thuc_hanh_tich_hop": 7.0,
        })
        data = resp.json()
        assert data["is_kha_thi"] is True
        assert data["diem_can_dat"] == 10.0  # Chính xác 10.0 = khả thi


# ─────────────────────────────────────────────────────────────
# TC-07: Bất khả thi
# ─────────────────────────────────────────────────────────────

class TestTC07BatKhaThi:
    """TC-07: Điểm hiện tại quá thấp → Mục tiêu Bất khả thi"""

    def test_tc07_infeasible_ly_thuyet_a_plus(self):
        """TK=[2.0, 2.0], so_tin_chi=2, GK=1.0, mục tiêu A+ → CK cần (9.0 - 0.4 - 0.3)/0.5 = 16.6 > 10"""
        resp = _simulate({
            "loai_hoc_phan": "ly_thuyet",
            "muc_tieu": "A+",
            "so_tin_chi": 2,
            "diem_thuong_ky_list": [2.0, 2.0],
            "diem_giua_ky": 1.0,
        })
        assert resp.status_code == 200
        data = resp.json()

        assert data["is_kha_thi"] is False
        assert data["diem_can_dat"] is None
        assert "Bất khả thi" in data["message"]

    def test_tc07_infeasible_tich_hop(self):
        """TH=3.0, chi_lt=1, chi_th=3, mục tiêu A → T_LT = (8.5×4 - 3.0×3)/1 = 25 > 10"""
        resp = _simulate({
            "loai_hoc_phan": "tich_hop",
            "muc_tieu": "A",
            "so_chi_lt": 1,
            "so_chi_th": 3,
            "diem_thuc_hanh_tich_hop": 3.0,
        })
        data = resp.json()
        assert data["is_kha_thi"] is False
        assert "Bất khả thi" in data["message"]

    def test_tc07_infeasible_thuc_hanh(self):
        """TH đã có [1, 1, 1], so_tin_chi 4 buổi, mục tiêu A+ (9.0):
        score_needed = (9.0×4 - 3) / 1 = 33 > 10 → Bất khả thi"""
        resp = _simulate({
            "loai_hoc_phan": "thuc_hanh",
            "muc_tieu": "A+",
            "diem_thuc_hanh_hien_tai": [1.0, 1.0, 1.0],
            "so_tin_chi": 4,
        })
        data = resp.json()
        assert data["is_kha_thi"] is False
        assert "Bất khả thi" in data["message"]


# ─────────────────────────────────────────────────────────────
# Thực hành
# ─────────────────────────────────────────────────────────────

class TestThucHanh:

    def test_thuc_hanh_basic(self):
        """existing=[7.0, 8.0], tín chỉ=4, mục tiêu B+ (8.0):
        score_needed = (8.0×4 - 15.0) / 2 = 8.5"""
        resp = _simulate({
            "loai_hoc_phan": "thuc_hanh",
            "muc_tieu": "B+",
            "diem_thuc_hanh_hien_tai": [7.0, 8.0],
            "so_tin_chi": 4,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_kha_thi"] is True
        assert data["diem_can_dat"] == 8.5

    def test_thuc_hanh_already_completed(self):
        """Đã hoàn thành tất cả buổi → không có buổi còn lại"""
        resp = _simulate({
            "loai_hoc_phan": "thuc_hanh",
            "muc_tieu": "A",
            "diem_thuc_hanh_hien_tai": [9.0, 8.5, 9.5],
            "so_tin_chi": 3,
        })
        data = resp.json()
        assert data["is_kha_thi"] is True
        assert data["diem_can_dat"] is None

    def test_thuc_hanh_liet_already_completed(self):
        """Đã hoàn thành nhưng ĐTB thực hành < 3.0 → Cảnh báo liệt"""
        resp = _simulate({
            "loai_hoc_phan": "thuc_hanh",
            "muc_tieu": "D",
            "diem_thuc_hanh_hien_tai": [2.0, 2.0, 2.0],
            "so_tin_chi": 3,
        })
        data = resp.json()
        assert data["is_kha_thi"] is False
        assert "LIET THUC HANH" in data["message"]

    def test_thuc_hanh_liet_mathematically_unavoidable(self):
        """Chưa hoàn thành hết nhưng không thể cứu vãn khỏi bị liệt (< 3.0)
        so_tin_chi=5, existing=[0.0, 0.0, 0.0, 0.0], remaining=1
        max_possible = (0 + 10)/5 = 2.0 < 3.0 → Liệt thực hành!
        """
        resp = _simulate({
            "loai_hoc_phan": "thuc_hanh",
            "muc_tieu": "D",
            "diem_thuc_hanh_hien_tai": [0.0, 0.0, 0.0, 0.0],
            "so_tin_chi": 5,
        })
        data = resp.json()
        assert data["is_kha_thi"] is False
        assert "LIET THUC HANH" in data["message"]

    def test_thuc_hanh_missing_total_sessions(self):
        """Không có so_tin_chi hay tong_so_buoi → is_kha_thi = False"""
        resp = _simulate({
            "loai_hoc_phan": "thuc_hanh",
            "muc_tieu": "A",
            "diem_thuc_hanh_hien_tai": [8.0, 8.0],
        })
        data = resp.json()
        assert data["is_kha_thi"] is False


# ─────────────────────────────────────────────────────────────
# Score Map
# ─────────────────────────────────────────────────────────────

class TestScoreMap:

    def test_get_score_map_returns_9_grades(self):
        """Bảng quy đổi phải có đủ 9 mức: A+, A, B+, B, C+, C, D+, D, F"""
        token = _get_student_token()
        resp = client.get(
            "/simulation/score-map",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 9

        grades = {item["diem_chu"] for item in data}
        expected = {"A+", "A", "B+", "B", "C+", "C", "D+", "D", "F"}
        assert grades == expected

    def test_score_map_f_grade_is_not_dat(self):
        """F phải là 'Không Đạt'"""
        token = _get_student_token()
        resp = client.get(
            "/simulation/score-map",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = resp.json()
        f_grade = next(item for item in data if item["diem_chu"] == "F")
        assert f_grade["loai_danh_gia"] == "Không Đạt"
        assert f_grade["diem_he_4"] == 0.0

    def test_score_map_c_plus_and_c_ranges(self):
        """C+ phải từ 6.0 đến 6.9, C phải từ 5.5 đến 5.9 theo quy chế mới"""
        token = _get_student_token()
        resp = client.get(
            "/simulation/score-map",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = resp.json()
        c_plus = next(item for item in data if item["diem_chu"] == "C+")
        c = next(item for item in data if item["diem_chu"] == "C")

        assert c_plus["diem_10_min"] == 6.0
        assert c_plus["diem_10_max"] == 6.9
        assert c["diem_10_min"] == 5.5
        assert c["diem_10_max"] == 5.9

    def test_score_map_requires_auth(self):
        """Không có token → 403"""
        resp = client.get("/simulation/score-map")
        assert resp.status_code == 403
