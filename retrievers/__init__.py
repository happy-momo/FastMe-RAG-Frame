"""
检索器模块 - 场景化检索器
Retriever Module - Scene-Aware Retrievers

提供场景感知的检索器实现，将 SceneRouter 与 BaseRetriever 结合。
Provides scene-aware retriever implementations that combine SceneRouter with BaseRetriever.

可用检索器:
Available retrievers:
- SceneAwareRetriever: 场景感知检索器（包装 BaseRetriever）
  SceneAwareRetriever: Scene-aware retriever (wraps BaseRetriever)
- RetrieverFactory: 检索器工厂（根据配置创建检索器）
  RetrieverFactory: Retriever factory (creates retrievers based on configuration)

Example:
    >>> from retrievers import SceneAwareRetriever, RetrieverFactory
    >>> from routers import SceneRouter
    >>> from vector_stores import ChromaAdapter
    >>> from vector_stores.chroma_retriever import ChromaRetriever
    >>>
    >>> # 创建基础检索器
    >>> chroma_adapter = ChromaAdapter(...)
    >>> base_retriever = ChromaRetriever(chroma_adapter)
    >>>
    >>> # 包装为场景感知检索器
    >>> scene_router = SceneRouter()
    >>> scene_aware = SceneAwareRetriever(base_retriever, scene_router)
    >>>
    >>> # 执行场景化检索
    >>> results, source_fields = scene_aware.retrieve(
    ...     question="设备报警怎么处理？",
    ...     scene="fault_diagnosis",
    ...     filters={"device_id": "EQ001"}
    ... )
"""

from retrievers.scene_aware import SceneAwareRetriever
from retrievers.factory import RetrieverFactory

__all__ = [
    "SceneAwareRetriever",
    "RetrieverFactory",
]
