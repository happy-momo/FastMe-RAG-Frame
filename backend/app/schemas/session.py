"""会话管理数据契约 / Session management data contracts."""

from datetime import datetime
from typing import List
import time

from pydantic import BaseModel, Field


class SessionInfo(BaseModel):
    id: str
    message_count: int = 0
    created_at: str = Field(default_factory=lambda: str(int(time.time() * 1000)))


class SessionCreate(BaseModel):
    id: str = Field(..., min_length=1)


class SessionList(BaseModel):
    sessions: List[SessionInfo] = Field(default_factory=list)


class SessionMessage(BaseModel):
    """单条历史消息 / Single historical message."""
    role: str  # "user" | "assistant"
    content: str


class SessionMessageList(BaseModel):
    """会话历史消息列表 / Session message history."""
    session_id: str
    messages: List[SessionMessage] = Field(default_factory=list)