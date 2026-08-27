from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from deps import get_db, get_current_user
from models.user_model import User
from utils.jwt_util import get_password_hash, verify_password, create_access_token
from utils.response import ApiResponse


router = APIRouter(prefix="/api/user", tags=["用户模块"])

# 请求体模型
class RegisterReq(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名，2-50 字符")
    password: str = Field(..., min_length=6, max_length=100, description="密码，最短 6 位")
    is_admin: bool = Field(default=False, description="是否管理员，默认 false")

class LoginReq(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=100, description="密码")

@router.post("/register")
def register(req: RegisterReq, db: Session = Depends(get_db)):
    # 判断用户名是否存在
    exist_user = db.query(User).filter(User.username == req.username).first()
    if exist_user:
        return ApiResponse.error(msg="用户名已存在", code=400)
    new_user = User(
        username=req.username,
        hashed_password=get_password_hash(req.password),
        is_admin=req.is_admin,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return ApiResponse.success(
        data={"user_id": new_user.id},
        msg="注册成功",
    )

@router.post("/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        return ApiResponse.error(msg="用户名不存在", code=400)
    if not verify_password(req.password, user.hashed_password):
        return ApiResponse.error(msg="密码错误", code=400)
    token = create_access_token(username=user.username, user_id=user.id)
    return ApiResponse.success(
        data={"access_token": token, "token_type": "bearer"},
        msg="登录成功",
    )


@router.get("/me")
def get_my_info(
    current_user: User = Depends(get_current_user),
):
    return ApiResponse.success(
        data={
            "id": current_user.id,
            "username": current_user.username,
            "is_admin": current_user.is_admin,
        },
        msg="获取用户信息成功",
    )