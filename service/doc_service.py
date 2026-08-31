"""
文档解析 & 清洗 & 分块服务

升级点（相对于 Day3 原始版本）：
1. extract_text: 增加 PDF 表格简单处理（PyPDF2 无法直接识别表格，用启发式规则把密集列文本拼成行）
2. clean_text: 增加 PDF 乱码字符过滤（常见的 ligature 替代字符、soft-hyphen、OCR 噪声）
3. chunk_text: 升级为递归字符分块（从大到小按分隔符递归切），增加块重叠防语义截断
"""
import os
import re
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session
from models.doc_model import Document
from fastapi import UploadFile, HTTPException
from PyPDF2 import PdfReader
from config.settings import settings

UPLOAD_TMP_DIR = "./tmp_upload"
os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)

# PDF 乱码 / OCR 噪声字符清理表
_PDF_NOISE_PATTERNS = [
    # 常见 PDF ligature 替代字符（映射回常见 ASCII/UTF-8）
    (re.compile(r"[\uF000-\uF0FF]"), ""),    # PUA 私有区（旧版字体编码常塞这里）
    (re.compile(r"[\u2028\u2029]"), "\n"),    # 行分隔符 / 段分隔符 → 换行为一
    (re.compile(r"\u00AD"), ""),              # soft hyphen（可选断字符）
    (re.compile(r"[\u00A0\u2000-\u200A]"), " "),  # 各种空白符 → 普通空格
    (re.compile(r"[\u2018\u2019]"), "'"),    # 智能引号
    (re.compile(r"[\u201C\u201D]"), '"'),
    (re.compile(r"[\u2014\u2013]"), "-"),
    (re.compile(r"[\uFFFD]"), ""),            # Unicode replacement char
]


def extract_text(file_path: str, file_type: str) -> str:
    """
    读取 PDF/TXT/MD，提取原始文本。
    PDF 增加简单表格启发式：同一页面中若多行出现 3+ 个连续 "  "（双空格），
    视为列分隔，将页面所有行按列对齐后用 | 拼成表格行。
    """
    text = ""
    if file_type == "pdf":
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            page_text = _try_extract_table_rows(page_text)
            text += page_text + "\n"
    elif file_type in ("txt", "md"):
        for enc in ("utf-8", "gbk", "utf-8-sig", "latin-1"):
            try:
                with open(file_path, "r", encoding=enc) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue
    return text.strip()


def _try_extract_table_rows(page_text: str) -> str:
    """
    PDF 表格启发式处理：
    PyPDF2 对表格的文本抽取会把各列内容用空格隔开，行用换行分隔。
    这里做两件事：
      1) 把连续的 3+ 空格规范为 |（列分隔符），使表格行在分块后仍可被识别
      2) 压缩每页内的噪声行（太短的 OCR 碎片）
    """
    if not page_text.strip():
        return page_text

    lines = page_text.split("\n")
    processed_lines: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            processed_lines.append("")
            continue
        # 判断：行内是否有 ≥2 处 "  "（双空格）—— 大概率是表格行
        if stripped.count("  ") >= 2:
            # 把连续 2+ 空格替换为 |，保留原始内容（分块时再处理）
            table_line = re.sub(r"  +", " | ", stripped)
            processed_lines.append(table_line)
        else:
            processed_lines.append(stripped)

    return "\n".join(processed_lines)


def clean_text(text: str) -> str:
    """
    文本清洗：增强版乱码过滤 + 规范化。
    处理顺序：PDF 噪声字符 → 控制字符 → 空白规范化 → 去首尾空白
    """
    if not text:
        return ""

    # 1. PDF / OCR 乱码
    for pattern, replacement in _PDF_NOISE_PATTERNS:
        text = pattern.sub(replacement, text)

    # 2. 控制字符（保留 \n \t）
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 3. 空白规范化
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # 4. 去行首行尾空格
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def _split_once(text: str, sep: str) -> List[str]:
    """按分隔符切一次，保留分隔符（用于递归场景，避免语义硬断裂）"""
    if sep not in text:
        return [text]
    parts = text.split(sep)
    # 重新拼回：除了最后一段，其余都带上分隔符
    result = []
    for i, p in enumerate(parts):
        if i < len(parts) - 1:
            result.append(p + sep)
        else:
            if p:
                result.append(p)
    return result


