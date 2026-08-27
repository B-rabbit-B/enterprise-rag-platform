"""
全局异常处理器：

1) 兜底 Exception → 500 规范 JSON（保证服务不崩）

2) RequestValidationError → 422 + 字段级错误详情

3) StarletteHTTPException → 401/403/404 统一格式
"""
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.response import ApiResponse
from utils.logger import log_error

def register_exception_handlers(app: FastAPI):
    """注册三个全局异常处理器到 FastAPI 实例"""

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # 记录完整堆栈到日志
        log_error(f"[UnhandledException] {request.method} {request.url.path} | error={str(exc)}")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(msg=f"服务器内部错误: {str(exc)}", code=500),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            field = ".".join(str(loc) for loc in err.get("loc", []))
            errors.append(f"{field}: {err.get('msg', '')}")
        log_error(f"[ValidationError] {request.method} {request.url.path} | errors={errors}")
        return JSONResponse(
            status_code=422,
            content=ApiResponse.error(
                msg="参数校验失败", code=422, data={"errors": errors}
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse.error(msg=str(exc.detail), code=exc.status_code),
        )
