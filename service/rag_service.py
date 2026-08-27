"""
RAG 向量服务：Chroma 向量入库 + 按标签过滤检索
Day4 实现：仅向量召回；Rerank 放到 Day5 由 utils/rerank_util.py 处理
"""
import os
from typing import List, Optional

import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings

from config.settings import settings
from utils.rerank_util import Reranker

# ---------- 初始化 Chroma 客户端（仅创建目录，不下载模型）----------
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)

client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIR,
    settings=Settings(anonymized_telemetry=False),
)

COLLECTION_NAME = "enterprise_docs"

# 延迟初始化：首次使用时才加载 embedding 模型
_embedding_fn = None
_collection = None


def _get_embedding_fn():
    """懒加载 embedding 函数（首次调用时才下载/加载模型）"""
    global _embedding_fn
    if _embedding_fn is None:
        print(f"[rag_service] 正在加载 embedding 模型: {settings.EMBEDDING_MODEL} ...")
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        print("[rag_service] embedding 模型加载完成")
    return _embedding_fn


def _get_collection():
    """懒加载 collection（首次调用时才创建）"""
    global _collection
    if _collection is None:
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=_get_embedding_fn(),
        )
    return _collection

def upsert_document_chunks(
    doc_id: int,
    filename: str,
    tag: str,
    chunks: List[str],
) -> int:
    """
    将文档分块写入 Chroma。
    每个 chunk 的 metadata 包含：
        - doc_id, filename, tag, chunk_index
    返回写入的 chunk 数量。
    """
    if not chunks:
        return 0

    ids = [f"doc_{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "doc_id": doc_id,
            "filename": filename,
            "tag": tag or "",
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]

    col = _get_collection()
    col.upsert(
        ids=ids,
        documents=chunks,
        metadatas=metadatas,
    )
    return len(chunks)

def delete_document_chunks(doc_id: int) -> int:
    """删除指定文档的所有分块"""
    col = _get_collection()
    res = col.get(where={"doc_id": doc_id})
    ids = res.get("ids", [])
    if not ids:
        return 0
    col = _get_collection()
    col.delete(ids=ids)
    return len(ids)

def retrieve_by_tag(
    query: str,
    tag: Optional[str] = None,
    top_k: int = 5,
    use_rerank: bool = False,
) -> List[dict]:
    """
    按标签过滤检索。
    - tag 为空：全库召回
    - tag 非空：加 where 过滤
    - use_rerank=True：使用 Reranker 重排（Day5 启用）
    返回：[{"id","document","metadata","distance"}, ...]
    """
    where_filter = {"tag": tag} if tag else None

    col = _get_collection()
    results = col.query(
        query_texts=[query],
        n_results=top_k * 2 if use_rerank else top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    if not results or not results["ids"] or not results["ids"][0]:
        return []

    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    hits = [
        {
            "id": ids[i],
            "document": docs[i],
            "metadata": metas[i],
            "distance": distances[i],
        }
        for i in range(len(ids))
    ]

    # 可选 Rerank（占位，Day5 真正启用）
    if use_rerank and hits:
        reranker = Reranker()
        documents = [h["document"] for h in hits]
        ranked = reranker.rerank(query=query, documents=documents, top_k=top_k)
        hits = [hits[idx] for idx, _ in ranked]

    return hits[:top_k]

def list_collections():
    """调试用：查看集合信息"""
    return {
        "name": _get_collection().name,
        "count": _get_collection().count(),
    }