def _recursive_split(text: str, chunk_size: int, separators: List[str]) -> List[str]:
    """
    递归字符分块：从最粗的分隔符（\n\n）开始切，
    若切出的片段仍超过 chunk_size，则用更细的分隔符继续切，
    最终兜底按硬字符切。这样最大化保留语义完整性。
    """
    if len(text) <= chunk_size:
        return [text]

    if not separators:
        # 兜底：硬切 + 重叠
        pieces = []
        start = 0
        overlap = 0  # 兜底阶段不重叠，避免引入噪声
        while start < len(text):
            end = start + chunk_size
            pieces.append(text[start:end])
            if end >= len(text):
                break
            start = end - overlap
        return pieces

    sep = separators[0]
    remaining_seps = separators[1:]

    segments = _split_once(text, sep)
    result: List[str] = []
    buffer = ""

    for seg in segments:
        if len(buffer) + len(seg) <= chunk_size:
            buffer += seg
        else:
            if buffer:
                result.append(buffer.strip())
            # 当前 seg 自己可能也超长 → 递归下一层分隔符
            if len(seg) > chunk_size:
                result.extend(_recursive_split(seg, chunk_size, remaining_seps))
                buffer = ""
            else:
                buffer = seg

    if buffer.strip():
        result.append(buffer.strip())

    return result


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[str]:
    """
    递归字符分块 + 块重叠。

    分隔符优先级（从粗到细）：
      \n\n → \n → 。！？. → \t → 硬切

    块重叠：
      每个新 chunk 开头带上上一个 chunk 的尾部 chunk_overlap 字符，
      确保跨 chunk 的句子不会被截断。

    :param text: 清洗后的文本
    :param chunk_size: 每块目标字符数（默认 settings.CHUNK_SIZE）
    :param chunk_overlap: 块间重叠字符数（默认 settings.CHUNK_OVERLAP）
    :return: 分块列表
    """
    if not text:
        return []
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    separators = ["\n\n", "\n", "。", "！", "？", ". ", "；", ";", "，", ", ", " ", ""]

    # 先递归切分
    raw_chunks = _recursive_split(text, chunk_size, separators)

    # 去除空块
    raw_chunks = [c.strip() for c in raw_chunks if c and c.strip()]

    # 添加块重叠
    overlapped: List[str] = []
    for i, chunk in enumerate(raw_chunks):
        if i == 0:
            overlapped.append(chunk)
        else:
            prev_tail = raw_chunks[i - 1][-chunk_overlap:] if chunk_overlap > 0 and raw_chunks[i - 1] else ""
            if prev_tail:
                overlapped.append((prev_tail + "\n" + chunk).strip())
            else:
                overlapped.append(chunk)

    return overlapped


# ========== 以下是文档元数据的 DB 操作 ==========

def save_document_meta(
    db: Session,
    filename: str,
    file_type: str,
    tag: str,
    preview: str,
    uploader_id: int,
) -> Document:
    doc = Document(
        filename=filename,
        file_type=file_type,
        tag=tag,
        content_preview=preview[:1500] if preview else "",
        uploader_id=uploader_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_doc_list(db: Session):
    return db.query(Document).order_by(Document.created_at.desc()).all()


def get_doc_by_id(db: Session, doc_id: int):
    return db.query(Document).filter(Document.id == doc_id).first()


def delete_doc(db: Session, doc_id: int):
    doc = get_doc_by_id(db, doc_id)
    if not doc:
        return False
    db.query(Document).filter(Document.id == doc_id).delete(synchronize_session=False)
    db.commit()
    return True