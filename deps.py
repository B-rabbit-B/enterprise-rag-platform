from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from config.settings import settings
from core.db_base import Base
from models.user_model import User
from utils.jwt_util import decode_token

# 唯一一处数据库引擎
engine = create_engine(settings.SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 数据库会话依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT鉴权
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")

def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    获取当前用户：优先从 request.state 取（AuthMiddleware 已解析过 JWT），
    避免在每个路由上重复解析 token。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="token无效或者已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. 优先从中间件已注入的 request.state 取，避免重复解析
    username = getattr(request.state, "username", None)
    if not username:
        # 兜底：手动解析 token
        payload = decode_token(token)
        if not payload:
            raise credentials_exception
        username = payload.get("sub")
        if not username:
            raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user