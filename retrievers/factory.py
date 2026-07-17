"""
检索器工厂
Retriever Factory

根据配置创建对应的检索器实例。
Creates corresponding retriever instances based on configuration.
"""

import logging
from typing import Optional, Dict, Any

from core.retriever import BaseRetriever
from routers.scene_router import SceneRouter
from vector_stores.base import VectorStoreAdapter

logger = logging.getLogger("fastme_rag")


class RetrieverFactory:
    """
    检索器工厂
    Retriever Factory

    根据 vector_store_type 创建对应的检索器实例。
    Creates corresponding retriever instances based on vector_store_type.

    支持的向量库类型：
    Supported vector store types:
    - chroma: Chroma 向量库 / Chroma vector store
    - faiss: FAISS 向量库 / FAISS vector store

    Example:
        >>> from retrievers import RetrieverFactory
        >>> from routers import SceneRouter
        >>> from vector_stores import ChromaAdapter
        >>>
        >>> # 创建向量库适配器
        >>> adapter = ChromaAdapter(...)
        >>>
        >>> # 创建检索器
        >>> retriever = RetrieverFactory.create(
        ...     vector_store_type="chroma",
        ...     vector_store_adapter=adapter,
        ...     scene_router=SceneRouter()
        ... )
    """

    @staticmethod
    def create(
        vector_store_type: str,
        vector_store_adapter: VectorStoreAdapter,
        scene_router: SceneRouter,
        retriever_config: Optional[Dict[str, Any]] = None
    ) -> BaseRetriever:
        """
        创建检索器
        Create retriever

        Args:
            vector_store_type: 向量库类型 / Vector store type ("chroma", "faiss", ...)
            vector_store_adapter: VectorStoreAdapter 实例 / VectorStoreAdapter instance
            scene_router: SceneRouter 实例 / SceneRouter instance
            retriever_config: 检索器额外配置（可选） / Additional retriever config (optional)

        Returns:
            BaseRetriever 实例 / BaseRetriever instance

        Raises:
            ValueError: 当不支持该向量库类型时 / When the vector store type is not supported
        """
        retriever_config = retriever_config or {}

        if vector_store_type == "chroma":
            from vector_stores.chroma_retriever import ChromaRetriever
            base_retriever = ChromaRetriever(vector_store_adapter)
            logger.info(f"[RetrieverFactory] 创建 ChromaRetriever")

        elif vector_store_type == "faiss":
            from vector_stores.faiss_retriever import FAISSRetriever
            post_filter_multiplier = retriever_config.get("post_filter_multiplier", 5)
            base_retriever = FAISSRetriever(
                vector_store_adapter,
                post_filter_multiplier=post_filter_multiplier
            )
            logger.info(f"[RetrieverFactory] 创建 FAISSRetriever (post_filter_multiplier={post_filter_multiplier})")

        else:
            raise ValueError(
                f"Unsupported vector store type: {vector_store_type}. "
                f"Supported types: chroma, faiss"
            )

        # 包装为场景感知检索器
        from retrievers.scene_aware import SceneAwareRetriever
        scene_aware_retriever = SceneAwareRetriever(base_retriever, scene_router)

        logger.info(f"[RetrieverFactory] 创建 SceneAwareRetriever (type={vector_store_type})")
        return scene_aware_retriever
