import json
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.mutable import MutableDict
from datetime import datetime
from models.user_model import Base

# 会话表
class ChatSession(Base):
    __tablename__ = "chat_session"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, default="新会话")
    user_id = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# 消息表
class ChatMessage(Base):
    __tablename__ = "chat_message"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    extra_json = Column(Text, nullable=True)       # 存储溯源等元数据(JSON字符串)
    create_time = Column(DateTime, default=datetime.now)