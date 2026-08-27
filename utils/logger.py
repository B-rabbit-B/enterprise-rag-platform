"""
结构化日志工具：同时输出到控制台 + 按天滚动的日志文件
用于记录 RAG 请求的 user_id / 命中数 / 耗时 / 状态
"""
import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")

logger = logging.getLogger("rag_app")
logger.setLevel(logging.INFO)

# 避免重复添加 handler（uvicorn reload 时会触发）
if not logger.handlers:
    # 文件 handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    # 控制台 handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

def log_rag_request(
    user_id: int,
    question: str,
    hit_count: int,
    cost_sec: float,
    success: bool = True,
    tag: str = "",
):
    """RAG 问答请求结构化日志"""
    status = "SUCCESS" if success else "FAILED"
    logger.info(
        f"[RAG] user_id={user_id} | tag={tag} | hits={hit_count} | "
        f"cost={cost_sec:.2f}s | status={status} | question={question[:100]}"
    )

def log_info(msg: str):
    logger.info(msg)

def log_warning(msg: str):
    logger.warning(msg)

def log_error(msg: str):
    logger.error(msg)
