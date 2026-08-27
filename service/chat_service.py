import json
import time
from typing import Optional, List, Dict

from sqlalchemy.orm import Session
from datetime import datetime

from config.settings import settings
from models.chat_model import ChatSession, ChatMessage

# ---------- RAG 依赖 --------
from service.rag_service import retrieve_by_tag
from utils.rerank_util import RerankUtil
from utils.token_counter import truncate_context
from utils.logger import log_rag_request

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except Exception:
    _OPENAI_AVAILABLE = False

# 初始化兼容 OpenAI 客户端（阿里云百炼 / 其他兼容模式）
client = None
if _OPENAI_AVAILABLE and settings.LLM_API_KEY:
    try:
        client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            timeout=30,
        )
    except Exception:
        client = None


def create_chat_session(db: Session, user_id: int, title: str):
    sess = ChatSession(user_id=user_id, title=title)
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


def get_user_session_list(db: Session, user_id: int):
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.update_time.desc()).all()


def get_session_by_id(db: Session, session_id: int):
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def add_chat_message(db: Session, session_id: int, role: str, content: str):
    sess = get_session_by_id(db, session_id)
    if not sess:
        raise Exception("会话不存在")
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(msg)
    sess.update_time = datetime.now()
    db.commit()
    db.refresh(msg)
    return msg



def get_messages_by_session_id(db: Session, session_id: int):
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.create_time).all()


def delete_session(db: Session, session_id: int):
    # synchronize_session=False：告知 SQLAlchemy 不同步本地会话缓存，
    # 直接执行 SQL 删除，避免批量删除后残留的脏数据
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete(
        synchronize_session=False
    )
    db.query(ChatSession).filter(ChatSession.id == session_id).delete(
        synchronize_session=False
    )
    db.commit()


# ========== Day5：完整 RAG 问答链路 ==========

RAG_PROMPT_TEMPLATE = """
你是知识库问答助手，请严格基于下面【参考上下文】回答用户问题。
规则：
1. 只允许使用参考上下文内提供的信息；不要编造、不要使用你的固有知识。
2. 如果上下文没有相关答案，请直接回复：【未在知识库找到相关信息】
3. 回答末尾输出参考来源：文档名称、文档ID

【参考上下文】
{context_content}

【用户问题】
{user_query}
"""


def build_context_text(hits: List[Dict]) -> str:
    """把多段 hits 拼接为大模型可读的上下文字符串，并附带来源元数据"""
    parts = []
    for h in hits:
        meta = h.get("metadata", {})
        filename = meta.get("filename", "?")
        doc_id = meta.get("doc_id", "?")
        parts.append(f"[文档名:{filename} | doc_id:{doc_id}]\n{h['document']}")
    return "\n=====\n".join(parts)


def _save_rag_messages(
    db: Session,
    session_id: int,
    user_query: str,
    answer: str,
    reference: List[Dict],
) -> ChatMessage:
    """将用户提问和 AI 回答分别持久化；AI 回答附带溯源元数据"""
    # 用户消息
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=user_query,
    )
    db.add(user_msg)

    # AI 回答，溯源信息存 extra_json
    ai_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer,
        extra_json=json.dumps({"reference": reference}, ensure_ascii=False),
    )
    db.add(ai_msg)

    # 更新会话时间
    sess = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if sess:
        sess.update_time = datetime.now()

    db.commit()
    db.refresh(ai_msg)
    return ai_msg


