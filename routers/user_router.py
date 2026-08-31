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


# ========== 用户管理（管理员用）==========
@router.get("/list")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        return ApiResponse.error(msg="仅管理员可查看用户列表", code=403)
    users = db.query(User).order_by(User.id.asc()).all()
    return ApiResponse.success(
        data=[
            {
                "id": u.id,
                "username": u.username,
                "is_admin": u.is_admin,
                "create_time": u.create_time.strftime("%Y-%m-%d %H:%M:%S") if u.create_time else None,
            }
            for u in users
        ],
        msg="ok",
    )


@router.post("/{user_id}/toggle-admin")
def toggle_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        return ApiResponse.error(msg="仅管理员可操作", code=403)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return ApiResponse.error(msg="用户不存在", code=404)
    if user.username == "admin" and not user.is_admin:
        return ApiResponse.error(msg="内置 admin 账号不可降权", code=400)
    # 不能把自己降权
    if user.id == current_user.id:
        return ApiResponse.error(msg="不能修改自己的权限", code=400)
    user.is_admin = not user.is_admin
    db.commit()
    return ApiResponse.success(data={"is_admin": user.is_admin}, msg="权限已更新")


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        return ApiResponse.error(msg="仅管理员可操作", code=403)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return ApiResponse.error(msg="用户不存在", code=404)
    if user.username == "admin":
        return ApiResponse.error(msg="内置 admin 账号不可删除", code=400)
    if user.id == current_user.id:
        return ApiResponse.error(msg="不能删除自己", code=400)
    db.delete(user)
    db.commit()
    return ApiResponse.success(msg="删除成功")