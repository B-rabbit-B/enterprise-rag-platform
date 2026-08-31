from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
from config.settings import settings
from deps import get_db, get_current_user
from models.user_model import User
from schemas.doc_schema import DocumentOut, UploadResponse
from service import doc_service
from service import rag_service
from utils.response import ApiResponse

router = APIRouter(prefix="/api/doc", tags=["文档管理模块"])

# 管理员校验工具函数
def require_admin(user: User):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")

# 上传文档（仅管理员）
@router.post("/upload")
def upload_doc(
    file: UploadFile = File(...),
    tag: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)
    allow_suffix = {"pdf", "txt", "md"}
    suffix = file.filename.split(".")[-1].lower()
    if suffix not in allow_suffix:
        raise HTTPException(status_code=400, detail="仅支持 pdf / txt / md")

    # 文件大小校验：避免大文件 OOM
    max_bytes = settings.MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024
    file_bytes = file.file.read()
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大，最大支持 {settings.MAX_UPLOAD_FILE_SIZE_MB}MB",
        )

    tmp_path = f"./tmp_upload/{file.filename}"
    with open(tmp_path, "wb") as fw:
        fw.write(file_bytes)

    raw_text = doc_service.extract_text(tmp_path, suffix)
    if not raw_text:
        raise HTTPException(status_code=400, detail="文件解析失败，未提取到文本")

    # Day3：文本清洗 + 分块
    cleaned = doc_service.clean_text(raw_text)
    chunks = doc_service.chunk_text(cleaned)

    # 先落库元数据（拿到 doc_id）
    doc = doc_service.save_document_meta(
        db=db,
        filename=file.filename,
        file_type=suffix,
        tag=tag,
        preview=cleaned,
        uploader_id=current_user.id,
    )

    # Day4：写入向量库
    chunk_count = rag_service.upsert_document_chunks(
        doc_id=doc.id,
        filename=file.filename,
        tag=tag,
        chunks=chunks,
    )

    os.remove(tmp_path)

    # 扩展响应：分块数量通过 model_dump 之外的方式返回
    payload = DocumentOut.model_validate(doc).model_dump()
    payload["chunk_count"] = chunk_count
    payload["chunk_size"] = len(chunks)
    return ApiResponse.success(data=payload, msg="文档上传成功")

# 获取全部文档列表
@router.get("/list")
def list_doc(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    docs = doc_service.get_doc_list(db)

    # 查 Chroma collection 用于获取每个文档的分片数
    _col = None
    try:
        from service.rag_service import _get_collection
        _col = _get_collection()
    except Exception:
        pass

    data = []
    for d in docs:
        chunk_count = 0
        try:
            if _col is not None:
                res = _col.get(where={"doc_id": d.id})
                chunk_count = len(res.get("ids", []))
        except Exception:
            pass
        data.append({
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "tag": d.tag,
            "preview": (d.content_preview or "")[:200],
            "upload_time": str(d.created_at),
            "uploader_id": d.uploader_id,
            "chunk_count": chunk_count,
            "parse_status": "success" if chunk_count > 0 else "pending",
        })
    return ApiResponse.success(data=data, msg="获取文档列表成功")

# 删除文档
@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    ok = doc_service.delete_doc(db, doc_id)
    if not ok:
        return ApiResponse.error(msg="文档不存在", code=404)
    # 同步删除向量库
    rag_service.delete_document_chunks(doc_id)
    return ApiResponse.success(msg="文档删除成功")


# 获取文档的真实分片列表（从 Chroma）
@router.get("/{doc_id}/chunks")
def list_doc_chunks(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    doc = doc_service.get_doc_by_id(db, doc_id)
    if not doc:
        return ApiResponse.error(msg="文档不存在", code=404)

    try:
        col = rag_service._get_collection()
        res = col.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
    except Exception as e:
        return ApiResponse.error(msg=f"向量库查询失败: {e}", code=500)

    ids = res.get("ids", [])
    docs = res.get("documents", [])
    metas = res.get("metadatas", [])

    # 按 Chroma id 里带的 index 排序（格式: doc_{doc_id}_chunk_{idx}）
    def _chunk_idx(cid: str) -> int:
        try:
            return int(cid.rsplit("_", 1)[-1])
        except Exception:
            return 0

    pairs = list(zip(ids, docs, metas))
    pairs.sort(key=lambda p: _chunk_idx(p[0]))

    items = []
    for i, (cid, text, meta) in enumerate(pairs):
        items.append({
            "chunk_id": cid,
            "index": meta.get("chunk_index", i) if meta else i,
            "content": text or "",
            "char_count": len(text or ""),
        })

    return ApiResponse.success(
        data={"doc_id": doc_id, "total": len(items), "items": items},
        msg="获取分片成功",
    )


# 重新解析：删除旧向量 → 重新分块 → 写入新向量
@router.post("/{doc_id}/reparse")
def reparse_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    doc = doc_service.get_doc_by_id(db, doc_id)
    if not doc:
        return ApiResponse.error(msg="文档不存在", code=404)

    # 1. 删旧向量
    rag_service.delete_document_chunks(doc_id)

    # 2. 从 DB 拿 content_preview（upload 时存的清洗后文本）
    raw = doc.content_preview or ""
    if not raw:
        return ApiResponse.error(msg="文档无可解析内容", code=400)

    # 3. 重新 chunk（会读取 settings 里最新的 CHUNK_SIZE / CHUNK_OVERLAP）
    chunks = doc_service.chunk_text(raw)

    # 4. upsert 新向量
    new_count = rag_service.upsert_document_chunks(
        doc_id=doc.id,
        filename=doc.filename,
        tag=doc.tag or "",
        chunks=chunks,
    )

    return ApiResponse.success(
        data={"doc_id": doc.id, "chunk_count": new_count},
        msg=f"重新解析完成，新生成 {new_count} 个分片",
    )


# 调试：按标签检索（Day4 验收用）
@router.get("/search")
def search_by_tag(
    query: str,
    tag: str | None = None,
    top_k: int = 5,
    current_user: User = Depends(get_current_user),
):
    """按标签过滤检索片段，用于 Day4 验收调试"""
    require_admin(current_user)
    hits = rag_service.retrieve_by_tag(query=query, tag=tag, top_k=top_k)
    return ApiResponse.success(data={"total": len(hits), "hits": hits}, msg="检索成功")