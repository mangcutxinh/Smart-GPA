"""
SmartGPA – Auth Service
Business logic: register, login, refresh token, logout
"""
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import random
import smtplib
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def send_email(to_email: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Chua cau hinh SMTP de gui email that. Vui long thiet lap SMTP_HOST, "
                "SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD va SMTP_FROM_EMAIL trong backend/.env."
            ),
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Khong gui duoc email OTP qua SMTP: {exc}",
        )
from app.db.real_db import BLACKLIST, PASSWORD_RESET_OTPS, USERS_DB, find_user_by_login, user_login_key
from app.models.schemas import (
    AccessTokenResponse,
    PasswordChangeWithOtp,
    PasswordOtpRequest,
    PasswordOtpResponse,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
    UserRole,
)


def _user_out(user: dict) -> UserOut:
    return UserOut(
        id=user["id"],
        email=user.get("email") or user.get("username", ""),
        username=user.get("username"),
        full_name=user["full_name"],
        role=UserRole(user["role"]),
        is_active=user["is_active"],
        created_at=user["created_at"],
        student_id=user.get("student_id"),
        lecturer_id=user.get("lecturer_id"),
        faculty_id=user.get("faculty_id"),
        major_id=user.get("major_id"),
        must_change_password=bool(user.get("must_change_password", False)),
        email_verified=bool(user.get("email_verified", False)),
    )


def register_user(user_data: UserCreate) -> UserOut:
    """
    Đăng ký tài khoản mới.
    - Kiểm tra email trùng lặp
    - Hash mật khẩu bcrypt
    - Lưu vào USERS_DB
    """
    if user_data.email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{user_data.email}' đã được đăng ký. Vui lòng dùng email khác.",
        )

    user_id = str(uuid4())
    now = datetime.now(timezone.utc)

    new_user = {
        "id": user_id,
        "email": str(user_data.email),
        "username": str(user_data.email),
        "password_hash": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "role": user_data.role.value,
        "is_active": True,
        "created_at": now,
        "notifications": [],
        "must_change_password": False,
        "email_verified": True,
    }
    USERS_DB[user_login_key(new_user)] = new_user

    return _user_out(new_user)



def login_user(login_data: UserLogin) -> Token:
    """
    Đăng nhập với email + mật khẩu.
    Trả về Access Token (30 phút) + Refresh Token (7 ngày).
    """
    user = find_user_by_login(str(login_data.email))

    # Dùng thông điệp chung để tránh user enumeration
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa. Liên hệ Admin để được hỗ trợ.",
        )

    token_payload = {
        "sub": user_login_key(user),
        "role": user["role"],
        "uid": user["id"],
    }
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        must_change_password=bool(user.get("must_change_password", False)),
        username=user.get("username"),
    )


def refresh_access_token(refresh_token: str) -> AccessTokenResponse:
    """
    Làm mới Access Token bằng Refresh Token còn hiệu lực.
    Raise 401 nếu token đã bị blacklist hoặc không hợp lệ.
    """
    if refresh_token in BLACKLIST:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token đã bị thu hồi. Vui lòng đăng nhập lại.",
        )

    payload = decode_token(refresh_token)  # Raises 401 nếu hết hạn / sai

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ. Cần dùng Refresh Token.",
        )

    login_key = payload.get("sub", "")
    user = find_user_by_login(login_key)
    if not user or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại hoặc đã bị vô hiệu hóa.",
        )

    new_access_token = create_access_token({
        "sub": user_login_key(user),
        "role": user["role"],
        "uid": user["id"],
    })
    return AccessTokenResponse(access_token=new_access_token)


def logout_user(refresh_token: str) -> None:
    """
    Thu hồi Refresh Token (thêm vào blacklist).
    Sau khi logout, refresh_token này không thể dùng để lấy access token mới.
    """
    BLACKLIST.add(refresh_token)


def request_password_otp(body: PasswordOtpRequest) -> PasswordOtpResponse:
    user = find_user_by_login(body.username)
    if not user or user.get("role") != UserRole.STUDENT.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay tai khoan sinh vien.")

    otp = f"{random.randint(0, 999999):06d}"
    login_key = user_login_key(user)
    email = str(body.email)
    user["pending_email"] = email
    PASSWORD_RESET_OTPS[login_key] = {
        "otp": otp,
        "email": email,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
    }

    send_email(
        email,
        "[SmartGPA] Ma OTP doi mat khau",
        (
            f"Xin chao {user.get('full_name', 'sinh vien')},\n\n"
            f"Ma OTP doi mat khau SmartGPA cua ban la: {otp}\n"
            "Ma co hieu luc trong 10 phut. Neu ban khong yeu cau doi mat khau, vui long bo qua email nay.\n\n"
            "SmartGPA"
        ),
    )
    return PasswordOtpResponse(
        message="Da gui ma OTP den email.",
        username=login_key,
        email=email,
    )


def change_password_with_otp(body: PasswordChangeWithOtp) -> UserOut:
    user = find_user_by_login(body.username)
    if not user or user.get("role") != UserRole.STUDENT.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay tai khoan sinh vien.")

    login_key = user_login_key(user)
    otp_record = PASSWORD_RESET_OTPS.get(login_key)
    if not otp_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chua yeu cau OTP hoac OTP da het han.")
    if otp_record["expires_at"] < datetime.now(timezone.utc):
        PASSWORD_RESET_OTPS.pop(login_key, None)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP da het han.")
    if str(body.otp).strip() != otp_record["otp"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP khong chinh xac.")

    user["password_hash"] = hash_password(body.new_password)
    user["email"] = otp_record["email"]
    user["email_verified"] = True
    user["must_change_password"] = False
    user.pop("pending_email", None)
    PASSWORD_RESET_OTPS.pop(login_key, None)
    return _user_out(user)
