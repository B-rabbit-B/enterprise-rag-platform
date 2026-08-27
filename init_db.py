import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import bcrypt
from sqlalchemy import inspect, text
from deps import engine, SessionLocal
from core.db_base import Base
from models.user_model import User
from models.doc_model import Document
from models.chat_model import ChatMessage  # noqa: F401  确保模型注册到 Base


def hash_password(raw: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(raw.encode("utf-8"), salt).decode("utf-8")


def _ensure_chat_message_extra_json():
    """为已存在的 chat_message 表补齐 extra_json 字段（Day5 新增）"""
    insp = inspect(engine)
    if "chat_message" not in insp.get_table_names():
        return
    columns = [c["name"] for c in insp.get_columns("chat_message")]
    if "extra_json" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE chat_message ADD COLUMN extra_json TEXT")
            )
        print("✅ 已为 chat_message 表补充 extra_json 字段")


if __name__ == "__main__":
    print("正在创建数据表...")
    Base.metadata.create_all(bind=engine)
    print("已识别表：", list(Base.metadata.tables.keys()))

    # 对已有数据库做字段补齐
    _ensure_chat_message_extra_json()

    print("初始化管理员账号...")
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        new_admin = User(
            username="admin",
            hashed_password=hash_password("admin123456"),
            is_admin=True
        )
        db.add(new_admin)
        db.commit()
    db.close()
    print("✅数据库初始化完成 admin / admin123456")