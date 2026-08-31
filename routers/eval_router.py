"""
检索评估 API
POST /api/eval/run  — 跑一轮评估，对比纯向量 vs 混合检索
GET  /api/eval/meta — 返回当前知识库的 tag 列表（前端构造测试样本时用）

expected_tag 支持逗号分隔多个值，命中任意一个就算召回成功；
未指定 expected_tag 时，只要有召回结果就算命中。
"""
import time
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends

from deps import get_current_user
from models.user_model import User
from utils.response import ApiResponse
from config.settings import settings

router = APIRouter(prefix="/api/eval", tags=["检索评估"])


class EvalSample(BaseModel):
    question: str
    expected_tag: str = ""


class EvalRunRequest(BaseModel):
    samples: List[EvalSample]
    top_k: int = 5


def _match_hits(hits: List[dict], expected_tag: str) -> List[dict]:
    """
    根据 expected_tag 判断 hits 中哪些算命中：
      - expected_tag 为空 → 全部 hits 都算命中（兜底模式）
      - expected_tag="tag1,tag2" → 任一 metadata.tag 在集合里就算命中
    """
    if not expected_tag or not expected_tag.strip():
        return hits
    wanted = set(t.strip() for t in expected_tag.split(",") if t.strip())
    return [h for h in hits if h.get("metadata", {}).get("tag") in wanted]


def _eval_single(query: str, expected_tag: str, top_k: int, use_hybrid: bool) -> dict:
    """对单个问题评估：临时切换 settings.HYBRID_ENABLE → 调 retrieve_by_tag"""
    original_flag = settings.HYBRID_ENABLE
    settings.HYBRID_ENABLE = use_hybrid
    try:
        from service.rag_service import retrieve_by_tag
        t0 = time.time()
        hits = retrieve_by_tag(query=query, tag=None, top_k=top_k, use_rerank=False)
        cost_ms = (time.time() - t0) * 1000
    except Exception as e:
        settings.HYBRID_ENABLE = original_flag
        return {
            "recall_at_k": False,
            "hit_count": 0,
            "total_hits": 0,
            "top_tags": [],
            "cost_ms": 0,
            "error": str(e),
        }
    finally:
        settings.HYBRID_ENABLE = original_flag

    matched = _match_hits(hits, expected_tag)
    return {
        "recall_at_k": len(matched) > 0,
        "hit_count": len(matched),
        "total_hits": len(hits),
        "top_tags": [h.get("metadata", {}).get("tag", "") for h in hits],
        "cost_ms": round(cost_ms, 1),
        "expected_tag": expected_tag,
    }


@router.post("/run")
def run_eval(req: EvalRunRequest, current_user: User = Depends(get_current_user)):
    """跑一轮完整评估：纯向量 vs 混合检索"""
    if not req.samples:
        return ApiResponse.error(msg="请传入至少 1 条测试样本", code=400)

    # 预热（一次就行）
    from service.rag_service import _get_collection, _get_embedding_fn
    try:
        _get_embedding_fn()
        col = _get_collection()
        if col.count() == 0:
            return ApiResponse.error(msg="向量库为空，请先上传文档", code=400)
    except Exception as e:
        return ApiResponse.error(msg=f"向量库初始化失败: {e}", code=500)

    vector_cases = []
    hybrid_cases = []

    for s in req.samples:
        v = _eval_single(s.question, s.expected_tag, req.top_k, use_hybrid=False)
        h = _eval_single(s.question, s.expected_tag, req.top_k, use_hybrid=True)
        vector_cases.append(v)
        hybrid_cases.append(h)

    n = len(req.samples)
    vec_recalled = sum(1 for r in vector_cases if r["recall_at_k"])
    hyb_recalled = sum(1 for r in hybrid_cases if r["recall_at_k"])
    vec_time = sum(r["cost_ms"] for r in vector_cases) / n if n else 0
    hyb_time = sum(r["cost_ms"] for r in hybrid_cases) / n if n else 0

    return ApiResponse.success(
        data={
            "top_k": req.top_k,
            "total": n,
            "vector": {
                "recall_at_k": round(vec_recalled / n * 100, 1) if n else 0,
                "hit_count": vec_recalled,
                "avg_cost_ms": round(vec_time, 1),
                "cases": [
                    {
                        "question": s.question,
                        "expected_tag": s.expected_tag,
                        "recall_at_k": vector_cases[i]["recall_at_k"],
                        "hit_count": vector_cases[i]["hit_count"],
                    }
                    for i, s in enumerate(req.samples)
                ],
            },
            "hybrid": {
                "recall_at_k": round(hyb_recalled / n * 100, 1) if n else 0,
                "hit_count": hyb_recalled,
                "avg_cost_ms": round(hyb_time, 1),
                "cases": [
                    {
                        "question": s.question,
                        "expected_tag": s.expected_tag,
                        "recall_at_k": hybrid_cases[i]["recall_at_k"],
                        "hit_count": hybrid_cases[i]["hit_count"],
                    }
                    for i, s in enumerate(req.samples)
                ],
            },
        },
        msg="评估完成",
    )


@router.get("/meta")
def eval_meta(current_user: User = Depends(get_current_user)):
    """返回向量库里所有已有的 tag，前端可用来构造测试样本"""
    from service.rag_service import _get_collection
    try:
        col = _get_collection()
        res = col.get(include=["metadatas"])
        tags = set()
        for m in res.get("metadatas", []) or []:
            t = m.get("tag") if m else None
            if t:
                for tag in str(t).split(","):
                    tag = tag.strip()
                    if tag:
                        tags.add(tag)
        return ApiResponse.success(data={"tags": sorted(tags)}, msg="ok")
    except Exception as e:
        return ApiResponse.error(msg=str(e), code=500)