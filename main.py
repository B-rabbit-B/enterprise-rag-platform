import os
from contextlib import asynccontextmanager
# 仅本地开发兜底，不覆盖外部已设置的环境变量
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")  # Windows 下屏蔽 huggingface 符号链接警告

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

# 模板 & 静态资源路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 直接用 jinja2 原生环境（绕开 starlette 的 Jinja2Templates 缓存层 bug）
_jinja_env = Environment(
    loader=FileSystemLoader(os.path.join(BASE_DIR, "templates")),
    autoescape=select_autoescape(["html", "htm"]),
    enable_async=False,
)

def render(template_name: str, **kwargs) -> HTMLResponse:
    """原生 Jinja2 渲染函数（替代 _templates.TemplateResponse）"""
    template = _jinja_env.get_template(template_name)
    html = template.render(**kwargs)
    return HTMLResponse(content=html)
from sqlalchemy import inspect, text
from config.settings import settings
from deps import engine
import models.user_model
import models.chat_model
import models.log_model
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
    # 0. 确保上传临时目录存在
    import os
    os.makedirs("./tmp_upload", exist_ok=True)
    # 1. 建表
    Base.metadata.create_all(bind=engine)
    # 2. 字段迁移（兼容老数据库）
    _ensure_chat_message_extra_json()
    # 3. 预热 Reranker（只加载一次，彻底解决重复加载问题）
    from utils.rerank_util import preload
    preload()
    # 4. 预热 Embedding 模型 & Chroma Collection（避免首次请求卡 + 首页 stats 正常）
    try:
        from service.rag_service import _get_embedding_fn, _collection
        _get_embedding_fn()
        log_info("=== Embedding 模型 & Chroma Collection 预热完成 ===")
    except Exception as e:
        log_info(f"=== Embedding 预热跳过（{e.__class__.__name__}），将在首次使用时加载 ===")
    # 5. 日志
    log_info("=== RAG 平台启动完成 ===")

    yield  # 服务运行中...

    # ===== 关闭阶段（预留扩展：可在此释放 DB 连接池、模型显存等资源） =====
    log_info("=== RAG 平台已关闭 ===")


# 1. 实例化 app，绑定生命周期
app = FastAPI(
    title="企业知识库RAG问答平台",
    version="1.1.0",
    description="""
基于 FastAPI + ChromaDB + BGE-Reranker 的企业级 RAG 后端服务。

**RAG 流程**: 文档上传 → 递归分块 → 向量化入库 → 混合检索（向量 + BM25） → Rerank 精排 → Token 截断 → LLM 生成 → 溯源返回

**快速上手**:
1. 管理员账号默认 `admin / admin123456`
2. 调 POST `/api/user/login` 登录拿到 token
3. 点击页面右上角 🔒 **Authorize**，填入 `Bearer 你的token`（注意 Bearer 和 token 之间有空格）
4. 然后调用其他接口就会自动带上鉴权头
    """,
    lifespan=lifespan,
    # ========== Swagger UI 美化参数（零依赖）==========
    swagger_ui_parameters={
        "docExpansion": "list",           # 只展开分组，不全部展开
        "defaultModelsExpandDepth": -1,   # 隐藏底部模型定义面板，页面清爽
        "operationsSorter": "method",     # 按 POST > GET > DELETE 排序
        "filter": True,                   # 顶部接口搜索框
        "showRequestHeaders": True,
    },
)

# 1.1 注入 Bearer Token 认证 scheme（apiKey 方式弹框 + schema 缓存，修复 Swagger Authorize 按钮失效）
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    # 缓存 schema，避免重复生成
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # 配置 apiKey 认证方案，Swagger 弹框输入 Authorization 头
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "输入格式：`Bearer {access_token}`",
        }
    }
    # 全局开启鉴权（白名单接口由中间件跳过）
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 2. 注册全局异常处理器（兜底所有异常，保证服务不崩）
from middleware.exception_handler import register_exception_handlers
register_exception_handlers(app)

# 3. 开启 CORS 中间件（必须在 AuthMiddleware 之前注册，否则跨域请求被鉴权拦）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 注册全局鉴权中间件（白名单放行登录/注册/文档）
from middleware.auth_middleware import AuthMiddleware
app.add_middleware(AuthMiddleware)

# 4. 导入并挂载所有路由
from routers.doc_router import router as doc_router
from routers.chat_router import router as chat_router
from routers.user_router import router as user_router
from routers.log_router import router as log_router
from routers.eval_router import router as eval_router
app.include_router(doc_router)
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(log_router)
app.include_router(eval_router)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ---------- 页面路由 ----------
@app.get("/", response_class=HTMLResponse)
def page_index(request: Request):
    return render("index.html", request=request)

@app.get("/chat", response_class=HTMLResponse)
def page_chat(request: Request):
    return render("chat.html", request=request)

@app.get("/documents", response_class=HTMLResponse)
def page_documents(request: Request):
    return render("documents.html", request=request)

@app.get("/evaluation", response_class=HTMLResponse)
def page_evaluation(request: Request):
    return render("evaluation.html", request=request)

@app.get("/settings", response_class=HTMLResponse)
def page_settings(request: Request):
    return render("settings.html", request=request)

# ---------- 统计接口（首页用）----------
@app.get("/api/stats")
def api_stats():
    """首页统计：文档数 / chunk 数 / BM25 索引状态 / 运行状态"""
    from deps import SessionLocal
    from models.doc_model import Document
    from service.rag_service import _collection, _bm25_index
    db = SessionLocal()
    try:
        doc_count = db.query(Document).count()
    finally:
        db.close()

    chunk_count = 0
    try:
        if _collection is not None:
            chunk_count = _collection.count()
    except Exception:
        pass

    return {
        "code": 200,
        "msg": "ok",
        "data": {
            "doc_count": doc_count,
            "chunk_count": chunk_count,
            "bm25_ready": _bm25_index is not None,
            "hybrid_enabled": True,
            "service_status": "running",
        },
    }

@app.get("/api/config")
def api_config():
    """系统当前配置（用于设置页面展示，敏感字段已过滤）"""
    from config.settings import settings as s
    return {
        "code": 200,
        "msg": "ok",
        "data": {
            # 检索策略
            "hybrid_enabled": s.HYBRID_ENABLE,
            "hybrid_vector_weight": s.HYBRID_VECTOR_WEIGHT,
            "hybrid_bm25_weight": s.HYBRID_BM25_WEIGHT,
            "hybrid_bm25_top_k": s.HYBRID_BM25_TOP_K,
            # RAG 参数
            "rag_top_k": s.RAG_RETRIEVE_TOP_K,
            "rag_rerank_top_n": s.RAG_RERANK_TOP_N,
            "rag_max_context_token": s.RAG_MAX_CONTEXT_TOKEN,
            # 分块参数
            "chunk_size": s.CHUNK_SIZE,
            "chunk_overlap": s.CHUNK_OVERLAP,
            # 模型信息
            "embedding_model": s.EMBEDDING_MODEL,
            "llm_model": s.LLM_MODEL or "（未配置，仅检索模式可用）",
            # 路径
            "chroma_persist_dir": s.CHROMA_PERSIST_DIR,
            "sqlite_database_url": s.SQLITE_DATABASE_URL,
        },
    }


if __name__ == "__main__":
    import uvicorn
    from utils.logger import log_info
    log_info("服务启动参数：reload=False, port=8000")
    # reload=True 会 fork 子进程导致大模型重复加载，生产环境务必关闭
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)