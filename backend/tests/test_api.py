"""API 契约测试（使用 FakeFastMeRAG，不依赖真实模型）."""

import pytest


# ============ 基础 & 健康 ============

def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "FastMe RAG Chatbot Demo"


def test_healthz(client, fake_rag):
    fake_rag._count = 7
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["vector_count"] == 7
    assert body["llm_reachable"] is False  # 桩 base_url 为空


# ============ 场景 ============

def test_list_scenes(client):
    r = client.get("/api/scenes")
    assert r.status_code == 200
    names = [s["name"] for s in r.json()]
    assert "default" in names and "manual_query" in names


# ============ 会话 ============

def test_sessions_lifecycle(client):
    # 创建会话 / create
    r = client.post("/api/sessions", json={"id": "s1"})
    assert r.status_code == 200
    assert r.json()["id"] == "s1"

    # 列表 / list
    r = client.get("/api/sessions")
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()["sessions"]]
    assert "s1" in ids

    # 删除 / delete
    r = client.delete("/api/sessions/s1")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    r = client.get("/api/sessions")
    assert all(s["id"] != "s1" for s in r.json()["sessions"])


# ============ 入库 ============

def test_ingest_success(client):
    r = client.post(
        "/api/ingest",
        files={"file": ("手册.txt", "设备操作步骤如下：\n1. 开机\n2. 检测".encode("utf-8"), "text/plain")},
        data={"doc_type": "manual"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["doc_type"] == "manual"
    assert body["chunks_count"] == 3


def test_ingest_rejects_bad_doc_type(client):
    r = client.post(
        "/api/ingest",
        files={"file": ("a.txt", b"x", "text/plain")},
        data={"doc_type": "unsupported"},
    )
    assert r.status_code == 422


def test_ingest_rejects_bad_extension(client):
    r = client.post(
        "/api/ingest",
        files={"file": ("a.exe", b"x", "application/octet-stream")},
        data={"doc_type": "manual"},
    )
    assert r.status_code == 422


# ============ 同步对话 ============

def test_chat_without_session(client):
    r = client.post("/api/chat", json={"question": "你好", "scene": "manual_query"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "你好"
    assert "sources" in body


def test_chat_with_session_uses_memory(client):
    r = client.post("/api/chat", json={"question": "第一问", "session_id": "sess_x"})
    assert r.status_code == 200
    assert r.json()["answer"].startswith("[memory]")
    # 再次提问应能读到历史（桩子把问题记入记忆）
    r2 = client.post("/api/chat", json={"question": "第一问", "session_id": "sess_x"})
    assert r2.status_code == 200
    # session 消息计数应递增
    sess = client.get("/api/sessions").json()["sessions"]
    target = [s for s in sess if s["id"] == "sess_x"][0]
    assert target["message_count"] == 2


# ============ 流式对话 (SSE) ============

def test_chat_stream(client):
    r = client.post("/api/chat/stream", json={"question": "你好", "scene": "default"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    body = r.text
    assert "event: meta" in body
    assert "event: delta" in body
    assert "event: done" in body
    # 收集的文本应拼成序列
    import json
    deltas = "".join(
        json.loads(line.replace("data: ", ""))
        for line in body.splitlines()
        if line.startswith("data: ") and _frame_is_delta(body, line)
    )
    assert deltas  # 至少非空


def _frame_is_delta(whole, line):
    # 简略判断：该 data 行的上一条 event 行是 delta
    lines = whole.splitlines()
    idx = lines.index(line)
    return idx >= 1 and lines[idx - 1].startswith("event: delta")


def test_chat_stream_with_session_ok(client):
    r = client.post("/api/chat/stream", json={"question": "流式", "session_id": "ss1"})
    assert r.status_code == 200
    assert "event: done" in r.text