from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from core.db_base import Base

class ActionLog(Base):
    """操作日志：自动记录登录、文档上传、问答等关键行为"""
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=True)
    action = Column(String(100), nullable=False)
    target = Column(String(255), nullable=True)
    detail = Column(Text, nullable=True)
    ip = Column(String(50), nullable=True)
    create_time = Column(DateTime, default=datetime.utcnow, index=True)