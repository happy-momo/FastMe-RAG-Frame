"""会话内存注册表 / In-memory session registry.

框架的对话记忆本身存于内存；后端维护一份轻量注册表（会话 id + 消息计数 +
创建时间）供前端列出 / 切换会话。两者生命周期一致：进程重启即全部清空。
The framework's conversation memory itself lives in memory; the backend keeps a
lightweight registry (session id + message count + created time) so the frontend
can list / switch sessions. Both share a life cycle: everything resets on restart.
"""

import time
from typing import Dict, Optional


class SessionStore:
    """后端侧会话元数据注册表 / Backend-side session metadata registry."""

    def __init__(self) -> None:
        self._sessions: Dict[str, dict] = {}

    def create(self, session_id: str) -> dict:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "id": session_id,
                "message_count": 0,
                "created_at": str(int(time.time() * 1000)),
            }
        return self._sessions[session_id]

    def record_message(self, session_id: str) -> dict:
        sess = self._sessions.setdefault(session_id, self.create(session_id))
        sess["message_count"] += 1
        return sess

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def list(self) -> list:
        return list(self._sessions.values())

    def get(self, session_id: str) -> Optional[dict]:
        return self._sessions.get(session_id)


# 全局单例 / Global singleton
session_store = SessionStore()