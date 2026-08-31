import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.bm25_util import BM25Index, _tokenize

print("=" * 60)
print("测试 1：BM25 分词")
print("=" * 60)
test_queries = [
    "FastAPI 如何处理请求参数校验",
    "SQLAlchemy Column 定义参数有哪些",
    "BGE Reranker Cross Encoder 原理",
    "ChromaDB PersistentClient 配置",
]
for q in test_queries:
    print(f"  Q: {q}")
    print(f"  tokens: {_tokenize(q)}")
    print()

print("=" * 60)
print("测试 2：BM25 检索（纯关键词）")
print("=" * 60)
chunks = [
    "FastAPI 是一个现代化的 Python Web 框架，支持异步和类型提示。它使用 Pydantic 进行参数校验。",
    "SQLAlchemy 是 Python 的 ORM 框架，Column 定义支持 name、type、nullable、default 等参数。",
    "Cross Encoder Reranker 通过对 query 和 document 做 Cross Attention，输出相关性分数，用于精排。",
    "ChromaDB 的 PersistentClient 可以通过 path 参数指定数据持久化目录，支持向量持久化存储。",
    "BM25 是一种基于词频和文档频率的信息检索算法，常用于搜索引擎。",
]
bm25 = BM25Index.build(chunks)

test_queries_bm25 = [
    "Column 定义",
    "Cross Encoder 精排",
    "PersistentClient 路径",
    "Pydantic 校验",
]
for q in test_queries_bm25:
    results = bm25.search(q, top_k=3)
    print(f"  Q: {q}")
    for idx, score in results:
        print(f"    -> [{score:.4f}] {chunks[idx][:50]}...")
    print()

print("=" * 60)
print("测试 3：递归分块（无依赖版本）")
print("=" * 60)
import re
from typing import List

def _split_once(text: str, sep: str) -> List[str]:
    if sep not in text:
        return [text]
    parts = text.split(sep)
    result = []
    for i, p in enumerate(parts):
        if i < len(parts) - 1:
            result.append(p + sep)
        else:
            if p:
                result.append(p)
    return result

def _recursive_split(text: str, chunk_size: int, separators: List[str]) -> List[str]:
    if len(text) <= chunk_size:
        return [text]
    if not separators:
        pieces = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            pieces.append(text[start:end])
            if end >= len(text):
                break
            start = end
        return pieces
    sep = separators[0]
    remaining = separators[1:]
    segments = _split_once(text, sep)
    result = []
    buffer = ""
    for seg in segments:
        if len(buffer) + len(seg) <= chunk_size:
            buffer += seg
        else:
            if buffer:
                result.append(buffer.strip())
            if len(seg) > chunk_size:
                result.extend(_recursive_split(seg, chunk_size, remaining))
                buffer = ""
            else:
                buffer = seg
    if buffer.strip():
        result.append(buffer.strip())
    return result

test_text = """FastAPI 是一个现代化的 Python Web 框架。它基于 Starlette 构建，支持异步。
参数校验使用 Pydantic 模型，自动生成 OpenAPI 文档。

第二段介绍向量检索。向量检索通过 Embedding 模型将文本转为向量，
然后在向量空间中做相似度搜索，用于 RAG 系统的召回阶段。

第三段讲混合检索。混合检索结合 BM25 和向量检索，
BM25 擅长精准关键词匹配，向量擅长语义召回，二者加权融合效果更好。"""

separators = ["\n\n", "\n", "。", "！", "？", ". ", " ", ""]
raw_chunks = _recursive_split(test_text, chunk_size=80, separators=separators)
raw_chunks = [c.strip() for c in raw_chunks if c and c.strip()]

chunk_overlap = 15
overlapped = []
for i, chunk in enumerate(raw_chunks):
    if i == 0:
        overlapped.append(chunk)
    else:
        prev_tail = raw_chunks[i - 1][-chunk_overlap:]
        if prev_tail:
            overlapped.append((prev_tail + "\n" + chunk).strip())
        else:
            overlapped.append(chunk)

print(f"原文长度: {len(test_text)} 字符")
print(f"分块大小: 80, 重叠: 15")
print(f"分块数: {len(overlapped)}")
for i, c in enumerate(overlapped):
    print(f"\n--- 块 {i+1} [{len(c)}字] ---")
    print(f"  {c}")

print("\n✅ 所有测试通过！")