"""
Rerank 工具：基于 BGE-Reranker 的 Cross-Encoder 重排序
- Reranker：保留原接口（给 rag_service.py 用），实现真正的语义重排
- RerankUtil：Day5 对外高层封装，直接对 hits 列表重排并返回 top_n
"""
import os
from typing import List, Dict

# 国内镜像加速
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")


def _lazy_load_model():
    """延迟加载 reranker 模型，避免 import 时就下载/占显存"""
    from sentence_transformers import CrossEncoder
    # 使用 bge-reranker-base（轻量快速）
    return CrossEncoder("BAAI/bge-reranker-base")


class Reranker:
    """
    通用 Reranker（供 rag_service.retrieve_by_tag 使用）。
    保留旧签名：rerank(query, documents, top_k) -> List[(idx, score)]
    """
    _model = None

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            cls._model = _lazy_load_model()
        return cls._model

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5,
    ) -> List[tuple]:
        """
        Cross-Encoder 逐条打分。
        返回: [(index, score), ...] 按 score 降序取 top_k
        """
        if not documents:
            return []
        model = self._get_model()
        pairs = [[query, doc] for doc in documents]
        scores = model.predict(pairs)
        # scores 为 numpy array，转原生 float
        scored = [(i, float(s)) for i, s in enumerate(scores)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


class RerankUtil:
    """
    Day5 高层封装：直接对 hits 列表（含 document 字段）做重排，
    过滤低相关性片段，返回 top_n 条并带上 rerank_score。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._reranker = Reranker()
        return cls._instance

    def rerank(self, query: str, hits: List[Dict], top_n: int = 3) -> List[Dict]:
        """
        :param query: 用户问题
        :param hits: 向量检索返回的 hits 数组，元素形如 {"document": str, "metadata": dict, ...}
        :param top_n: 重排之后保留片段数量
        :return: 重排过滤后的 hits 列表（带 rerank_score 字段）
        """
        if not hits:
            return []
        documents = [item["document"] for item in hits]
        ranked = self._reranker.rerank(query=query, documents=documents, top_k=len(hits))

        # 绑定分数写回 hits
        for idx, score in ranked:
            hits[idx]["rerank_score"] = score

        # 按分数降序取 top_n
        sorted_hits = sorted(
            [hits[i] for i, _ in ranked],
            key=lambda x: x["rerank_score"],
            reverse=True,
        )
        return sorted_hits[:top_n]


def preload():
    """
    服务启动时预热 Reranker 模型，把首次加载耗时从用户第一次请求挪到服务启动阶段。
    在 main.py 启动时调用即可。
    """
    try:
        print("[rerank_util] 正在预加载 BGE-Reranker 模型 ...")
        Reranker._get_model()
        print("[rerank_util] Reranker 模型预加载完成")
    except Exception as e:
        print(f"[rerank_util] Reranker 预加载失败（不影响服务启动）：{e}")