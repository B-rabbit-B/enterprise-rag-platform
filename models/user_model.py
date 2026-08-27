from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
# 从core.db_base导入Base，不再导入deps！！
from core.db_base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.utcnow)
