"""
场景感知检索器
Scene-Aware Retriever

将 BaseRetriever 与 SceneRouter 结合，实现场景化检索能力。
Combines BaseRetriever with SceneRouter to enable scene-aware retrieval.
"""

from typing import List, Dict, Any, Optional, Tuple

from core.retriever import BaseRetriever
from core.models import FastMeSearchResult
from routers.scene_router import SceneRouter


class SceneAwareRetriever:
    """
    场景感知检索器
    Scene-Aware Retriever

    包装 BaseRetriever，添加场景化能力：
    Wraps BaseRetriever with scene-aware capabilities:
    - 自动应用场景配置（top_k, source_fields）
      Automatically applies scene config (top_k, source_fields)
    - 自动构建场景过滤条件
      Automatically builds scene filter conditions
    - 统一返回格式
      Unified return format

    Args:
        retriever: BaseRetriever 实例（Chroma/FAISS/Qdrant 等） / BaseRetriever instance (Chroma/FAISS/Qdrant etc.)
        scene_router: SceneRouter 实例 / SceneRouter instance

    Example:
        >>> from vector_stores.chroma_retriever import ChromaRetriever
        >>> from routers import SceneRouter
        >>>
        >>> chroma_retriever = ChromaRetriever(chroma_adapter)
        >>> scene_router = SceneRouter()
        >>> scene_aware = SceneAwareRetriever(chroma_retriever, scene_router)
        >>>
        >>> results, source_fields = scene_aware.retrieve(
        ...     question="设备报警怎么处理？",
        ...     scene="fault_diagnosis",
        ...     filters={"device_id": "EQ001"}
        ... )
    """

    def __init__(self, retriever: BaseRetriever, scene_router: SceneRouter):
        self.retriever = retriever
        self.scene_router = scene_router

    def retrieve(
        self,
        question: str,
        scene: str = "default",
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> Tuple[List[FastMeSearchResult], List[str]]:
        """
        场景化检索
        Scene-aware retrieval

        Args:
            question: 用户问题 / User question
            scene: 场景名称 / Scene name
            filters: 用户过滤条件（字典格式，会转换为 $eq） / User filter conditions (dict format, will be converted to $eq)
            top_k: 召回数量，默认使用场景配置 / Number of results, defaults to scene config

        Returns:
            (检索结果列表，场景配置字段列表) / (List of search results, list of scene config fields)

        Example:
            >>> results, source_fields = scene_aware.retrieve(
            ...     question="E001 设备有什么故障？",
            ...     scene="fault_diagnosis",
            ...     filters={"device_id": "EQ001"}
            ... )
        """
        # 1. 获取场景配置
        scene_config = self.scene_router.route(scene)
        final_top_k = top_k if top_k is not None else scene_config.get("top_k", 5)
        source_fields = scene_config.get("source_fields", [])

        # 2. 构建过滤条件（直接获取 FilterCondition 列表）
        filter_conditions = self.scene_router.build_filter(
            scene=scene,
            user_filter=filters
        )

        # 3. 执行检索
        results = self.retriever.retrieve(
            query=question,
            top_k=final_top_k,
            filters=filter_conditions
        )

        return results, source_fields
