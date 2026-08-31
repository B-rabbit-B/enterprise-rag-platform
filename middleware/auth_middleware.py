"""
全局鉴权中间件：

- 白名单放行：/api/user/login、/api/user/register、/docs、/openapi.json、/redoc、/

- 其余接口必须携带 Bearer Token

- Token 解析成功后，将 user_id / username 注入 request.state，下游可直接取
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from utils.jwt_util import decode_token
from utils.response import ApiResponse

# 白名单：不需要鉴权的接口（按前缀匹配）
# 说明：/ 只匹配根路径本身，页面路由、静态资源、统计接口需显式加
WHITE_LIST = [
    # 用户相关
    "/api/user/login",
    "/api/user/register",
    # Swagger / OpenAPI
    "/docs",
    "/openapi.json",
    "/redoc",
    # 首页 & 页面路由
    "/",
    "/chat",
    "/documents",
    "/evaluation",
    "/settings",
    "/favicon.ico",
    # 静态资源
    "/static",
    # 前端用轻量只读接口（无敏感数据）
    "/api/stats",
    "/api/config",
]

class AuthMiddleware(BaseHTTPMiddleware):
    """全局 JWT 鉴权中间件"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 1. 白名单直接放行
        if any(path == w or path.startswith(w + "/") for w in WHITE_LIST):
            return await call_next(request)

        # 2. 预检 OPTIONS 放行（CORS 用）
        if request.method == "OPTIONS":
            return await call_next(request)

        # 3. 校验 Authorization Header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content=ApiResponse.error(msg="未携带有效 token", code=401),
            )

        token = auth_header.split(" ")[1].strip()
        payload = decode_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content=ApiResponse.error(msg="token 无效或已过期", code=401),
            )

        # 4. 注入 request.state，下游接口可通过 request.state.user_id 取
        request.state.user_id = payload.get("user_id")
        request.state.username = payload.get("sub")

        return await call_next(request)