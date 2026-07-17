"""
Chroma 向量库适配器
Chroma Vector Store Adapter

封装 Chroma 向量库的操作，提供统一的接口。
Wraps Chroma vector store operations, providing a unified interface.

Classes:
    ChromaAdapter: Chroma 向量库适配器 / Chroma vector store adapter

Features:
    - 支持元数据过滤 / Supports metadata filtering
    - 支持持久化到磁盘 / Supports persistence to disk
    - 支持内存清理（重建连接） / Supports memory cleanup (connection rebuild)
    - 自动元数据清洗 / Automatic metadata sanitization

Example:
    >>> from vector_stores.chroma import ChromaAdapter
    >>> from langchain_huggingface import HuggingFaceEmbeddings
    >>>
    >>> embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    >>> adapter = ChromaAdapter(
    ...     collection_name="fastme_rag",
    ...     persist_directory="./data/chroma",
    ...     embedding_function=embeddings
    ... )
    >>>
    >>> # 添加文档
    >>> from langchain_core.documents import Document
    >>> docs = [Document(page_content="测试内容", metadata={"source": "test.txt"})]
    >>> adapter.add_documents(docs, ids=["test_1"])
    >>>
    >>> # 搜索
    >>> results = adapter.similarity_search_with_score("测试查询", k=5)
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document

from vector_stores.base import VectorStoreAdapter

# 框架日志配置
logger = logging.getLogger("fastme_rag")


class ChromaAdapter(VectorStoreAdapter):
    """
    Chroma 向量库适配器
    Chroma Vector Store Adapter

    封装 Chroma 向量库的操作，实现 VectorStoreAdapter 接口。
    Wraps Chroma vector store operations, implementing the VectorStoreAdapter interface.

    特性：
    Features:
    - 支持元数据过滤 / Supports metadata filtering
    - 支持持久化到磁盘（自动 + 手动） / Supports persistence to disk (automatic + manual)
    - 支持内存清理（重建连接） / Supports memory cleanup (connection rebuild)
    - 自动清洗元数据（只保留 str/int/float/bool） / Auto-sanitizes metadata (keeps only str/int/float/bool)

    Attributes:
        _chroma: Chroma 实例 / Chroma instance
        _collection_name: 集合名称 / Collection name
        _persist_directory: 持久化目录 / Persist directory
        _embedding_function: Embedding 函数 / Embedding function

    Example:
        >>> adapter = ChromaAdapter(
        ...     collection_name="my_collection",
        ...     persist_directory="./data/chroma",
        ...     embedding_function=embeddings
        ... )
        >>> adapter.add_documents(docs, ids=["1", "2"])
        >>> results = adapter.similarity_search_with_score("查询", k=5)
    """

    def __init__(
        self,
        collection_name: str,
        persist_directory: str,
        embedding_function,
    ):
        """
        初始化 Chroma 适配器
        Initialize Chroma adapter

        Args:
            collection_name: Chroma 集合名称 / Chroma collection name
            persist_directory: Chroma 数据持久化目录 / Chroma data persist directory
            embedding_function: LangChain Embedding 函数 / LangChain Embedding function

        Example:
            >>> from langchain_huggingface import HuggingFaceEmbeddings
            >>> embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
            >>> adapter = ChromaAdapter(
            ...     collection_name="fastme_rag",
            ...     persist_directory="./data/chroma",
            ...     embedding_function=embeddings
            ... )
        """
        self._collection_name = collection_name
        self._persist_directory = persist_directory
        self._embedding_function = embedding_function

        # 创建 Chroma 实例
        self._chroma = self._create_chroma_instance()

        logger.info(f"[ChromaAdapter] 初始化完成：collection={collection_name}, dir={persist_directory}")

    def _create_chroma_instance(self) -> Chroma:
        """
        创建 Chroma 实例的内部方法
        Internal method to create a Chroma instance

        Returns:
            新的 Chroma 实例 / New Chroma instance
        """
        return Chroma(
            collection_name=self._collection_name,
            persist_directory=self._persist_directory,
            embedding_function=self._embedding_function
        )

    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        添加文档到 Chroma
        Add documents to Chroma

        Args:
            documents: 文档列表 / Document list
            ids: 可选的文档 ID 列表 / Optional document ID list

        Note:
            会自动清洗元数据，只保留 str/int/float/bool 类型
            Automatically sanitizes metadata, keeping only str/int/float/bool types
        """
        # 清洗元数据（Chroma 要求）
        clean_docs = []
        for doc in documents:
            clean_metadata = self.sanitize_metadata(doc.metadata)
            clean_docs.append(Document(
                page_content=doc.page_content,
                metadata=clean_metadata
            ))

        # 添加到 Chroma
        if ids:
            self._chroma.add_documents(documents=clean_docs, ids=ids)
        else:
            self._chroma.add_documents(documents=clean_docs)

        logger.debug(f"[ChromaAdapter] 添加 {len(clean_docs)} 个文档")

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        带分数的相似度搜索
        Similarity search with scores

        Args:
            query: 查询文本 / Query text
            k: 返回结果数量 / Number of results to return
            filter: 元数据过滤条件 / Metadata filter conditions

        Returns:
            文档和分数的元组列表 / List of document and score tuples
        """
        results = self._chroma.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter
        )
        return results

    def get_count(self) -> int:
        """
        获取向量总数
        Get total vector count

        Returns:
            向量数量 / Number of vectors
        """
        return len(self._chroma.get()["ids"])

    def delete_collection(self) -> None:
        """
        删除集合
        Delete collection

        Note:
            删除后会重新创建空集合，以便继续使用
            After deletion, an empty collection is recreated for continued use
        """
        try:
            self._chroma.delete_collection()
            logger.info(f"[ChromaAdapter] 集合 {self._collection_name} 已删除")
        except Exception as e:
            logger.warning(f"[ChromaAdapter] 删除集合失败：{e}")

        # 重新创建空集合（使用内部方法）
        self._chroma = self._create_chroma_instance()
        logger.info(f"[ChromaAdapter] 集合 {self._collection_name} 已重新创建")

    def get_config(self) -> Dict[str, Any]:
        """
        获取配置信息
        Get configuration info

        Returns:
            配置信息字典 / Configuration info dictionary
        """
        return {
            "collection_name": self._collection_name,
            "persist_directory": self._persist_directory,
            "vector_count": self.get_count(),
            "supports_filter": True,
        }

    def persist(self) -> None:
        """
        持久化到磁盘
        Persist to disk

        Note:
            Chroma 通常会自动持久化，此方法提供手动持久化选项
            Chroma usually persists automatically; this method provides a manual persistence option
        """
        try:
            self._chroma._client.persist()
            logger.info(f"[ChromaAdapter] 已持久化到 {self._persist_directory}")
        except Exception as e:
            logger.warning(f"[ChromaAdapter] 持久化失败：{e}")

    def reset_for_memory_cleanup(self) -> 'ChromaAdapter':
        """
        重建连接以释放内存
        Rebuild connection to release memory

        Chroma 的 HNSW 索引在内存中累积，此方法会：
        Chroma's HNSW index accumulates in memory; this method will:
        1. 持久化当前数据到磁盘
           Persist current data to disk
        2. 在当前实例上重建 Chroma 连接（释放旧的内存索引）
           Rebuild Chroma connection on current instance (releasing old in-memory index)
        3. 执行垃圾回收
           Run garbage collection

        Returns:
            self（原地更新，保持所有外部引用有效）/ self (updated in-place, keeping all external references valid)

        Note:
            原地替换 _chroma 内部对象，而非返回新实例。
            Replaces _chroma internal object in-place instead of returning a new instance.
            这确保所有持有当前适配器引用的组件（如 ChromaRetriever）自动使用更新后的连接，
            This ensures all components holding a reference to this adapter (e.g. ChromaRetriever)
            automatically use the updated connection,
            避免引用不同步导致的内存泄漏和数据不一致。
            avoiding memory leaks and data inconsistency from reference desynchronization.

        Example:
            >>> # 批量入库时定期清理内存
            >>> for i, file in enumerate(files):
            ...     adapter.add_documents(...)
            ...     if i % 10 == 0:
            ...         adapter.reset_for_memory_cleanup()
        """
        import gc

        logger.info(f"[ChromaAdapter] 重建连接以释放内存...")

        # 1. 持久化当前数据
        self.persist()

        # 2. 原地替换 Chroma 实例（释放旧的内存索引）
        self._chroma = self._create_chroma_instance()

        # 3. 清理 Python 垃圾
        gc.collect()

        logger.info(f"[ChromaAdapter] 连接已重建，内存已释放")
        return self

    def supports_filter(self) -> bool:
        """
        Chroma 支持元数据过滤
        Chroma supports metadata filtering

        Returns:
            始终返回 True / Always returns True
        """
        return True
