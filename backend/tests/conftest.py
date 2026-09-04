"""后端测试夹具 / Backend test fixtures.

核心思路：不依赖真实 LLM / embedding 模型。用一个 FakeFastMeRAG 桩替换框架，
注入到 RAGManager 单例，从而在无模型环境下验证全部 API 契约。
Idea: no real LLM / embedding needed. A FakeFastMeRAG stub replaces the framework,
injected into the RAGManager singleton, so the full API contract is tested
without any model.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.rag import RAGManager
import app.core.rag as rag_module
import app.core.streaming as streaming_module


class _FakeStreamChunk:
    def __init__(self, text: str):
        self.content = text


class FakeFastMeRAG:
    """模拟框架最小接口 / Minimal fake of the framework interface."""

    scenes = {
        "default": {"description": "默认问答", "top_k": 5, "prompt_template": "default", "source_fields": ["chunk_id"]},
        "manual_query": {"description": "手册查询", "top_k": 5, "prompt_template": "default", "source_fields": ["chunk_id"]},
    }

    def __init__(self):
        self.memories = {}
        self._count = 0

    # ---- manager.rag 依赖 ----
    @property
    def scene_router(self):
        return _FakeSceneRouter(self.scenes)

    @property
    def config(self):
        return {"llm": {"base_url": "", "api_key": None}}

    def get_scenes(self):
        return list(self.scenes.keys())

    def get_vector_count(self):
        return self._count

    def ingest(self, file_path, doc_type, extra_metadata=None):
        self._count += 1
        return {
            "status": "success",
            "doc_id": "doc_1",
            "file_name": "test.txt",
            "doc_type": doc_type,
            "chunks_count": 3,
            "vector_count": self._count,
        }

    def chat_with_memory(self, question, session_id, scene="default", filters=None, top_k=None):
        self.memories.setdefault(session_id, []).append(question)
        return {"question": question, "scene": scene, "answer": f"[memory] {question}", "sources": []}

    def chat(self, question, scene="default", filters=None, top_k=None):
        return {"question": question, "scene": scene, "answer": question, "sources": []}

    # ---- manager.chat_with_memory / session 依赖 ----
    def get_memory(self, session_id):
        return _FakeMemory(self.memories, session_id)

    def create_memory(self, session_id):
        self.memories.setdefault(session_id, [])

    def clear_memory(self, session_id=None):
        if session_id is None:
            self.memories.clear()
        else:
            self.memories.pop(session_id, None)

    # ---- streaming 依赖 ----
    @property
    def scene_aware_retriever(self):
        return _FakeRetriever()

    @property
    def prompt_adapter(self):
        return _FakePromptAdapter()

    @property
    def llm(self):
        return _FakeLLM()


class _FakeSceneRouter:
    def __init__(self, scenes):
        self.scene_config = scenes

    def route(self, scene):
        return self.scene_config.get(scene, self.scene_config.get("default", {}))


class _FakeMemory:
    def __init__(self, store, session_id):
        self._store, self._id = store, session_id

    def load_memory_variables(self, _):
        from langchain_core.messages import HumanMessage, AIMessage
        items = self._store.get(self._id, [])
        history = []
        for q in items:
            history.append(HumanMessage(content=q))
            history.append(AIMessage(content=f"回答：{q}"))
        return {"history": history}

    def save_context(self, inputs, outputs):
        q = inputs.get("input")
        if q not in self._store.get(self._id, []):
            self._store.setdefault(self._id, []).append(q)


class _FakeRetriever:
    def retrieve(self, question, scene="default", filters=None, top_k=None):
        from core.models import FastMeSearchResult
        contexts = [
            FastMeSearchResult(
                chunk_id="chunk_1", doc_id="doc_1", doc_type="manual", text="手册内容A",
                score=0.9, metadata={"chunk_id": "chunk_1"},
            )
        ]
        return contexts, ["chunk_id"]


class _FakePromptAdapter:
    def _format_context(self, contexts, source_fields=None):
        return "FORMATTED_CONTEXT"

    def get_system_prompt(self, name):
        return "system-prompt"


class _FakeLLM:
    def stream(self, messages):
        for part in ["你", "好", "，", "世界"]:
            yield _FakeStreamChunk(part)


@pytest.fixture
def fake_rag(monkeypatch):
    """重置单例并注入 FakeFastMeRAG。"""
    fake = FakeFastMeRAG()
    RAGManager._instance = None
    monkeypatch.setattr(rag_module, "FastMeRAG", lambda: fake)
    return fake


@pytest.fixture
def client(fake_rag):
    from app.main import app
    yield TestClient(app)
    # 清理单例避免跨用例污染 / Reset singleton between tests
    RAGManager._instance = None
    streaming_module.RAGManager._instance = None