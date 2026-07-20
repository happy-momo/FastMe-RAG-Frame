"""
向量存储抽象接口
Vector Store Abstract Interface

定义向量数据库适配器的统一接口，支持多种向量库的插件化扩展。
Defines a unified interface for vector database adapters, supporting pluggable extension of multiple vector stores.

Classes:
    VectorStoreAdapter: 向量存储适配器抽象基类 / Vector store adapter abstract base class

Example:
    >>> from vector_stores.base import VectorStoreAdapter
    >>>
    >>> class MyVectorStoreAdapter(VectorStoreAdapter):
    ...     def add_documents(self, documents, ids=None):
    ...         # 实现添加文档逻辑
    ...         pass
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from langchain_core.documents import Document


class VectorStoreAdapter(ABC):
    """
    向量存储适配器抽象基类
    Vector Store Adapter Abstract Base Class

    所有向量数据库适配器必须实现此接口，以确保框架的可插拔性。
    All vector database adapters must implement this interface to ensure framework pluggability.

    实现要求：
    Required implementations:
    1. add_documents(): 添加文档到向量库
       Add documents to the vector store
    2. similarity_search_with_score(): 带分数的相似度搜索
       Similarity search with scores
    3. get_count(): 获取向量总数
       Get total vector count
    4. delete_collection(): 删除集合
       Delete the collection
    5. get_config(): 获取当前配置信息
       Get current configuration info

    可选实现：
    Optional implementations:
    - persist(): 持久化到磁盘
      Persist to disk
    - reset_for_memory_cleanup(): 重置以释放内存
      Reset to release memory

    Example:
        >>> class MyVectorStoreAdapter(VectorStoreAdapter):
        ...     def add_documents(self, documents, ids=None):
        ...         pass
        ...     def similarity_search_with_score(self, query, k=5, filter=None):
        ...         pass
        ...     def get_count(self):
        ...         pass
        ...     def delete_collection(self):
        ...         pass
        ...     def get_config(self):
        ...         pass
    """

    @abstractmethod
    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        添加文档到向量库
        Add documents to the vector store

        Args:
            documents: 文档列表，每个文档包含 page_content 和 metadata / Document list, each containing page_content and metadata
            ids: 可选的文档 ID 列表，用于去重和更新 / Optional document ID list for deduplication and updates

        Example:
            >>> from langchain_core.documents import Document
            >>> docs = [
            ...     Document(page_content="设备手册内容", metadata={"source": "manual.pdf"}),
            ...     Document(page_content="故障日志", metadata={"source": "log.log"})
            ... ]
            >>> adapter.add_documents(docs, ids=["chunk_1", "chunk_2"])
        """
        pass

    @abstractmethod
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
            filter: 元数据过滤条件，如 {"device_id": "EQ001"} / Metadata filter conditions, e.g. {"device_id": "EQ001"}

        Returns:
            文档和分数的元组列表，分数范围通常为 [0, 1]，越高越相关 / List of document and score tuples, score range typically [0, 1], higher is more relevant

        Example:
            >>> results = adapter.similarity_search_with_score(
            ...     query="设备报警怎么处理？",
            ...     k=5,
            ...     filter={"device_id": "EQ001"}
            ... )
            >>> for doc, score in results:
            ...     print(f"Score: {score:.4f}, Content: {doc.page_content[:50]}")
        """
        pass

    @abstractmethod
    def get_count(self) -> int:
        """
        获取向量库中的向量总数
        Get total vector count in the vector store

        Returns:
            向量数量 / Vector count

        Example:
            >>> count = adapter.get_count()
            >>> print(f"当前向量库共有 {count} 个向量")
        """
        pass

    @abstractmethod
    def delete_collection(self) -> None:
        """
        删除整个集合
        Delete the entire collection

        警告：此操作不可逆，会删除所有数据
        Warning: This operation is irreversible and deletes all data

        Example:
            >>> adapter.delete_collection()  # 删除所有数据
        """
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        获取当前向量库的配置信息
        Get current vector store configuration info

        Returns:
            配置字典，至少包含： / Configuration dict, at minimum containing:
            - collection_name: 集合名称 / Collection name
            - persist_directory: 持久化目录（如果支持） / Persist directory (if supported)
            - vector_count: 向量数量 / Vector count

        Example:
            >>> config = adapter.get_config()
            >>> print(f"Collection: {config['collection_name']}")
            >>> print(f"Vectors: {config['vector_count']}")
        """
        pass

    # ========== 可选方法 ==========

    def persist(self) -> None:
        """
        持久化到磁盘（可选实现）
        Persist to disk (optional implementation)

        不是所有向量库都需要显式持久化，有些是自动持久化的
        Not all vector stores require explicit persistence; some persist automatically

        Example:
            >>> adapter.persist()  # 保存到磁盘
        """
        pass

    def reset_for_memory_cleanup(self) -> 'VectorStoreAdapter':
        """
        重建连接以释放内存（可选实现）
        Rebuild connection to release memory (optional implementation)

        用于批量入库时的内存优化，某些向量库（如 Chroma）的索引会
        在内存中累积，需要定期重建连接才能释放。
        Used for memory optimization during batch ingestion. Some vector stores (e.g. Chroma)
        accumulate indexes in memory and require periodic connection rebuilds to release.

        默认实现返回 self（不做任何操作），子类可覆盖此方法在原地重建内部连接。
        Default implementation returns self (no-op); subclasses can override to rebuild
        internal connections in-place.

        Returns:
            self（原地更新后的当前实例）/ self (current instance after in-place update)

        Note:
            实现时应原地替换内部对象（如 _chroma、_faiss），而非返回新实例。
            Implementations should replace internal objects (e.g. _chroma, _faiss) in-place,
            而非返回新实例，以确保所有外部引用自动保持有效。
            rather than returning a new instance, to ensure all external references
            remain valid automatically.

        Example:
            >>> # 批量入库时每 10 个文件清理一次内存
            >>> for i, file in enumerate(files):
            ...     adapter.add_documents(...)
            ...     if i % 10 == 0:
            ...         adapter.reset_for_memory_cleanup()
        """
        return self

    def supports_filter(self) -> bool:
        """
        是否支持元数据过滤
        Whether metadata filtering is supported

        Returns:
            True 如果支持 metadata 过滤 / True if metadata filtering is supported

        Note:
            FAISS 等纯向量索引不支持 metadata 过滤，
            需要在应用层实现过滤逻辑
            Pure vector indexes like FAISS do not support metadata filtering;
            filtering logic must be implemented at the application layer
        """
        return True

    def sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗元数据以符合向量库要求
        Sanitize metadata to meet vector store requirements

        Args:
            metadata: 原始元数据 / Raw metadata

        Returns:
            清洗后的元数据 / Sanitized metadata

        Note:
            不同向量库对元数据类型有不同限制：
            Different vector stores have different type restrictions on metadata:
            - Chroma: 只接受 str, int, float, bool / Only accepts str, int, float, bool
            - FAISS: 通常不存储元数据 / Typically does not store metadata
            - Milvus: 支持更多类型 / Supports more types
        """
        clean_metadata = {}
        for k, v in metadata.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                clean_metadata[k] = v
            else:
                clean_metadata[k] = str(v)
        return clean_metadata
