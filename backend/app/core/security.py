"""
SmartGPA – Security Utilities
- bcrypt password hashing
- JWT Access Token (30 phút) + Refresh Token (7 ngày)
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt

# Workaround for passlib + bcrypt >= 4.1.0 compatibility on Python 3.12/3.13
import bcrypt
original_hashpw = bcrypt.hashpw
def patched_hashpw(password, salt):
    # Ensure password is in bytes to calculate length correctly
    if isinstance(password, str):
        password_bytes = password.encode("utf-8")
    else:
        password_bytes = password
    
    # Truncate to 72 bytes (standard bcrypt limit) to prevent ValueError
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
        
    return original_hashpw(password_bytes, salt)
bcrypt.hashpw = patched_hashpw

from passlib.context import CryptContext

from app.core.config import settings

# ─── Password hashing ────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Mã hóa mật khẩu bằng bcrypt"""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác minh mật khẩu plaintext với hash đã lưu"""
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT Token generation ─────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Tạo JWT Access Token.
    Mặc định hết hạn sau ACCESS_TOKEN_EXPIRE_MINUTES phút.
    Payload: sub (email), role, uid, type="access"
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Tạo JWT Refresh Token.
    Hết hạn sau REFRESH_TOKEN_EXPIRE_DAYS ngày.
    Payload: sub (email), role, uid, type="refresh"
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Giải mã và xác minh JWT token.
    Raises HTTP 401 nếu token không hợp lệ hoặc đã hết hạn.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
