from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from deps import get_db, get_current_user
from models.user_model import User
from models.log_model import ActionLog
from utils.response import ApiResponse

router = APIRouter(prefix="/api/logs", tags=["操作日志"])

@router.get("")
def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        return ApiResponse.error(msg="仅管理员可查看日志", code=403)

    q = db.query(ActionLog)
    if action:
        q = q.filter(ActionLog.action == action)

    total = q.count()
    logs = q.order_by(desc(ActionLog.id)).offset((page - 1) * page_size).limit(page_size).all()

    return ApiResponse.success(
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": l.id,
                    "username": l.username,
                    "action": l.action,
                    "target": l.target,
                    "detail": l.detail,
                    "ip": l.ip,
                    "create_time": l.create_time.strftime("%Y-%m-%d %H:%M:%S") if l.create_time else None,
                }
                for l in logs
            ],
        },
        msg="ok",
    )