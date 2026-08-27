from pydantic import BaseModel
from datetime import datetime
from typing import Any


class DocumentOut(BaseModel):
    id: int
    filename: str
    file_type: str
    tag: str | None
    content_preview: str | None
    uploader_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UploadResponse(DocumentOut):
    """上传响应扩展：附带分块数量信息"""
    chunk_count: int = 0
    chunk_size: int = 0


class SearchHit(BaseModel):
    id: str
    document: str
    metadata: dict[str, Any]
    distance: float


class SearchResponse(BaseModel):
    total: int
    hits: list[SearchHit]