"""纯逻辑单元测试：schema 校验、SSE 序列化、对话工厂。"""

import pytest

from pydantic import ValidationError

from app.schemas.chat import ChatRequest
from app.core.streaming import SseFrame
from app.api.chat import _sse_serializer
from app.api.ingest import _parse_extra_metadata


def test_chat_request_requires_question():
    with pytest.raises(ValidationError):
        ChatRequest(question="")


def test_chat_request_defaults():
    req = ChatRequest(question="hi")
    assert req.scene == "default"
    assert req.session_id is None
    assert req.top_k is None


def test_chat_request_top_k_bounds():
    with pytest.raises(ValidationError):
        ChatRequest(question="hi", top_k=999)


def test_parse_extra_metadata_valid():
    assert _parse_extra_metadata('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_parse_extra_metadata_none():
    assert _parse_extra_metadata(None) is None


def test_parse_extra_metadata_invalid():
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        _parse_extra_metadata("not json")


def test_sse_serializer_format():
    frame = SseFrame("delta", {"delta": "你"})
    out = _sse_serializer(frame)
    assert out.startswith("event: delta\n")
    assert '"你"' in out
    assert out.endswith("\n\n")
    out = _sse_serializer(SseFrame("done", {"answer": ""}))
    assert out.startswith("event: done\n")