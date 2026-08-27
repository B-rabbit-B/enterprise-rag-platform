import os
import re
from pathlib import Path
from sqlalchemy.orm import Session
from models.doc_model import Document
from fastapi import UploadFile, HTTPException
from PyPDF2 import PdfReader
from config.settings import settings

UPLOAD_TMP_DIR = "./tmp_upload"
os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)


def extract_text(file_path: str, file_type: str) -> str:
    """读取PDF/TXT/MD，提取原始文本"""
    text = ""
    if file_type == "pdf":
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    elif file_type in ("txt", "md"):
        # 尝试多种编码，Windows 下兼容
        for enc in ("utf-8", "gbk", "utf-8-sig"):
            try:
                with open(file_path, "r", encoding=enc) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue
    return text.strip()


def clean_text(text: str) -> str:
    """文本清洗：去除多余空白、控制字符、连续特殊符号"""
    if not text:
        return ""
    # 去除控制字符（换行、制表符保留）
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # 合并多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 合并多余空格
    text = re.sub(r"[ \t]{2,}", " ", text)
    # 去除行首行尾空格
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> list[str]:
    """
    按字符数分块，支持重叠。
    优先按段落拆分，段落过长再按字符切割。
    """
    if not text:
        return []
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    buffer = ""

    for para in paragraphs:
        # 单段过长，再按字符切分
        if len(para) > chunk_size:
            if buffer:
                chunks.append(buffer)
                buffer = ""
            start = 0
            while start < len(para):
                end = start + chunk_size
                piece = para[start:end]
                chunks.append(piece)
                start = end - chunk_overlap
                if start >= len(para):
                    break
            continue

        if len(buffer) + len(para) + 2 <= chunk_size:
            buffer = (buffer + "\n\n" + para).strip() if buffer else para
        else:
            if buffer:
                chunks.append(buffer)
            # 新块起始，带重叠（取上一块尾部）
            if chunk_overlap > 0 and chunks:
                tail = chunks[-1][-chunk_overlap:]
                buffer = (tail + "\n\n" + para).strip()
            else:
                buffer = para

    if buffer:
        chunks.append(buffer)

    return chunks

def save_document_meta(
    db: Session,
    filename: str,
    file_type: str,
    tag: str,
    preview: str,
    uploader_id: int,
):
    """保存文档元数据到 SQLite 数据库，返回 Document 对象"""
    doc = Document(
        filename=filename,
        file_type=file_type,
        tag=tag,
        content_preview=preview[:1500] if preview else "",  # 只存预览
        uploader_id=uploader_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_doc_list(db: Session):
    return db.query(Document).order_by(Document.created_at.desc()).all()

def get_doc_by_id(db: Session, doc_id:int):
    return db.query(Document).filter(Document.id == doc_id).first()

def delete_doc(db: Session, doc_id: int):
    doc = get_doc_by_id(db, doc_id)
    if not doc:
        return False
    # synchronize_session=False：直接 SQL 删除，避免批量操作后会话不同步
    db.query(Document).filter(Document.id == doc_id).delete(synchronize_session=False)
    db.commit()
    return True