"""会话管理 API / Session management API."""

from fastapi import APIRouter, HTTPException

from app.core.rag import RAGManager
from app.core.sessions import session_store
from app.schemas.session import SessionCreate, SessionInfo, SessionList, SessionMessageList

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=SessionList)
async def list_sessions() -> dict:
    """列出当前所有会话（含消息数/创建时间）。"""
    sessions = session_store.list()
    # 按创建时间倒序 / Sort by created time descending
    sessions.sort(key=lambda s: s["created_at"], reverse=True)
    return {"sessions": sessions}


@router.post("", response_model=SessionInfo)
async def create_session(body: SessionCreate) -> dict:
    """创建一个新会话。"""
    manager = RAGManager()
    manager.create_session(body.id)
    return session_store.create(body.id)


@router.get("/{session_id}/messages", response_model=SessionMessageList)
async def get_session_messages(session_id: str) -> dict:
    """
    获取指定会话的历史消息。
    Get historical messages for a given session.

    从框架的对话记忆中读取并转换为前端可直接渲染的格式。
    Reads from the framework's conversation memory and converts to
    a frontend-friendly format.
    """
    manager = RAGManager()
    memory = manager.rag.get_memory(session_id)
    if memory is None:
        # 会话不存在（可能还没说过话）→ 返回空列表，不报错
        # Session doesn't exist yet (no messages sent) → return empty list, not an error
        return {"session_id": session_id, "messages": []}

    try:
        raw_messages = memory.chat_memory.messages
    except AttributeError:
        return {"session_id": session_id, "messages": []}

    messages = []
    for msg in raw_messages:
        msg_type = type(msg).__name__
        if msg_type == "HumanMessage":
            role = "user"
        elif msg_type in ("AIMessage", "SystemMessage"):
            role = "assistant"
        else:
            # 其他类型跳过 / Skip other types
            continue
        messages.append({
            "role": role,
            "content": getattr(msg, "content", ""),
        })

    return {"session_id": session_id, "messages": messages}


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict:
    """删除一个会话（含框架记忆）。"""
    manager = RAGManager()
    manager.clear_session(session_id)
    session_store.delete(session_id)
    return {"ok": True, "id": session_id}
