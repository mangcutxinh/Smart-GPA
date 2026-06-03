"""
SmartGPA – Data Integration & Upload Tests
Covers:
  - TC-02: Fail-Fast CSV/Excel file validation with descriptive row errors.
  - S3/Azure Storage renaming & file isolation.
  - /simulation/calc Databricks-integrated inverse GPA calculations.
"""
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _get_token(email: str) -> str:
    resp = client.post("/auth/login", json={
        "email": email,
        "password": "password123",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ─── Upload Hub Validation Tests (TC-02) ───────────────────────────────────

class TestUploadHubValidation:
    """TC-02: Giảng viên upload file danh sách điểm định dạng không hợp lệ"""

    def test_upload_invalid_file_extension(self):
        """Chỉ chấp nhận .csv hoặc .xlsx. File .txt phải bị từ chối 422."""
        token = _get_token("thibinh.gv1001@smartgpa.edu")
        file_payload = {"file": ("diem_thi.txt", b"student_id,ma_mon\nSV1,INT1", "text/plain")}
        
        resp = client.post(
            "/upload/file",
            files=file_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 422
        assert "Định dạng file không hợp lệ" in resp.json()["detail"]

    def test_upload_missing_required_headers(self):
        """Thiếu các cột bắt buộc (ví dụ: thiếu loai_hoc_phan) -> 422."""
        token = _get_token("thibinh.gv1001@smartgpa.edu")
        csv_data = "student_id,ma_mon,ma_lop_hoc_phan\nSV123,INT1306,L01\n"
        file_payload = {"file": ("diem.csv", csv_data.encode("utf-8"), "text/csv")}
        
        resp = client.post(
            "/upload/file",
            files=file_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 422
        assert "Thiếu các cột bắt buộc" in resp.json()["detail"]

    def test_upload_grade_out_of_range(self):
        """Đầu điểm vượt quá dải 0.0 - 10.0 -> trả lỗi dòng chi tiết (Fail-Fast)."""
        token = _get_token("thibinh.gv1001@smartgpa.edu")
        csv_data = (
            "student_id,ma_mon,ma_lop_hoc_phan,loai_hoc_phan,diem_giua_ky,diem_thong_thuong\n"
            "SV123456,INT1306,L01,ly_thuyet,8.5,12.0\n"  # Lỗi 12.0 ở thường kỳ
        )
        file_payload = {"file": ("diem.csv", csv_data.encode("utf-8"), "text/csv")}
        
        resp = client.post(
            "/upload/file",
            files=file_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "Dữ liệu file chứa dòng lỗi" in detail["message"]
        assert "Dòng 2" in detail["errors"][0]
        assert "12.0" in detail["errors"][0]

    def test_upload_invalid_course_type(self):
        """Loại học phần sai quy chuẩn -> lỗi dòng chi tiết."""
        token = _get_token("thibinh.gv1001@smartgpa.edu")
        csv_data = (
            "student_id,ma_mon,ma_lop_hoc_phan,loai_hoc_phan,diem_giua_ky\n"
            "SV123456,INT1306,L01,unknown_type,8.5\n"
        )
        file_payload = {"file": ("diem.csv", csv_data.encode("utf-8"), "text/csv")}
        
        resp = client.post(
            "/upload/file",
            files=file_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 422
        assert "unknown_type" in resp.json()["detail"]["errors"][0]


# ─── End-to-End Upload & Query Integration Tests ──────────────────────────────

class TestDataIntegrationE2E:
    """Kiểm thử liên thông: Upload file điểm -> Tự động nạp Delta -> Giả lập ngược"""

    def test_e2e_successful_upload_and_simulation(self):
        # 1. Đăng nhập với tư cách Giảng viên để nạp điểm thô
        lecturer_token = _get_token("thibinh.gv1001@smartgpa.edu")
        
        # Tạo file điểm CSV hợp lệ của sinh viên mới SV999888 môn INT1306 (Lý thuyết)
        csv_data = (
            "student_id,ma_mon,ma_lop_hoc_phan,loai_hoc_phan,diem_giua_ky,diem_thong_thuong\n"
            "SV999888,INT1306,L01,ly_thuyet,8.0,8.5;9.5\n"
        )
        file_payload = {"file": ("diem_thi_lop_A.csv", csv_data.encode("utf-8"), "text/csv")}
        
        upload_resp = client.post(
            "/upload/file",
            files=file_payload,
            headers={"Authorization": f"Bearer {lecturer_token}"}
        )
        assert upload_resp.status_code == 201
        res = upload_resp.json()
        assert "thành công" in res["message"]
        assert "diem_thao_L01_" in res["filename"]
        assert res["pipeline_status"] == "COMPLETED"
        assert res["databricks_run_id"]
        
        # 2. ??ng nh?p v?i t? c?ch Sinh vi?n ?? ch?y gi? l?p ?i?m t?ch h?p Databricks
        student_token = _get_token("student@smartgpa.edu")
        
        # Yêu cầu giả lập tính điểm ngược cho SV999888 môn INT1306 vừa nạp điểm thô
        calc_payload = {
            "student_id": "SV999888",
            "ma_mon": "INT1306",
            "diem_chu_muc_tieu": "A"  # Mục tiêu A (ngưỡng 8.5)
        }
        
        calc_resp = client.post(
            "/simulation/calc",
            json=calc_payload,
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert calc_resp.status_code == 200
        sim_res = calc_resp.json()
        
        # TK_trung_binh = (8.5 + 9.5)/2 = 9.0
        # GK = 8.0
        # Base = 0.2*9.0 + 0.3*8.0 = 1.8 + 2.4 = 4.2
        # CK_chinh_xac = (8.5 - 4.2)/0.5 = 8.6
        assert sim_res["is_kha_thi"] is True
        assert sim_res["diem_muc_tieu_nguong"] == 8.5
        assert sim_res["diem_can_dat"] == pytest.approx(8.6, abs=0.1)
        assert sim_res["chi_tiet"]["diem_thuong_ky_trung_binh"] == 9.0
        assert sim_res["chi_tiet"]["diem_giua_ky"] == 8.0

    def test_uploaded_scores_auto_create_student_account_and_otp_password_change(self, monkeypatch):
        from app.db.databricks_db import save_uploaded_scores_mock
        from app.db.fake_db import PASSWORD_RESET_OTPS, USERS_DB
        from app.services import auth_service

        sent_emails = []

        def fake_send_email(to_email: str, subject: str, body: str) -> None:
            sent_emails.append({"to": to_email, "subject": subject, "body": body})

        monkeypatch.setattr(auth_service, "send_email", fake_send_email)

        rows = [{
            "student_id": "SV777888",
            "student_name": "Nguyen Van Test",
            "ma_mon": "INT1306",
            "ma_lop_hoc_phan": "L01",
            "loai_hoc_phan": "ly_thuyet",
            "diem_giua_ky": 7.0,
            "diem_thong_thuong_list": [7.5, 8.0],
        }]

        assert save_uploaded_scores_mock(rows) == 1
        username = "sv777888.vantest"
        assert username in USERS_DB
        assert USERS_DB[username]["must_change_password"] is True
        assert USERS_DB[username]["email_verified"] is False

        login_resp = client.post("/auth/login", json={"email": username, "password": "password123"})
        assert login_resp.status_code == 200
        assert login_resp.json()["must_change_password"] is True

        mssv_login_resp = client.post("/auth/login", json={"email": "SV777888", "password": "password123"})
        assert mssv_login_resp.status_code == 200

        otp_resp = client.post("/auth/password/request-otp", json={
            "username": "SV777888",
            "email": "sv777888@example.com",
        })
        assert otp_resp.status_code == 200
        assert otp_resp.json().get("dev_otp") is None
        assert sent_emails and sent_emails[0]["to"] == "sv777888@example.com"
        otp = PASSWORD_RESET_OTPS[username]["otp"]

        change_resp = client.post("/auth/password/change-with-otp", json={
            "username": "SV777888",
            "otp": otp,
            "new_password": "newpass123",
        })
        assert change_resp.status_code == 200
        changed = change_resp.json()
        assert changed["email"] == "sv777888@example.com"
        assert changed["must_change_password"] is False
        assert changed["email_verified"] is True

        new_login_resp = client.post("/auth/login", json={"email": username, "password": "newpass123"})
        assert new_login_resp.status_code == 200

    def test_query_non_existent_student_scores(self):
        """Query mã SV hoặc môn học không tồn tại -> 404 Not Found."""
        student_token = _get_token("student@smartgpa.edu")
        calc_payload = {
            "student_id": "SV_UNKNOWN",
            "ma_mon": "INT1306",
            "diem_chu_muc_tieu": "A"
        }
        
        resp = client.post(
            "/simulation/calc",
            json=calc_payload,
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert resp.status_code == 404
        assert "Không tìm thấy bảng điểm" in resp.json()["detail"]

    def test_lay_diem_sinh_vien_tu_cloud_fallback(self):
        """Kiểm thử hàm lay_diem_sinh_vien_tu_cloud khi chạy cục bộ với fallback mock data"""
        from app.db.databricks_db import lay_diem_sinh_vien_tu_cloud
        
        # Thử truy vấn SV123456 môn INT1306 (đã được seed sẵn trong MOCK_GOLD_DB)
        res = lay_diem_sinh_vien_tu_cloud("SV123456", "INT1306")
        assert res is not None
        
        # Cấu trúc tuple: (diem_tich_luy_hien_tai, loai_hoc_phan, tong_so_chi, diem_trung_binh_thuc_hanh, diem_chu_hien_tai, status_canh_bao_final)
        diem_tich_luy, loai_hp, tong_so_chi, diem_tb_th, diem_chu, status_canh_bao = res
        assert loai_hp == "ly_thuyet"
        assert tong_so_chi == 2
        assert status_canh_bao == "An toan"
        assert diem_chu == "B+"
        
        # Thử truy vấn SV không tồn tại
        res_none = lay_diem_sinh_vien_tu_cloud("SV_KHONG_TON_TAI", "INT1306")
        assert res_none is None
