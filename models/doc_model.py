from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from core.db_base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32))
    tag = Column(String(128))
    content_preview = Column(Text)
    uploader_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())
