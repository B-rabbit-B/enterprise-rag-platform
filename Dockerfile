FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_ENDPOINT=https://hf-mirror.com \
    SQLITE_DATABASE_URL=sqlite:////app/data/rag_app.db \
    CHROMA_PERSIST_DIR=/app/data/chroma_db

WORKDIR /app

# 先装 CPU 版 torch，避免 sentence-transformers 拉取数 GB 的 CUDA 依赖
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 数据目录：SQLite + Chroma 放 /app/data；logs、tmp_upload 为代码内相对路径
RUN mkdir -p /app/data /app/logs /app/tmp_upload

EXPOSE 8000

# init_db.py 幂等：建表 + 创建默认 admin；main.py 里 host 写死 127.0.0.1，容器内需直接用 uvicorn 监听 0.0.0.0
CMD ["sh", "-c", "python init_db.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
