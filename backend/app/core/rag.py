"""
RAG 实例管理器
RAG Manager

持有唯一的 FastMeRAG 实例，并对外提供线程安全（串行化）的访问。
框架本身非线程安全，demo 并发量低，这里用一把全局操作锁串行化
ingest / chat / chat_stream，保证单实例下行为一致、无竞态。

Hold the single FastMeRAG instance and provide thread-safe (serialized) access.
The framework is not thread-safe; this demo has low concurrency, so a single
operation lock serializes ingest / chat / chat_stream for consistent behavior.
"""

import json
import logging
import threading
from typing import Any, Dict, List, Optional

from app_factory import FastMeRAG

logger = logging.getLogger("fastme_rag_demo")


class RAGManager:
    """FastMeRAG 单例管理器 / FastMeRAG singleton manager."""

    _instance: Optional["RAGManager"] = None
    _init_lock = threading.Lock()

    def __new__(cls) -> "RAGManager":
        """线程安全的单例创建 / Thread-safe singleton creation."""
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # __new__ 控制实例创建，这里只初始化一次
        # The instance is created once in __new__; init guarded here.
        if getattr(self, "_initialized", False):
            return
        logger.info("初始化 FastMeRAG 单例（首次启动可能需下载 embedding 模型）...")
        self.rag: FastMeRAG = FastMeRAG()  # 从环境变量读取配置
        # 串行化所有框架操作的操作锁 / Operation lock serializing framework calls
        self._op_lock = threading.Lock()
        self._initialized = True
        logger.info("FastMeRAG 单例就绪")

    # =====================================================================
    # 线程安全包装（串行化） / Thread-safe wrappers (serialized)
    # =====================================================================

    def ingest(
        self,
        file_path: str,
        doc_type: str,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """入库单个文档 / Ingest a single document."""
        with self._op_lock:
            return self.rag.ingest(file_path, doc_type, extra_metadata=extra_metadata)

    def chat(
        self,
        question: str,
        scene: str = "default",
        filters: Optional[dict] = None,
        top_k: Optional[int] = None,
    ) -> dict:
        """同步问答 / Synchronous chat."""
        with self._op_lock:
            return self.rag.chat(question, scene=scene, filters=filters, top_k=top_k)

    def chat_stream(self, *args: Any, **kwargs: Any):
        """流式问答（生成器，持锁迭代）/ Streaming chat (generator, lock held)."""
        self._op_lock.acquire()
        try:
            for chunk in self.rag.chat_stream(*args, **kwargs):
                yield chunk
        finally:
            self._op_lock.release()

    def chat_with_memory(
        self,
        question: str,
        session_id: str,
        scene: str = "default",
        filters: Optional[dict] = None,
        top_k: Optional[int] = None,
    ) -> dict:
        """带记忆的问答 / Chat with conversation memory."""
        with self._op_lock:
            return self.rag.chat_with_memory(
                question, session_id, scene=scene, filters=filters, top_k=top_k
            )

    # =====================================================================
    # 只读查询 / Read-only queries
    # =====================================================================

    def get_scenes(self) -> List[Dict[str, Any]]:
        """返回场景列表（含描述）/ List scenes with descriptions."""
        scenes = []
        for name, cfg in self.rag.scene_router.scene_config.items():
            scenes.append({
                "name": name,
                "description": cfg.get("description", ""),
            })
        return scenes

    def get_vector_count(self) -> int:
        try:
            return self.rag.get_vector_count()
        except Exception as e:  # 向量库不可用时不至于让健康检查崩溃
            logger.warning("获取向量数量失败：%s", e)
            return 0

    def llm_reachable(self) -> bool:
        """探测 LLM 端点是否可达（轻量 /v1/models 请求）。"""
        import httpx
        base_url = self.rag.config.get("llm", {}).get("base_url", "")
        api_key = self.rag.config.get("llm", {}).get("api_key", "") or None
        if not base_url:
            return False
        url = base_url.rstrip("/") + "/models"
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        try:
            resp = httpx.get(url, headers=headers, timeout=5.0)
            return resp.status_code < 500
        except Exception:
            return False

    # =====================================================================
    # 会话管理（由后端维护的一份轻量注册表；框架记忆本身在内存中）
    # / Session management (a lightweight registry maintained in the backend;
    #   the framework memory itself lives in memory)
    # =====================================================================

    def create_session(self, session_id: str) -> None:
        self.rag.create_memory(session_id)

    def clear_session(self, session_id: str) -> None:
        self.rag.clear_memory(session_id)

    def session_exists(self, session_id: str) -> bool:
        return self.rag.get_memory(session_id) is not None