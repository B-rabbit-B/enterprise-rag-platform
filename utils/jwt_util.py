import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt
from config.settings import settings


def get_password_hash(raw_password: str) -> str:
    """密码哈希 bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(raw_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """校验密码"""
    return bcrypt.checkpw(raw_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(username: str, user_id: int = None, expires_delta: timedelta = None):
    """生成JWT token，payload 中包含 sub(用户名) 和 user_id"""
    to_encode = {"sub": username}
    if user_id is not None:
        to_encode["user_id"] = user_id
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """解析并校验 JWT token，返回 payload dict；失败返回 None"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except Exception:
        return None