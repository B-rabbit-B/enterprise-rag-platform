"""
RAG 检索效果评估脚本

功能：
  1) 构造一批 "问题 → 期望命中文档(标签)" 的测试样本
  2) 分别用【纯向量检索】和【混合检索】跑一遍
  3) 统计 Recall@K（目标文档是否出现在 top-K 结果中）
  4) 打印对比表格，量化优化前后的差异

设计：
  - 复用 rag_service.retrieve_by_tag，切换 settings.HYBRID_ENABLE 即可对比
  - 不调用 LLM（避免耗时和 Token 费用），只评检索质量
  - 无需写死测试数据，测试样本写在下方 SAMPLES 里，改完脚本直接 run

用法：
  cd d:\\enterprise-rag-platform
  python tests/evaluate_rag.py
"""
import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings

# ============ 测试样本：用户自行修改 ============
# question: 用户问题
# expected_tag: 期望命中的文档 tag（用于粗粒度评估：top-K 里是否出现了该 tag）
# 注：更精细的评估是指定具体 chunk id，但这需要标注数据，这里用 tag 级别做轻量评估
SAMPLES = [
    # --- 示例 1：通用语义问 ---
    {
        "question": "FastAPI 如何处理请求参数校验？",
        "expected_tag": "fastapi_doc",
    },
    # --- 示例 2：关键词精确问（BM25 应该更擅长）---
    {
        "question": "SQLAlchemy 的 Column 定义参数有哪些？",
        "expected_tag": "sqlalchemy_doc",
    },
    # --- 示例 3：中英文混合问 ---
    {
        "question": "ChromaDB PersistentClient 怎么配置",
        "expected_tag": "chroma_doc",
    },
    # --- 示例 4：长 query ---
    {
        "question": "RAG 系统中如果向量检索没有召回到相关文档应该怎么处理，有没有短路机制来节省 LLM 的调用开销？",
        "expected_tag": "rag_doc",
    },
    # --- 示例 5：专业术语（BM25 关键词强命中）---
    {
        "question": "BGE Reranker Cross Encoder 的原理是什么？",
        "expected_tag": "reranker_doc",
    },
]
# ================================================


def evaluate_retrieval(
    query: str,
    expected_tag: str,
    top_k: int = 5,
    use_hybrid: bool = True,
) -> dict:
    """
    对单个问题评估检索质量。

    指标：
      - recall_at_k：期望 tag 是否出现在 top-K 检索结果中
      - hit_count：top-K 中 tag 匹配的数量
      - has_keyword_hit：BM25 特有的关键词（query 中出现的术语）是否被命中
    """
    # 临时切换混合检索开关
    original_flag = settings.HYBRID_ENABLE
    settings.HYBRID_ENABLE = use_hybrid

    try:
        from service.rag_service import retrieve_by_tag
        hits = retrieve_by_tag(query=query, tag=None, top_k=top_k, use_rerank=False)
    except Exception as e:
        return {
            "recall_at_k": False,
            "hit_count": 0,
            "top_k": top_k,
            "expected_tag": expected_tag,
            "mode": "hybrid" if use_hybrid else "vector",
            "error": str(e),
        }
    finally:
        settings.HYBRID_ENABLE = original_flag

    matched = [h for h in hits if h.get("metadata", {}).get("tag") == expected_tag]
    return {
        "recall_at_k": len(matched) > 0,
        "hit_count": len(matched),
        "total_hits": len(hits),
        "top_k": top_k,
        "expected_tag": expected_tag,
        "mode": "hybrid" if use_hybrid else "vector",
        "top_tags": [h.get("metadata", {}).get("tag", "") for h in hits],
    }


