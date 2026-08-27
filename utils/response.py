"""
统一响应封装：所有接口返回 {code, msg, data} 标准结构
code=0 表示成功，非 0 表示异常（HTTP 状态码或业务错误码）
"""
from typing import Any, Optional

class ApiResponse:
    """统一响应工具类"""

    @staticmethod
    def success(data: Any = None, msg: str = "ok", code: int = 0) -> dict:
        return {"code": code, "msg": msg, "data": data}

    @staticmethod
    def error(msg: str = "error", code: int = -1, data: Any = None) -> dict:
        return {"code": code, "msg": msg, "data": data}
