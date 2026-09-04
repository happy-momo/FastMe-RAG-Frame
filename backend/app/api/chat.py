"""聊天 API / Chat API.

提供：
- POST /api/chat          同步问答（支持记忆）
- POST /api/chat/stream   SSE 流式问答（支持记忆）
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.core.rag import RAGManager
from app.core.sessions import session_store
from app.core.streaming import SseFrame, stream_chat
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger("fastme_rag_demo")
router = APIRouter(prefix="/api/chat", tags=["chat"])


def _run_chat(req: ChatRequest) -> dict:
    """执行同步对话（在事件循环线程池中运行）。"""
    manager = RAGManager()
    if req.session_id:
        if not manager.session_exists(req.session_id):
            manager.create_session(req.session_id)
        result = manager.chat_with_memory(
            question=req.question,
            session_id=req.session_id,
            scene=req.scene,
            filters=req.filters,
            top_k=req.top_k,
        )
        session_store.record_message(req.session_id)
    else:
        result = manager.chat(req.question, scene=req.scene, filters=req.filters, top_k=req.top_k)
    return result


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> dict:
    try:
        return await run_in_threadpool(_run_chat, req)
    except Exception as e:
        logger.exception("同步对话失败")
        raise  # 交由全局异常处理器返回 JSON


def _sse_serializer(frame: SseFrame) -> str:
    """将 SseFrame 序列化为 SSE 文本 / Serialize a SseFrame to SSE text."""
    payload = json.dumps(frame.data, ensure_ascii=False)
    return f"event: {frame.event}\ndata: {payload}\n\n"


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    """流式问答，返回 text/event-stream。"""

    manager = RAGManager()

    def event_source():
        # 串行化：流式期间持有操作锁，避免与入库/其它操作竞态
        manager._op_lock.acquire()
        try:
            for frame in stream_chat(
                manager,
                question=req.question,
                scene=req.scene,
                session_id=req.session_id,
                filters=req.filters,
                top_k=req.top_k,
            ):
                yield _sse_serializer(frame)
        finally:
            manager._op_lock.release()
            if req.session_id:
                session_store.record_message(req.session_id)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 关闭代理缓冲，保证实时 / disable proxy buffering
        },
    )