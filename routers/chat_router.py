from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from deps import get_db, get_current_user
from models.user_model import User
from schemas.chat_schema import (
    SessionCreate, MessageOut, MessageCreate,
    RAGMessageCreate,
)
from service import chat_service
from service import rag_service
from service import doc_service
from utils.response import ApiResponse

router = APIRouter(prefix="/api/chat", tags=["会话模块"])

# 新建会话
@router.post("/session")
def create_session(
    req: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sess = chat_service.create_chat_session(db, current_user.id, req.session_name)
    return ApiResponse.success(
        data={
            "session_id": sess.id,
            "session_name": sess.title,
            "create_time": str(sess.create_time),
            "update_time": str(sess.update_time),
        },
        msg="创建会话成功",
    )

# 获取我的会话列表
@router.get("/session")
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = chat_service.get_user_session_list(db, current_user.id)
    data = [
        {
            "session_id": s.id,
            "session_name": s.title,
            "create_time": str(s.create_time),
            "update_time": str(s.update_time),
        }
        for s in sessions
    ]
    return ApiResponse.success(data=data, msg="获取会话列表成功")

# 删除会话
@router.delete("/session/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sess = chat_service.get_session_by_id(db, session_id)
    if not sess or sess.user_id != current_user.id:
        return ApiResponse.error(msg="会话不存在或无权限", code=404)
    chat_service.delete_session(db, session_id)
    return ApiResponse.success(msg="删除成功")

# 获取会话历史消息
@router.get("/session/{session_id}/messages")
def list_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sess = chat_service.get_session_by_id(db, session_id)
    if not sess or sess.user_id != current_user.id:
        return ApiResponse.error(msg="会话不存在或无权限", code=404)
    msgs = chat_service.get_messages_by_session_id(db, session_id)
    data = [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "extra_json": m.extra_json,
            "create_time": str(m.create_time),
        }
        for m in msgs
    ]
    return ApiResponse.success(data=data, msg="获取历史消息成功")

# 发送一条消息（Day4：接入 Chroma 向量检索 + 简单拼接回复）
@router.post("/session/{session_id}/message", response_model=MessageOut)
def send_message(
    session_id: int,
    req: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = chat_service.get_session_by_id(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="会话不存在或无权限")

    # 保存用户消息
    user_msg = chat_service.add_chat_message(db, session_id, "user", req.content)

    # Day4：向量检索 + 拼接回复（保留原逻辑用于对比 / 调试）
    hits = rag_service.retrieve_by_tag(
        query=req.content,
        tag=None,
        top_k=3,
    )

    if hits:
        context_parts = []
        for h in hits:
            context_parts.append(f"[{h['metadata'].get('filename','?')}] {h['document']}")
        context = "\n\n".join(context_parts)
        reply_content = f"【检索到 {len(hits)} 条相关片段】\n{context}\n\n（Day5 将接入 LLM 生成自然语言回复）"
    else:
        reply_content = "（未检索到相关文档片段，Day5 将接入 LLM 生成回复）"

    assistant_msg = chat_service.add_chat_message(db, session_id, "assistant", reply_content)
    return assistant_msg


# ========== Day5：完整 RAG 问答接口（Day6 统一响应 + 中间件鉴权） ==========
@router.post("/session/{session_id}/rag")
def send_rag_message(
    session_id: int,
    req: RAGMessageCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    完整 RAG 问答：向量召回 → Rerank 重排 → Token 截断 → LLM 生成 → 消息持久化
    全局鉴权中间件已处理 Token 校验，从 request.state 取 user_id
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="未授权")

    # 校验会话归属
    session = chat_service.get_session_by_id(db, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404, detail="会话不存在或无权限")

    result = chat_service.rag_chat(
        db=db,
        user_query=req.question,
        tag_filter=req.tag,
        session_id=session_id,
        user_id=user_id,
        retrieve_mode=req.retrieve_mode or "hybrid",
        use_rerank=req.use_rerank if req.use_rerank is not None else True,
    )
    if result.get("success"):
        return ApiResponse.success(data=result, msg="问答成功")
    return ApiResponse.error(
        msg=result.get("error", "问答失败"),
        code=500,
        data=result,
    )