def rag_chat(
    db: Session,
    user_query: str,
    tag_filter: Optional[str],
    session_id: int,
    user_id: int,
) -> dict:
    """
    完整 RAG 业务链路：
    1) 向量召回 top_k → 2) Rerank 重排序 → 3) Token 截断
    → 4) 组装约束 Prompt → 5) 调用 LLM → 6) 消息持久化（含溯源）
    """
    _total_start = time.time()

    # 1. 向量召回
    _t0 = time.time()
    try:
        raw_hits = retrieve_by_tag(
            query=user_query,
            tag=tag_filter,
            top_k=settings.RAG_RETRIEVE_TOP_K,
            use_rerank=False,
        )
    except Exception as e:
        _cost_err = time.time() - _total_start
        log_rag_request(user_id=user_id, question=user_query, hit_count=0,
                        cost_sec=_cost_err, tag=tag_filter or "", success=False)
        return {
            "success": False,
            "error": f"向量检索异常：{str(e)}",
            "answer": "服务暂时无法完成检索，请稍后重试",
            "reference": [],
        }
    print(f"[rag_chat] ① 向量召回耗时 {time.time() - _t0:.2f}s，命中 {len(raw_hits)} 条")

    # 2. Rerank 重排序（语义相关性过滤）
    _t0 = time.time()
    try:
        rerank_util = RerankUtil()
        rerank_hits = rerank_util.rerank(
            query=user_query,
            hits=raw_hits,
            top_n=settings.RAG_RERANK_TOP_N,
        )
    except Exception as e:
        # 重排失败不阻断：退化使用原始 hits
        rerank_hits = raw_hits[: settings.RAG_RERANK_TOP_N]
    print(f"[rag_chat] ② Rerank 重排耗时 {time.time() - _t0:.2f}s，保留 {len(rerank_hits)} 条")

    # 3. Token 截断，避免超出模型上下文窗口
    _t0 = time.time()
    final_hits = truncate_context(
        rerank_hits, max_total_tokens=settings.RAG_MAX_CONTEXT_TOKEN
    )
    context_str = build_context_text(final_hits)
    prompt = RAG_PROMPT_TEMPLATE.format(
        context_content=context_str, user_query=user_query
    )
    print(f"[rag_chat] ③ Token截断耗时 {time.time() - _t0:.2f}s，最终 {len(final_hits)} 条片段")

    # ====== 短路优化：无检索结果直接返回，不调用 LLM ======
    if not final_hits:
        ref_list: List[Dict] = []
        answer_no_hit = "【未在知识库找到相关信息】\n\n参考来源：无"
        try:
            ai_msg = _save_rag_messages(
                db=db,
                session_id=session_id,
                user_query=user_query,
                answer=answer_no_hit,
                reference=ref_list,
            )
            message_id = ai_msg.id
        except Exception:
            message_id = None
        _cost = time.time() - _total_start
        log_rag_request(user_id=user_id, question=user_query, hit_count=0,
                        cost_sec=_cost, tag=tag_filter or "", success=True)
        print(f"[rag_chat] 短路返回（无命中），总耗时 {_cost:.2f}s")
        return {
            "success": True,
            "answer": answer_no_hit,
            "reference": ref_list,
            "message_id": message_id,
        }

    # 4. 调用大模型，捕获超时 / 网络异常 / 鉴权错误
    _t0 = time.time()
    answer = ""
    llm_error = None

    if client is None:
        llm_error = "LLM 客户端未初始化，请检查 LLM_API_KEY / LLM_BASE_URL 配置"
    else:
        try:
            resp = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            answer = resp.choices[0].message.content or ""
        except Exception as e:
            llm_error = f"大模型调用异常：{str(e)}"
    print(f"[rag_chat] ④ LLM调用耗时 {time.time() - _t0:.2f}s")

    # 5. 构造溯源元数据
    ref_list = [item.get("metadata", {}) for item in final_hits]

    # 兜底：无答案时返回友好提示，但仍持久化对话
    if llm_error:
        answer = "服务暂时无法获取回答，请稍后重试"

    # 6. 持久化
    _t0 = time.time()
    try:
        ai_msg = _save_rag_messages(
            db=db,
            session_id=session_id,
            user_query=user_query,
            answer=answer,
            reference=ref_list,
        )
        message_id = ai_msg.id
    except Exception:
        message_id = None
    print(f"[rag_chat] ⑤ 消息持久化耗时 {time.time() - _t0:.2f}s")

    result = {
        "success": llm_error is None,
        "answer": answer,
        "reference": ref_list,
        "message_id": message_id,
    }
    if llm_error:
        result["error"] = llm_error

    _cost = time.time() - _total_start
    log_rag_request(user_id=user_id, question=user_query, hit_count=len(final_hits),
                    cost_sec=_cost, tag=tag_filter or "", success=result.get("success", False))
    print(f"[rag_chat] ✅ 完成，总耗时 {_cost:.2f}s")
    return result