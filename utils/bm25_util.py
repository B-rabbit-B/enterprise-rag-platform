"""
轻量 BM25 关键词检索工具（纯 Python 实现，无外部依赖）
- 支持中英文混合分词（英文按空格/标点，中文按 bigram 切分）
- 实现 BM25 经典算法（IDF + 词频 + 文档长度归一化）
- 对 chunk 集合构建索引，支持批量查询

设计考虑：
- 不引入 jieba 等额外依赖，降低部署门槛
- bigram 切分对中文短句效果足够好，配合 Reranker 精排兜底
"""
import math
import re
from typing import List, Dict, Tuple, Optional


def _tokenize(text: str) -> List[str]:
    """中英文混合分词：
    - 英文/数字按空格和标点切分，小写化
    - 中文按 bigram 滑动窗口切分（"北京天气" -> "北京" "京天" "天气"）
    """
    if not text:
        return []
    text = text.lower()

    tokens = []

    # 英文/数字部分：连续的 [a-z0-9_]
    for m in re.finditer(r"[a-z0-9_]+", text):
        w = m.group()
        if len(w) > 1:
            tokens.append(w)

    # 中文部分：bigram 切分
    chinese_chars = re.findall(r"[\u4e00-\u9fff]+", text)
    for segment in chinese_chars:
        if len(segment) >= 2:
            for i in range(len(segment) - 1):
                tokens.append(segment[i:i + 2])
        elif len(segment) == 1:
            tokens.append(segment)

    return tokens


