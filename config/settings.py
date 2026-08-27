from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # extra="ignore": 允许 .env 中出现未声明的变量（如 HF_HUB_DISABLE_SYMLINKS_WARNING）
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM（空值时服务仍可启动，调用 LLM 时给出友好提示）
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = "qwen-plus"

    # JWT
    JWT_SECRET_KEY: str = "rag_platform_secret_key_2024"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # 数据库
    SQLITE_DATABASE_URL: str = "sqlite:///./rag_app.db"

    # 向量库
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # 文件上传限制（MB）
    MAX_UPLOAD_FILE_SIZE_MB: int = 50

    # RAG 业务参数（token截断、召回、重排）
    RAG_MAX_CONTEXT_TOKEN: int = 2000    # 上下文最大token阈值
    RAG_RETRIEVE_TOP_K: int = 5         # 向量召回数量
    RAG_RERANK_TOP_N: int = 3           # 重排之后保留片段

settings = Settings()