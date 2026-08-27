import os
from contextlib import asynccontextmanager
# 仅本地开发兜底，不覆盖外部已设置的环境变量
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")  # Windows 下屏蔽 huggingface 符号链接警告

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqlalchemy import inspect, text
from config.settings import settings
from deps import engine
import models.user_model
import models.chat_model
from core.db_base import Base


# ========== Day6：应用生命周期（lifespan）==========
# 字段迁移工具函数（仅在 lifespan 启动阶段调用一次）
def _ensure_chat_message_extra_json():
    insp = inspect(engine)
    if "chat_message" not in insp.get_table_names():
        return
    columns = [c["name"] for c in insp.get_columns("chat_message")]
    if "extra_json" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE chat_message ADD COLUMN extra_json TEXT"))
        print("✅ 已为 chat_message 表补充 extra_json 字段")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器：统一管理启动初始化与关闭释放，保证每个初始化步骤只执行一次"""
    from utils.logger import log_info

    # ===== 启动阶段 =====
    # 1. 建表
    Base.metadata.create_all(bind=engine)
    # 2. 字段迁移（兼容老数据库）
    _ensure_chat_message_extra_json()
    # 3. 预热 Reranker（只加载一次，彻底解决重复加载问题）
    from utils.rerank_util import preload
    preload()
    # 4. 日志
    log_info("=== RAG 平台启动完成 ===")

    yield  # 服务运行中...

    # ===== 关闭阶段（预留扩展：可在此释放 DB 连接池、模型显存等资源） =====
    log_info("=== RAG 平台已关闭 ===")


# 1. 实例化 app，绑定生命周期
app = FastAPI(title="企业知识库RAG问答平台", version="1.0.0", lifespan=lifespan)

# 2. 注册全局异常处理器（兜底所有异常，保证服务不崩）
from middleware.exception_handler import register_exception_handlers
register_exception_handlers(app)

# 3. 注册全局鉴权中间件（白名单放行登录/注册/文档）
from middleware.auth_middleware import AuthMiddleware
app.add_middleware(AuthMiddleware)

# 4. 导入并挂载所有路由
from routers.doc_router import router as doc_router
from routers.chat_router import router as chat_router
from routers.user_router import router as user_router
app.include_router(doc_router)
app.include_router(user_router)
app.include_router(chat_router)

@app.get("/")
def root():
    """根路径重定向到 Swagger 接口文档，方便本地调试与开源体验"""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    from utils.logger import log_info
    log_info("服务启动参数：reload=False, port=8000")
    # reload=True 会 fork 子进程导致大模型重复加载，生产环境务必关闭
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)