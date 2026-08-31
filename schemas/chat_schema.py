from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any

class SessionCreate(BaseModel):
    session_name: str = Field(default="新会话", min_length=1, max_length=200, description="会话标题")

class SessionOut(BaseModel):
    id: int
    session_name: str
    create_time: datetime
    update_time: datetime
    class Config:
        from_attributes = True

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    extra_json: Optional[str] = None
    create_time: datetime
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000, description="消息内容")

class RAGMessageCreate(BaseModel):
    """RAG问答入参：用户问题 + 可选 tag 过滤 + 检索策略切换"""
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题，最长 2000 字符")
    tag: Optional[str] = Field(default=None, max_length=50, description="过滤标签")
    retrieve_mode: Optional[str] = Field(default="hybrid", description="检索策略: hybrid=混合 / vector=纯向量")
    use_rerank: Optional[bool] = Field(default=True, description="是否启用 Rerank 精排")

class RAGMessageOut(BaseModel):
    """RAG问答返回：自然语言回答 + 文档溯源"""
    success: bool
    answer: str
    reference: List[Any] = []
    message_id: Optional[int] = None
    error: Optional[str] = None