def run_evaluation():
    """
    跑一轮完整评估：纯向量 vs 混合检索，对比 Recall@K
    """
    print("=" * 70)
    print("  RAG 检索效果评估脚本")
    print(f"  测试样本数: {len(SAMPLES)}")
    print(f"  评估指标 : Recall@K（期望文档是否出现在 top-K 结果中）")
    print("=" * 70)

    # 预热模型（避免第一次请求的加载时间干扰）
    print("\n[预热] 初始化向量库 / Embedding 模型 ...")
    from service.rag_service import _get_collection, _get_embedding_fn
    try:
        _get_embedding_fn()
        col = _get_collection()
        count = col.count()
        print(f"[预热] 完成，向量库共 {count} 个 chunk")
    except Exception as e:
        print(f"[预热] 失败: {e}")
        print("提示：请先上传文档（POST /api/doc/upload）构造知识库后再运行评估")
        return

    if col.count() == 0:
        print("⚠ 向量库为空，请先上传文档！")
        return

    top_k = settings.RAG_RETRIEVE_TOP_K

    print(f"\n--- 评估参数：top_k={top_k} ---\n")

    vector_results = []
    hybrid_results = []

    for i, sample in enumerate(SAMPLES):
        q = sample["question"]
        tag = sample["expected_tag"]
        print(f"[{i + 1}/{len(SAMPLES)}] Q: {q[:60]}...")
        print(f"   期望 tag: {tag}")

        # 纯向量
        t0 = time.time()
        v_res = evaluate_retrieval(q, tag, top_k=top_k, use_hybrid=False)
        v_time = time.time() - t0
        v_res["cost"] = v_time
        vector_results.append(v_res)

        # 混合检索
        t0 = time.time()
        h_res = evaluate_retrieval(q, tag, top_k=top_k, use_hybrid=True)
        h_time = time.time() - t0
        h_res["cost"] = h_time
        hybrid_results.append(h_res)

        print(f"   纯向量: recall={'✓' if v_res['recall_at_k'] else '✗'} | "
              f"命中数={v_res['hit_count']} | top_tags={v_res.get('top_tags', [])[:top_k]} | {v_time:.2f}s")
        print(f"   混合检索: recall={'✓' if h_res['recall_at_k'] else '✗'} | "
              f"命中数={h_res['hit_count']} | top_tags={h_res.get('top_tags', [])[:top_k]} | {h_time:.2f}s")
        print()

    # ============ 汇总对比 ============
    def _summary(results: list):
        total = len(results)
        recalled = sum(1 for r in results if r["recall_at_k"])
        avg_hit = sum(r["hit_count"] for r in results) / total if total else 0
        avg_time = sum(r["cost"] for r in results) / total if total else 0
        return {
            "total": total,
            "recalled": recalled,
            "recall_rate": recalled / total if total else 0,
            "avg_hit": avg_hit,
            "avg_time": avg_time,
        }

    vec_summary = _summary(vector_results)
    hyb_summary = _summary(hybrid_results)

    print("=" * 70)
    print("  评估结果汇总")
    print("=" * 70)
    print(f"{'指标':<20} {'纯向量检索':<20} {'混合检索':<20} {'提升'}")
    print("-" * 70)
    print(f"{'Recall@K':<20} {vec_summary['recall_rate']:.2%}{'':<14} "
          f"{hyb_summary['recall_rate']:.2%}{'':<14} "
          f"+{(hyb_summary['recall_rate'] - vec_summary['recall_rate']):.2%}")
    print(f"{'平均命中数':<16} {vec_summary['avg_hit']:.2f}{'':<15} "
          f"{hyb_summary['avg_hit']:.2f}{'':<15} "
          f"+{hyb_summary['avg_hit'] - vec_summary['avg_hit']:.2f}")
    print(f"{'平均耗时(ms)':<14} {vec_summary['avg_time'] * 1000:.0f}{'':<15} "
          f"{hyb_summary['avg_time'] * 1000:.0f}{'':<15} "
          f"{''}")
    print()

    # 保存详细结果
    report_path = Path(__file__).parent / "evaluation_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"评估时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"测试样本: {len(SAMPLES)}\n")
        f.write(f"Top-K: {top_k}\n\n")
        f.write("=== 纯向量 ===\n")
        for r in vector_results:
            f.write(f"  Q: {SAMPLES[vector_results.index(r)]['question']}\n")
            f.write(f"    recall={r['recall_at_k']} hits={r['hit_count']} tags={r.get('top_tags', [])}\n")
        f.write(f"\n=== 混合检索 ===\n")
        for r in hybrid_results:
            f.write(f"  Q: {SAMPLES[hybrid_results.index(r)]['question']}\n")
            f.write(f"    recall={r['recall_at_k']} hits={r['hit_count']} tags={r.get('top_tags', [])}\n")
        f.write(f"\n=== 汇总 ===\n")
        f.write(f"  纯向量 Recall@{top_k}: {vec_summary['recall_rate']:.2%}\n")
        f.write(f"  混合检索 Recall@{top_k}: {hyb_summary['recall_rate']:.2%}\n")
    print(f"📄 详细报告已保存到: {report_path}")


if __name__ == "__main__":
    run_evaluation()