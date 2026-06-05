"""
SmartGPA – FastAPI Dependencies
- get_current_user: Xác thực Bearer token, trả về UserOut
- require_role(*roles): Dependency factory kiểm tra vai trò
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.db.real_db import ASSIGNMENTS_DB, find_user_by_login
from app.models.schemas import UserOut, UserRole

# HTTPBearer cấu hình auto_error=False để kiểm tra và trả lỗi 403 tương thích ngược với Unit Tests
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserOut:
    """
    Dependency: Giải mã Bearer token → trả về UserOut.
    Raise 403 nếu thiếu token (tương thích unit tests).
    Raise 401 nếu token không hợp lệ / hết hạn.
    Raise 403 nếu tài khoản bị vô hiệu hóa.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vui lòng cung cấp Access Token hợp lệ.",
        )
    token = credentials.credentials
    payload = decode_token(token)  # Raises 401 nếu sai

    # Kiểm tra đây là access token (không phải refresh token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vui lòng sử dụng Access Token để xác thực",
        )

    login_key: str = payload.get("sub", "")
    if not login_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ: thiếu thông tin người dùng",
        )

    user = find_user_by_login(login_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại trong hệ thống",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa. Liên hệ Admin để được hỗ trợ.",
        )

    # Tính danh sách môn dạy cho giảng viên từ ASSIGNMENTS_DB (dynamic)
    subjects = None
    lecturer_id = user.get("lecturer_id")
    if user.get("role") == "lecturer" and lecturer_id:
        subjects = list({
            a["ma_mon"]
            for a in ASSIGNMENTS_DB
            if a["lecturer_id"] == lecturer_id
        })

    return UserOut(
        id=user["id"],
        email=user.get("email") or user.get("username", ""),
        username=user.get("username"),
        full_name=user["full_name"],
        role=UserRole(user["role"]),
        is_active=user["is_active"],
        created_at=user["created_at"],
        student_id=user.get("student_id"),
        lecturer_id=lecturer_id,
        subjects=subjects,
        faculty_id=user.get("faculty_id"),
        major_id=user.get("major_id"),
        must_change_password=bool(user.get("must_change_password", False)),
        email_verified=bool(user.get("email_verified", False)),
    )



def require_role(*allowed_roles: UserRole):
    """
    Dependency factory: Kiểm tra vai trò người dùng.

    Ví dụ:
        @router.post("/upload", dependencies=[Depends(require_role(UserRole.LECTURER))])
        @router.post("/simulate", dependencies=[Depends(require_role(UserRole.STUDENT))])
    """
    def role_checker(
        current_user: UserOut = Depends(get_current_user),
    ) -> UserOut:
        if current_user.role not in allowed_roles:
            allowed_str = ", ".join(r.value for r in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Vai trò '{current_user.role.value}' không có quyền truy cập chức năng này. "
                    f"Chức năng này yêu cầu: [{allowed_str}]"
                ),
            )
        return current_user

    return role_checker
