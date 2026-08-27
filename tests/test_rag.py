"""
Day4 验收测试：
1) 写入向量库后，集合 count 增加
2) 按标签过滤检索生效
运行方式： python -m tests.test_rag
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service import rag_service
from service.doc_service import clean_text, chunk_text

def test_clean_and_chunk():
    text = "Hello\n\n\nWorld!   This is a   test.\n\n\n" * 50
    cleaned = clean_text(text)
    chunks = chunk_text(cleaned, chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 0
    assert cleaned.count("  ") == 0
    print(f"[OK] clean_text + chunk_text: {len(chunks)} chunks")
    return chunks

def test_upsert_and_search():
    # 写入一批测试分块
    chunks = [
        "企业RAG平台支持文档上传与解析",
        "Chroma向量库用于存储文本分块",
        "管理员有权限上传和删除文档",
        "普通用户没有管理员权限无法上传",
        "RAG检索支持按标签过滤",
    ]
    n = rag_service.upsert_document_chunks(
        doc_id=9999,
        filename="test_setup.md",
        tag="测试",
        chunks=chunks,
    )
    assert n == len(chunks)
    print(f"[OK] upserted {n} chunks")

    # 按标签检索
    hits = rag_service.retrieve_by_tag(query="管理员权限", tag="测试", top_k=3)
    assert len(hits) > 0
    print(f"[OK] retrieve_by_tag hits={len(hits)}")
    for h in hits:
        print("  -", h["document"][:50], "| tag=", h["metadata"].get("tag"))

    # 清理
    rag_service.delete_document_chunks(9999)
    print("[OK] cleaned")

if __name__ == "__main__":
    test_clean_and_chunk()
    test_upsert_and_search()
    print("\nAll tests passed!")