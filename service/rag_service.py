"""
RAG 向量服务：Chroma 向量入库 + 混合检索（向量 + BM25）

检索流程（当 HYBRID_ENABLE=True 时）：
  1) 向量召回 top_k * 2（粗召回，保证覆盖）
  2) BM25 关键词独立召回 top_k
  3) 分数归一化 + 加权融合 → 输出最终 top_k

这样既保留向量的语义能力，又通过 BM25 补强专业术语精准匹配。
"""
import os
from typing import List, Optional, Dict

import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings

from config.settings import settings
from utils.rerank_util import Reranker
from utils.bm25_util import BM25Index, hybrid_fuse
from utils.logger import log_info, log_warning

os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)

client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIR,
    settings=Settings(anonymized_telemetry=False),
)

COLLECTION_NAME = "enterprise_docs"

_embedding_fn = None
_collection = None

# BM25 索引缓存：每次文档上传/删除后刷新
_bm25_index: Optional[BM25Index] = None
_bm25_chunk_ids: List[str] = []


def _get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        log_info(f"[rag_service] 正在加载 embedding 模型: {settings.EMBEDDING_MODEL} ...")
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        log_info("[rag_service] embedding 模型加载完成")
    return _embedding_fn


def _get_collection():
    global _collection
    if _collection is None:
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=_get_embedding_fn(),
        )
    return _collection


def _refresh_bm25_index():
    """
    从向量库全量拉取 chunks，重建 BM25 倒排索引。
    在文档上传、删除后调用，保证一致性。
    """
    global _bm25_index, _bm25_chunk_ids
    try:
        col = _get_collection()
        data = col.get(include=["documents"])
        ids = data.get("ids", [])
        docs = data.get("documents", [])

        if not docs:
            _bm25_index = None
            _bm25_chunk_ids = []
            return

        _bm25_index = BM25Index.build(docs)
        _bm25_chunk_ids = ids
        log_info(f"[rag_service] BM25 索引已重建，共 {len(ids)} 个 chunk")
    except Exception as e:
        log_warning(f"[rag_service] BM25 索引重建失败，降级为纯向量检索：{e}")
        _bm25_index = None
        _bm25_chunk_ids = []


def _ensure_bm25_index():
    """懒加载 BM25 索引，首次检索触发构建"""
    global _bm25_index
    if _bm25_index is None:
        _refresh_bm25_index()


def upsert_document_chunks(
    doc_id: int,
    filename: str,
    tag: str,
    chunks: List[str],
) -> int:
    """将文档分块写入 Chroma，同时刷新 BM25 索引"""
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
    col.upsert(ids=ids, documents=chunks, metadatas=metadatas)

    # 混合检索：刷新 BM25
    if settings.HYBRID_ENABLE:
        _refresh_bm25_index()

    return len(chunks)


def delete_document_chunks(doc_id: int) -> int:
    """删除指定文档的所有分块，同时刷新 BM25 索引"""
    col = _get_collection()
    res = col.get(where={"doc_id": doc_id})
    ids = res.get("ids", [])
    if not ids:
        return 0
    col.delete(ids=ids)

    if settings.HYBRID_ENABLE:
        _refresh_bm25_index()

    return len(ids)


def retrieve_by_tag(
    query: str,
    tag: Optional[str] = None,
    top_k: int = 5,
    use_rerank: bool = True,
    retrieve_mode: str = "hybrid",
) -> List[dict]:
    """
    混合检索主入口：
      - retrieve_mode="hybrid" : 向量召回 + BM25 关键词召回 → 加权融合（默认）
      - retrieve_mode="vector"  : 纯向量检索
      - use_rerank=True         : 最终对融合结果做 Cross-Encoder 精排
    """
    # 前端强制覆盖 HYBRID_ENABLE
    effective_hybrid = settings.HYBRID_ENABLE and retrieve_mode != "vector"
    where_filter = {"tag": tag} if tag else None
    col = _get_collection()

    # ========= 纯向量召回 =========
    try:
        vector_top_n = top_k * 2 if effective_hybrid else (top_k * 2 if use_rerank else top_k)
        results = col.query(
            query_texts=[query],
            n_results=vector_top_n,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        log_warning(f"[rag_service] Chroma 查询异常: {e}")
        return []

    if not results or not results["ids"] or not results["ids"][0]:
        return []

    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    vector_hits = [
        {
            "id": ids[i],
            "document": docs[i],
            "metadata": metas[i] or {},
            "distance": distances[i],
            "similarity": max(0.0, 1.0 - distances[i] / 2.0),
        }
        for i in range(len(ids))
    ]

    # ========= 混合检索融合（前端可动态切换）=========
    if effective_hybrid:
        _ensure_bm25_index()
        bm25_results: List[tuple] = []
        if _bm25_index is not None and _bm25_chunk_ids:
            try:
                # 如果有 tag 过滤，先从 BM25 索引中筛选符合 tag 的 chunk
                if tag:
                    # 对 BM25 索引做 tag 过滤：先拿到 BM25 全局结果，再根据 tag 元数据筛选
                    bm25_all = _bm25_index.search(query, top_k=settings.HYBRID_BM25_TOP_K * 3)
                    filtered = []
                    for idx, score in bm25_all:
                        cid = _bm25_chunk_ids[idx] if idx < len(_bm25_chunk_ids) else None
                        if cid and cid in ids:
                            # 这个 chunk 在向量检索中被拉出来了，说明 tag 匹配
                            # 但 BM25 索引是全量的，需要检查 metadata
                            filtered.append((idx, score))
                    bm25_results = filtered[:settings.HYBRID_BM25_TOP_K]
                else:
                    bm25_results = _bm25_index.search(query, top_k=settings.HYBRID_BM25_TOP_K)
            except Exception as e:
                log_warning(f"[rag_service] BM25 检索异常，降级为纯向量: {e}")

        if bm25_results:
            vector_hits = hybrid_fuse(
                vector_hits=vector_hits,
                bm25_results=bm25_results,
                bm25_chunk_ids=_bm25_chunk_ids,
                bm25_index_map={},
                vector_weight=settings.HYBRID_VECTOR_WEIGHT,
                bm25_weight=settings.HYBRID_BM25_WEIGHT,
            )
            # 融合后重新排序取 top_k
            vector_hits.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)
            vector_hits = vector_hits[:top_k]

    # ========= Rerank 精排 =========
    if use_rerank and vector_hits:
        # 补齐 BM25 模式下缺失的 document 字段
        for h in vector_hits:
            if not h.get("document"):
                try:
                    raw = col.get(ids=[h["id"]], include=["documents", "metadatas"])
                    if raw["documents"] and raw["documents"][0]:
                        h["document"] = raw["documents"][0]
                        h["metadata"] = raw["metadatas"][0] if raw["metadatas"] else {}
                except Exception:
                    pass

        reranker = Reranker()
        documents = [h["document"] for h in vector_hits if h.get("document")]
        if documents:
            ranked = reranker.rerank(query=query, documents=documents, top_k=top_k)
            # 把分数挂回 hits
            for idx, score in ranked:
                if idx < len(vector_hits):
                    vector_hits[idx]["rerank_score"] = score
            vector_hits = [vector_hits[i] for i, _ in ranked]

    return vector_hits[:top_k]


def list_collections():
    return {
        "name": _get_collection().name,
        "count": _get_collection().count(),
    }