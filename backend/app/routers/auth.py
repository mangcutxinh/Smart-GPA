"""
SmartGPA – Auth Router
Endpoints: /auth/register, /auth/login, /auth/refresh, /auth/logout, /auth/me
"""
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user
from app.models.schemas import (
    AccessTokenResponse,
    PasswordChangeWithOtp,
    PasswordOtpRequest,
    PasswordOtpResponse,
    RefreshRequest,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.services.auth_service import (
    change_password_with_otp,
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
    request_password_otp,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới",
    description="""
Tạo tài khoản mới với 1 trong 3 vai trò: **student / lecturer / admin**.

- Mật khẩu được mã hóa bằng **bcrypt** trước khi lưu.
- Email phải là duy nhất trong hệ thống.
- Mật khẩu tối thiểu 6 ký tự.
    """,
)
def register(user_data: UserCreate) -> UserOut:
    return register_user(user_data)


@router.post(
    "/login",
    response_model=Token,
    summary="Đăng nhập → nhận JWT tokens",
    description="""
Xác thực bằng email + mật khẩu.

Trả về:
- **access_token**: JWT, hết hạn sau **30 phút**. Dùng để gọi các protected endpoints.
- **refresh_token**: JWT, hết hạn sau **7 ngày**. Dùng để lấy access_token mới.
    """,
)
def login(login_data: UserLogin) -> Token:
    return login_user(login_data)


@router.post(
    "/password/request-otp",
    response_model=PasswordOtpResponse,
    summary="Sinh vien khai bao email va lay OTP doi mat khau",
)
def request_change_password_otp(body: PasswordOtpRequest) -> PasswordOtpResponse:
    return request_password_otp(body)


@router.post(
    "/password/change-with-otp",
    response_model=UserOut,
    summary="Sinh vien doi mat khau bang OTP",
)
def change_password_otp(body: PasswordChangeWithOtp) -> UserOut:
    return change_password_with_otp(body)


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Làm mới Access Token",
    description="Dùng **refresh_token** còn hiệu lực để lấy **access_token** mới (không cần đăng nhập lại).",
)
def refresh(body: RefreshRequest) -> AccessTokenResponse:
    return refresh_access_token(body.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Đăng xuất (thu hồi Refresh Token)",
    description="Thêm **refresh_token** vào blacklist. Token này sẽ không thể dùng sau khi logout.",
)
def logout(body: RefreshRequest) -> None:
    logout_user(body.refresh_token)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Thông tin tài khoản hiện tại",
    description="Trả về thông tin người dùng đang đăng nhập. Yêu cầu **Bearer Access Token** hợp lệ.",
)
def get_me(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    return current_user
