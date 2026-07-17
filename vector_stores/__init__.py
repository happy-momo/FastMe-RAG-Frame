"""
向量库模块
Vector Stores Module

提供多种向量数据库的适配器实现，支持 Chroma、FAISS 等。
Provides adapter implementations for multiple vector databases, supporting Chroma, FAISS, etc.

可用组件：
Available components:
- VectorStoreAdapter: 抽象基类（定义接口）
  Abstract base class (defines interface)
- ChromaAdapter: Chroma 向量库适配器
  Chroma vector store adapter
- FAISSAdapter: FAISS 向量库适配器
  FAISS vector store adapter
- VectorStoreFactory: 向量库工厂
  Vector store factory
- ChromaRetriever: Chroma 检索器（实现 BaseRetriever）
  Chroma retriever (implements BaseRetriever)
- FAISSRetriever: FAISS 检索器（实现 BaseRetriever）
  FAISS retriever (implements BaseRetriever)

Example:
    >>> from vector_stores import ChromaAdapter, FAISSAdapter, VectorStoreFactory
    >>> from vector_stores.chroma_retriever import ChromaRetriever
    >>> from vector_stores.faiss_retriever import FAISSRetriever
    >>>
    >>> # 使用工厂创建 Chroma 适配器
    >>> adapter = VectorStoreFactory.create(
    ...     vector_store_type="chroma",
    ...     embeddings=embeddings,
    ...     vector_store_config={
    ...         "collection_name": "my_collection",
    ...         "persist_directory": "./data/chroma"
    ...     }
    ... )
    >>> retriever = ChromaRetriever(adapter)
    >>>
    >>> # 使用 FAISS
    >>> adapter = FAISSAdapter(
    ...     embedding_function=embeddings,
    ...     index_path="./data/faiss_index"
    ... )
    >>> retriever = FAISSRetriever(adapter)
"""

from vector_stores.base import VectorStoreAdapter
from vector_stores.chroma import ChromaAdapter
from vector_stores.faiss import FAISSAdapter
from vector_stores.factory import VectorStoreFactory

__all__ = [
    "VectorStoreAdapter",
    "ChromaAdapter",
    "FAISSAdapter",
    "VectorStoreFactory",
]
