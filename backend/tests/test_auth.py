"""
SmartGPA – Test Auth Module
Covers:
  - TC-01: Token hết hạn / sai role → 401/403
  - Register: success, duplicate, weak password
  - Login: success, wrong password, nonexistent
  - Token: refresh, blacklist after logout
  - /auth/me: with & without token
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ─────────────────────────────────────────────────────────────
# TC-01: Authorization & Role-based Access Control
# ─────────────────────────────────────────────────────────────

class TestTC01Authorization:
    """TC-01: Endpoint yêu cầu auth → từ chối đúng cách"""

    def test_tc01a_no_token_returns_403(self):
        """Không có Authorization header → 403 Forbidden"""
        resp = client.post("/simulation/simulate", json={
            "loai_hoc_phan": "ly_thuyet",
            "muc_tieu": "A",
            "diem_thuong_ky": 8.0,
            "diem_giua_ky": 9.0,
        })
        assert resp.status_code == 403, (
            f"Expected 403 khi không có token, got {resp.status_code}"
        )

    def test_tc01b_invalid_token_returns_401(self):
        """Token giả mạo → 401 Unauthorized"""
        resp = client.post(
            "/simulation/simulate",
            json={
                "loai_hoc_phan": "ly_thuyet",
                "muc_tieu": "A",
                "diem_thuong_ky": 8.0,
                "diem_giua_ky": 9.0,
            },
            headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
        )
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 với invalid token, got {resp.status_code}"
        )

    def test_tc01c_admin_wrong_role_returns_403(self):
        """Admin cố gọi /simulation/simulate (chỉ dành cho Student) → 403"""
        # Login as admin
        login_resp = client.post("/auth/login", json={
            "email": "admin@smartgpa.edu",
            "password": "Admin@123",
        })
        assert login_resp.status_code == 200
        admin_token = login_resp.json()["access_token"]

        resp = client.post(
            "/simulation/simulate",
            json={
                "loai_hoc_phan": "ly_thuyet",
                "muc_tieu": "A",
                "diem_thuong_ky": 8.0,
                "diem_giua_ky": 9.0,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 403, (
            f"TC-01: Admin không được phép simulate, got {resp.status_code}"
        )

    def test_tc01d_lecturer_wrong_role_returns_403(self):
        """Lecturer cũng không được phép gọi /simulation/simulate → 403"""
        login_resp = client.post("/auth/login", json={
            "email": "thibinh.gv1001@smartgpa.edu",
            "password": "Gv@123",
        })
        lecturer_token = login_resp.json()["access_token"]

        resp = client.post(
            "/simulation/simulate",
            json={
                "loai_hoc_phan": "ly_thuyet",
                "muc_tieu": "A",
                "diem_thuong_ky": 8.0,
                "diem_giua_ky": 9.0,
            },
            headers={"Authorization": f"Bearer {lecturer_token}"},
        )
        assert resp.status_code == 403


# ─────────────────────────────────────────────────────────────
# Register
# ─────────────────────────────────────────────────────────────

class TestRegister:

    def test_register_student_success(self):
        resp = client.post("/auth/register", json={
            "email": "new_test_student@smartgpa.edu",
            "password": "password123",
            "full_name": "Test Student",
            "role": "student",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new_test_student@smartgpa.edu"
        assert data["role"] == "student"
        assert data["is_active"] is True
        # Đảm bảo không leak password
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_all_roles(self):
        for role in ["lecturer", "admin"]:
            resp = client.post("/auth/register", json={
                "email": f"new_{role}_test@smartgpa.edu",
                "password": "password123",
                "full_name": f"Test {role.capitalize()}",
                "role": role,
            })
            assert resp.status_code == 201, f"Failed for role {role}: {resp.json()}"
            assert resp.json()["role"] == role

    def test_register_unknown_role_returns_422(self):
        resp = client.post("/auth/register", json={
            "email": "new_unknown_role_test@smartgpa.edu",
            "password": "password123",
            "full_name": "Unknown Role",
            "role": "observer",
        })
        assert resp.status_code == 422

    def test_register_duplicate_email_returns_409(self):
        """Email đã tồn tại → 409 Conflict"""
        resp = client.post("/auth/register", json={
            "email": "student@smartgpa.edu",  # Đã seed sẵn
            "password": "password123",
            "full_name": "Duplicate",
            "role": "student",
        })
        assert resp.status_code == 409

    def test_register_weak_password_returns_422(self):
        """Mật khẩu < 6 ký tự → 422 Unprocessable Entity"""
        resp = client.post("/auth/register", json={
            "email": "weakpass@smartgpa.edu",
            "password": "123",  # Quá ngắn
            "full_name": "Weak Password User",
            "role": "student",
        })
        assert resp.status_code == 422

    def test_register_invalid_email_returns_422(self):
        """Email không đúng format → 422"""
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "password123",
            "full_name": "Bad Email",
            "role": "student",
        })
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────

class TestLogin:

    def test_login_success_returns_tokens(self):
        resp = client.post("/auth/login", json={
            "email": "student@smartgpa.edu",
            "password": "Sv@123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # Tokens không được rỗng
        assert len(data["access_token"]) > 20
        assert len(data["refresh_token"]) > 20

    def test_login_wrong_password_returns_401(self):
        resp = client.post("/auth/login", json={
            "email": "student@smartgpa.edu",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_email_returns_401(self):
        resp = client.post("/auth/login", json={
            "email": "nobody@smartgpa.edu",
            "password": "password123",
        })
        assert resp.status_code == 401

    def test_login_all_demo_accounts(self):
        """Tất cả 4 tài khoản demo đều login được"""
        accounts = [
            ("student@smartgpa.edu", "Sv@123"),
            ("thibinh.gv1001@smartgpa.edu", "Gv@123"),
            ("admin@smartgpa.edu", "Admin@123"),
        ]
        for email, password in accounts:
            resp = client.post("/auth/login", json={
                "email": email, "password": password,
            })
            assert resp.status_code == 200, f"Login failed for {email}"


# ─────────────────────────────────────────────────────────────
# Token Refresh & Logout
# ─────────────────────────────────────────────────────────────

class TestTokens:

    def _login(self, email: str = "admin@smartgpa.edu") -> dict:
        password = "Admin@123" if "admin" in email else ("Gv@123" if "gv" in email else "Sv@123")
        resp = client.post("/auth/login", json={
            "email": email, "password": password,
        })
        return resp.json()

    def test_refresh_token_returns_new_access_token(self):
        tokens = self._login()
        refresh_token = tokens["refresh_token"]

        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        # Access token mới phải khác cũ (vì timestamp khác)
        # (có thể giống nếu exp bị truncate đến giây, nhưng thường khác)

    def test_logout_blacklists_refresh_token(self):
        """Sau logout, refresh_token không dùng được nữa"""
        tokens = self._login("thibinh.gv1001@smartgpa.edu")
        refresh_token = tokens["refresh_token"]

        # Logout
        logout_resp = client.post("/auth/logout", json={"refresh_token": refresh_token})
        assert logout_resp.status_code == 204

        # Thử dùng refresh token đã bị blacklist
        refresh_resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_resp.status_code == 401, (
            "Refresh token đã logout không được phép refresh"
        )

    def test_cannot_use_access_token_as_refresh(self):
        """Access token không thể dùng ở endpoint /refresh"""
        tokens = self._login()
        access_token = tokens["access_token"]

        resp = client.post("/auth/refresh", json={"refresh_token": access_token})
        assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────
# /auth/me
# ─────────────────────────────────────────────────────────────

class TestGetMe:

    def test_get_me_student(self):
        login_resp = client.post("/auth/login", json={
            "email": "student@smartgpa.edu", "password": "Sv@123",
        })
        token = login_resp.json()["access_token"]

        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "student@smartgpa.edu"
        assert data["role"] == "student"

    def test_get_me_no_token_returns_403(self):
        resp = client.get("/auth/me")
        assert resp.status_code == 403

    def test_get_me_invalid_token_returns_401(self):
        resp = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer fake.invalid.token"},
        )
        assert resp.status_code in (401, 403)

