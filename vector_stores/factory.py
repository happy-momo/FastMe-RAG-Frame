"""
向量库工厂模块
Vector Store Factory Module

根据配置创建对应的向量库适配器实例。
Creates corresponding vector store adapter instances based on configuration.

支持的向量库：
Supported vector stores:
- chroma: Chroma 向量库 / Chroma vector store
- faiss: FAISS 向量库 / FAISS vector store

Example:
    >>> from vector_stores.factory import VectorStoreFactory
    >>> from langchain_huggingface import HuggingFaceEmbeddings
    >>>
    >>> embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    >>> adapter = VectorStoreFactory.create(
    ...     vector_store_type="chroma",
    ...     embeddings=embeddings,
    ...     vector_store_config={
    ...         "collection_name": "fastme_rag",
    ...         "persist_directory": "./data/chroma"
    ...     }
    ... )
"""

import logging
from typing import Dict, Any

from langchain_core.embeddings import Embeddings

from vector_stores.base import VectorStoreAdapter
from vector_stores.chroma import ChromaAdapter
from vector_stores.faiss import FAISSAdapter

logger = logging.getLogger("fastme_rag")


class VectorStoreFactory:
    """
    向量库工厂类
    Vector Store Factory Class

    根据 vector_store_type 创建对应的向量库适配器实例。
    Creates corresponding vector store adapter instances based on vector_store_type.

    Example:
        >>> adapter = VectorStoreFactory.create("chroma", embeddings, config)
    """

    @staticmethod
    def create(
        vector_store_type: str,
        embeddings: Embeddings,
        vector_store_config: Dict[str, Any]
    ) -> VectorStoreAdapter:
        """
        创建向量库适配器
        Create a vector store adapter

        Args:
            vector_store_type: 向量库类型 ("chroma", "faiss") / Vector store type ("chroma", "faiss")
            embeddings: Embedding 函数实例 / Embedding function instance
            vector_store_config: 向量库特定配置 / Vector store specific configuration

        Returns:
            VectorStoreAdapter 实例 / VectorStoreAdapter instance

        Raises:
            ValueError: 当不支持该向量库类型时 / When the vector store type is not supported

        Example:
            >>> # Chroma
            >>> adapter = VectorStoreFactory.create(
            ...     "chroma",
            ...     embeddings,
            ...     {
            ...         "collection_name": "fastme_rag",
            ...         "persist_directory": "./data/chroma"
            ...     }
            ... )

            >>> # FAISS
            >>> adapter = VectorStoreFactory.create(
            ...     "faiss",
            ...     embeddings,
            ...     {"index_path": "./data/faiss_index"}
            ... )
        """
        if vector_store_type == "chroma":
            logger.info(f"[VectorStoreFactory] 创建 Chroma 适配器")
            return ChromaAdapter(
                collection_name=vector_store_config.get("collection_name", "fastme_rag"),
                persist_directory=vector_store_config.get("persist_directory", "./data/chroma"),
                embedding_function=embeddings
            )

        elif vector_store_type == "faiss":
            logger.info(f"[VectorStoreFactory] 创建 FAISS 适配器")
            return FAISSAdapter(
                embedding_function=embeddings,
                index_path=vector_store_config.get("index_path", "./data/faiss_index")
            )

        else:
            raise ValueError(
                f"Unsupported vector store type: {vector_store_type}. "
                f"Supported types: chroma, faiss"
            )