class BM25Index:
    """
    BM25 文档索引，对一组 chunks 构建倒排表，支持关键词打分检索。

    用法：
        bm25 = BM25Index.build(chunks)   # chunks: [str, ...]
        hits = bm25.search(query, top_k=5)  # -> [(idx, score), ...]
    """

    K1 = 1.5
    B = 0.75

    def __init__(
        self,
        chunks: List[str],
        doc_token_freqs: List[Dict[str, int]],
        doc_lens: List[int],
        avgdl: float,
        idf: Dict[str, float],
    ):
        self.chunks = chunks
        self._doc_token_freqs = doc_token_freqs
        self._doc_lens = doc_lens
        self._avgdl = avgdl
        self._idf = idf
        self._doc_count = len(chunks)

    @classmethod
    def build(cls, chunks: List[str]) -> "BM25Index":
        """从 chunk 列表构建索引"""
        if not chunks:
            return cls([], [], [], 0.0, {})

        # 1. 分词 + 统计每个文档的词频
        doc_token_freqs: List[Dict[str, int]] = []
        doc_lens: List[int] = []
        for text in chunks:
            tokens = _tokenize(text)
            freq: Dict[str, int] = {}
            for t in tokens:
                freq[t] = freq.get(t, 0) + 1
            doc_token_freqs.append(freq)
            doc_lens.append(len(tokens))

        # 2. 计算平均文档长度
        avgdl = sum(doc_lens) / len(doc_lens) if doc_lens else 0.0

        # 3. 计算 IDF：每个词出现在多少篇文档中
        df: Dict[str, int] = {}
        for freq in doc_token_freqs:
            for t in freq.keys():
                df[t] = df.get(t, 0) + 1

        doc_count = len(chunks)
        idf: Dict[str, float] = {}
        for term, freq in df.items():
            # BM25 IDF 公式：log((N - df + 0.5) / (df + 0.5))
            idf[term] = math.log((doc_count - freq + 0.5) / (freq + 0.5) + 1.0)

        return cls(chunks, doc_token_freqs, doc_lens, avgdl, idf)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        BM25 检索，返回 [(chunk_index, score), ...] 按分数降序。
        分数做归一化，映射到 [0, 1]，方便与向量分数融合。
        """
        if not self.chunks or not query:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scores: List[float] = [0.0] * self._doc_count

        for d_idx in range(self._doc_count):
            freq = self._doc_token_freqs[d_idx]
            dl = self._doc_lens[d_idx]
            denom = self.K1 * (1 - self.B + self.B * dl / self._avgdl) if self._avgdl > 0 else self.K1

            for t in query_tokens:
                if t not in self._idf:
                    continue
                tf = freq.get(t, 0)
                if tf == 0:
                    continue
                numer = tf * (self.K1 + 1)
                scores[d_idx] += self._idf[t] * numer / (denom + tf)

        # 归一化到 [0, 1]
        if max(scores) > 0:
            scores = [s / max(scores) for s in scores]

        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        # 过滤得分为 0 的
        ranked = [(idx, s) for idx, s in ranked if s > 0]
        return ranked[:top_k]


def hybrid_fuse(
    vector_hits: List[Dict],
    bm25_results: List[Tuple[int, float]],
    bm25_chunk_ids: List[str],
    bm25_index_map: Dict[str, int],
    vector_weight: float = 0.6,
    bm25_weight: float = 0.4,
) -> List[Dict]:
    """
    融合向量检索和 BM25 关键词检索结果。

    :param vector_hits: 向量检索结果，每个含 "id"、"distance"、"document" 等字段
    :param bm25_results: BM25 结果 [(chunk_idx, score), ...]
    :param bm25_chunk_ids: BM25 索引对应的 chunk id 列表（与向量库 ids 一致）
    :param bm25_index_map: 向量库 id -> BM25 索引位置的映射
    :param vector_weight: 向量分数权重
    :param bm25_weight: BM25 分数权重
    :return: 融合排序后的 hits 列表
    """
    if not vector_hits and not bm25_results:
        return []
    if not vector_hits:
        # 只有 BM25 命中
        output = []
        for idx, score in bm25_results:
            cid = bm25_chunk_ids[idx]
            output.append({
                "id": cid,
                "document": "",
                "metadata": {},
                "distance": 1.0 - score,
                "bm25_score": score,
                "vector_score": 0.0,
                "hybrid_score": score * bm25_weight,
            })
        return output

    # 1. 向量分数归一化：distance 越小越好，转为 similarity = 1 - distance/max_dist
    v_min_dist = min(h["distance"] for h in vector_hits) if vector_hits else 0
    v_max_dist = max(h["distance"] for h in vector_hits) if vector_hits else 1
    v_range = v_max_dist - v_min_dist if v_max_dist > v_min_dist else 1.0

    # 2. 建立 BM25 得分查找表：chunk_id -> bm25_score
    bm25_score_map: Dict[str, float] = {}
    for idx, score in bm25_results:
        cid = bm25_chunk_ids[idx] if idx < len(bm25_chunk_ids) else None
        if cid:
            bm25_score_map[cid] = score

    # 3. 融合所有候选（向量命中 + BM25 命中并集）
    seen_ids: set = set()
    candidates: List[Dict] = []

    for h in vector_hits:
        cid = h["id"]
        if cid in seen_ids:
            continue
        seen_ids.add(cid)

        # 向量相似度（归一化到 0~1）
        v_sim = 1.0 - (h["distance"] - v_min_dist) / v_range if v_range > 0 else 1.0
        b_score = bm25_score_map.get(cid, 0.0)
        fused = vector_weight * v_sim + bm25_weight * b_score

        h_copy = dict(h)
        h_copy["vector_score"] = v_sim
        h_copy["bm25_score"] = b_score
        h_copy["hybrid_score"] = fused
        candidates.append(h_copy)

    # 加入仅在 BM25 中命中的候选
    for idx, score in bm25_results:
        cid = bm25_chunk_ids[idx] if idx < len(bm25_chunk_ids) else None
        if not cid or cid in seen_ids:
            continue
        seen_ids.add(cid)
        candidates.append({
            "id": cid,
            "document": "",
            "metadata": {},
            "distance": 1.0,
            "vector_score": 0.0,
            "bm25_score": score,
            "hybrid_score": score * bm25_weight,
        })

    # 4. 按融合分数降序
    candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return candidates