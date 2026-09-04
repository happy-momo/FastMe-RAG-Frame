"""聊天相关数据契约 / Chat-related data contracts."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="用户问题")
    scene: str = Field("default", description="场景名称，如 fault_diagnosis / manual_query")
    session_id: Optional[str] = Field(None, description="会话 ID，提供则使用带记忆对话")
    filters: Optional[Dict[str, Any]] = Field(None, description="元数据过滤条件")
    top_k: Optional[int] = Field(None, ge=1, le=50, description="召回数量")


class ChatResponse(BaseModel):
    question: str
    scene: str
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)