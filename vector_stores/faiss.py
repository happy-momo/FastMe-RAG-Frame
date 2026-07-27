"""
FAISS 向量库适配器
FAISS Vector Store Adapter

封装 FAISS 向量库的操作，提供统一的接口。
Wraps FAISS vector store operations, providing a unified interface.

Classes:
    FAISSAdapter: FAISS 向量库适配器 / FAISS vector store adapter

Features:
    - 纯内存索引，速度极快 / Pure in-memory index, extremely fast
    - 支持持久化到磁盘 / Supports persistence to disk
    - 不支持元数据过滤（需要在应用层实现） / Does not support metadata filtering (must be implemented at application layer)
    - 支持内存清理（保存并重新加载索引） / Supports memory cleanup (save and reload index)

Limitations:
    - 不支持元数据过滤，filter 参数会被忽略 / Does not support metadata filtering, filter parameter is ignored
    - 元数据自动清洗（与 ChromaAdapter 一致） / Metadata auto-sanitized (consistent with ChromaAdapter)

Example:
    >>> from vector_stores.faiss import FAISSAdapter
    >>> from langchain_huggingface import HuggingFaceEmbeddings
    >>>
    >>> embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    >>> adapter = FAISSAdapter(
    ...     embedding_function=embeddings,
    ...     index_path="./data/faiss_index"
    ... )
    >>>
    >>> # 添加文档
    >>> from langchain_core.documents import Document
    >>> docs = [Document(page_content="测试内容", metadata={"source": "test.txt"})]
    >>> adapter.add_documents(docs)
    >>>
    >>> # 搜索
    >>> results = adapter.similarity_search_with_score("测试查询", k=5)
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from vector_stores.base import VectorStoreAdapter

# 框架日志配置
logger = logging.getLogger("fastme_rag")


class FAISSAdapter(VectorStoreAdapter):
    """
    FAISS 向量库适配器
    FAISS Vector Store Adapter

    封装 FAISS 向量库的操作，实现 VectorStoreAdapter 接口。
    Wraps FAISS vector store operations, implementing the VectorStoreAdapter interface.

    特性：
    Features:
    - 纯内存索引，速度极快 / Pure in-memory index, extremely fast
    - 支持持久化到磁盘 / Supports persistence to disk
    - 不支持元数据过滤（filter 参数会被忽略） / Does not support metadata filtering (filter parameter is ignored)

    限制：
    Limitations:
    - 不支持元数据过滤，需要在应用层实现 / Does not support metadata filtering, must be implemented at application layer
    - 元数据自动清洗（只保留 str/int/float/bool，None 被丢弃，其他类型转为 str）
      Metadata auto-sanitized (keeps only str/int/float/bool, None dropped, other types converted to str)

    Attributes:
        _faiss: FAISS 实例 / FAISS instance
        _embedding_function: Embedding 函数 / Embedding function
        _index_path: 索引持久化路径 / Index persist path

    Example:
        >>> adapter = FAISSAdapter(
        ...     embedding_function=embeddings,
        ...     index_path="./data/faiss_index"
        ... )
        >>> adapter.add_documents(docs)
        >>> results = adapter.similarity_search_with_score("查询", k=5)
    """

    def __init__(
        self,
        embedding_function: Embeddings,
        index_path: Optional[str] = None,
        load_existing: bool = True,
    ):
        """
        初始化 FAISS 适配器
        Initialize FAISS adapter

        Args:
            embedding_function: LangChain Embedding 函数 / LangChain Embedding function
            index_path: 索引持久化路径（可选） / Index persist path (optional)
            load_existing: 如果索引存在，是否加载现有索引 / Whether to load existing index if present

        Example:
            >>> from langchain_huggingface import HuggingFaceEmbeddings
            >>> embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
            >>> adapter = FAISSAdapter(
            ...     embedding_function=embeddings,
            ...     index_path="./data/faiss_index"
            ... )
        """
        self._embedding_function = embedding_function
        self._index_path = index_path

        # chunk_id -> FAISS docstore_id 映射，用于去重
        # chunk_id -> FAISS docstore_id mapping, used for deduplication
        self._chunk_id_to_docstore_id: Dict[str, str] = {}

        # 尝试加载现有索引，否则创建空索引
        if load_existing and index_path and Path(index_path).exists():
            try:
                self._faiss = FAISS.load_local(
                    folder_path=index_path,
                    embeddings=embedding_function,
                    allow_dangerous_deserialization=True
                )
                # 重建 chunk_id 映射（从已有文档的 metadata 中提取）
                self._rebuild_chunk_id_mapping()
                logger.info(f"[FAISSAdapter] 加载现有索引：{index_path}，已有 {self.get_count()} 个向量")
            except Exception as e:
                logger.warning(f"[FAISSAdapter] 加载索引失败，创建新索引：{e}")
                self._faiss = self._create_empty_index(embedding_function)
        else:
            # 创建空索引
            self._faiss = self._create_empty_index(embedding_function)
            logger.info(f"[FAISSAdapter] 创建新索引")

    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        添加文档到 FAISS（支持基于 chunk_id 的去重）
        Add documents to FAISS (supports chunk_id-based deduplication)

        Args:
            documents: 文档列表 / Document list
            ids: 文档 ID 列表（chunk_id），用于去重 / Document ID list (chunk_id), used for deduplication

        Note:
            当提供 ids 时，会先删除相同 chunk_id 的已有文档，再添加新文档（upsert 语义）
            When ids are provided, existing documents with the same chunk_id are deleted first (upsert semantics)
            元数据会自动清洗（只保留 str/int/float/bool，None 被丢弃，其他类型转为 str）
            Metadata is auto-sanitized (keeps only str/int/float/bool, None dropped, other types converted to str)
        """
        # 清洗元数据（与 ChromaAdapter 保持一致）
        clean_docs = []
        for doc in documents:
            clean_metadata = self.sanitize_metadata(doc.metadata)
            clean_docs.append(Document(
                page_content=doc.page_content,
                metadata=clean_metadata
            ))

        # 如果提供了 ids，执行去重（upsert 语义）
        if ids:
            duplicate_count = 0
            for chunk_id in ids:
                if chunk_id in self._chunk_id_to_docstore_id:
                    docstore_id = self._chunk_id_to_docstore_id[chunk_id]
                    try:
                        self._faiss.delete([docstore_id])
                        del self._chunk_id_to_docstore_id[chunk_id]
                        duplicate_count += 1
                    except Exception as e:
                        logger.debug(f"[FAISSAdapter] 删除旧文档失败: {e}")
            if duplicate_count > 0:
                logger.debug(f"[FAISSAdapter] 去重：删除 {duplicate_count} 个已有文档")

        # 添加到 FAISS
        result_ids = self._faiss.add_documents(clean_docs)

        # 建立 chunk_id -> docstore_id 映射
        if ids and result_ids:
            for chunk_id, docstore_id in zip(ids, result_ids):
                self._chunk_id_to_docstore_id[chunk_id] = docstore_id

        logger.debug(f"[FAISSAdapter] 添加 {len(clean_docs)} 个文档")

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
            filter: 元数据过滤条件（FAISS 不支持，会被忽略） / Metadata filter conditions (FAISS does not support, will be ignored)

        Returns:
            文档和分数的元组列表 / List of document and score tuples

        Note:
            FAISS 不支持元数据过滤，filter 参数会被忽略
            FAISS does not support metadata filtering, the filter parameter is ignored
            如需过滤，请在应用层实现
            For filtering, implement at the application layer
        """
        if filter:
            logger.warning(
                "[FAISSAdapter] FAISS 不支持元数据过滤，filter 参数将被忽略。"
                "请在应用层实现过滤逻辑。"
            )

        results = self._faiss.similarity_search_with_score(query=query, k=k)
        return results

    def get_count(self) -> int:
        """
        获取向量总数
        Get total vector count

        Returns:
            向量数量 / Number of vectors
        """
        try:
            return self._faiss.index.ntotal
        except AttributeError:
            return 0

    def delete_collection(self) -> None:
        """
        删除集合（重置索引）
        Delete collection (reset index)

        Note:
            FAISS 是内存索引，重置即可删除所有数据
            FAISS is an in-memory index; resetting deletes all data
        """
        self._faiss = self._create_empty_index(self._embedding_function)
        self._chunk_id_to_docstore_id.clear()
        logger.info("[FAISSAdapter] 索引已重置")

    def get_config(self) -> Dict[str, Any]:
        """
        获取配置信息
        Get configuration info

        Returns:
            配置信息字典 / Configuration info dictionary
        """
        return {
            "index_path": self._index_path,
            "vector_count": self.get_count(),
            "supports_filter": False,
        }

    def persist(self) -> None:
        """
        持久化到磁盘
        Persist to disk

        Note:
            FAISS 需要显式调用 save_local 才能持久化
            FAISS requires explicit save_local call to persist
        """
        if self._index_path:
            self._faiss.save_local(self._index_path)
            logger.info(f"[FAISSAdapter] 索引已保存到 {self._index_path}")
        else:
            logger.warning("[FAISSAdapter] 未设置 index_path，无法持久化")

    def reset_for_memory_cleanup(self) -> 'FAISSAdapter':
        """
        保存并重新加载索引以释放内存
        Save and reload index to release memory

        在当前实例上重新加载 FAISS 索引，释放旧的内存索引。
        Reloads FAISS index on current instance, releasing old in-memory index.

        Returns:
            self（原地更新，保持所有外部引用有效）/ self (updated in-place, keeping all external references valid)

        Note:
            原地替换 _faiss 内部对象，而非返回新实例。
            Replaces _faiss internal object in-place instead of returning a new instance.
            这确保所有持有当前适配器引用的组件自动使用更新后的索引，
            This ensures all components holding a reference to this adapter
            automatically use the updated index,
            避免引用不同步导致的内存泄漏和数据不一致。
            avoiding memory leaks and data inconsistency from reference desynchronization.
        """
        import gc

        logger.info("[FAISSAdapter] 保存并重新加载索引以释放内存...")

        if self._index_path:
            # 保存当前索引
            self.persist()

            # 原地重新加载 FAISS 索引
            self._faiss = FAISS.load_local(
                folder_path=self._index_path,
                embeddings=self._embedding_function,
                allow_dangerous_deserialization=True
            )

            # 重建 chunk_id 映射
            self._rebuild_chunk_id_mapping()

            # 清理垃圾
            gc.collect()

            logger.info("[FAISSAdapter] 索引已重新加载，内存已释放")
            return self
        else:
            logger.warning("[FAISSAdapter] 未设置 index_path，无法重新加载")
            return self

    def supports_filter(self) -> bool:
        """
        FAISS 不支持元数据过滤
        FAISS does not support metadata filtering

        Returns:
            始终返回 False / Always returns False
        """
        return False

    def _rebuild_chunk_id_mapping(self):
        """
        从现有文档的 metadata 中重建 chunk_id -> docstore_id 映射
        Rebuild chunk_id -> docstore_id mapping from existing document metadata

        当加载已有索引或重新加载索引后调用，确保去重映射与实际数据一致。
        Called after loading or reloading an existing index to ensure the dedup mapping is consistent.
        """
        self._chunk_id_to_docstore_id.clear()
        if hasattr(self._faiss, 'docstore') and hasattr(self._faiss, 'index_to_docstore_id'):
            for faiss_idx, docstore_id in self._faiss.index_to_docstore_id.items():
                try:
                    doc = self._faiss.docstore.search(docstore_id)
                    if doc and hasattr(doc, 'metadata'):
                        chunk_id = doc.metadata.get("chunk_id")
                        if chunk_id:
                            self._chunk_id_to_docstore_id[chunk_id] = docstore_id
                except Exception:
                    pass
        if self._chunk_id_to_docstore_id:
            logger.debug(f"[FAISSAdapter] 重建 chunk_id 映射：{len(self._chunk_id_to_docstore_id)} 条记录")

    def _create_empty_index(self, embedding_function: Embeddings) -> FAISS:
        """
        创建一个空的 FAISS 索引
        Create an empty FAISS index

        Args:
            embedding_function: Embedding 函数 / Embedding function

        Returns:
            空的 FAISS 实例 / Empty FAISS instance

        Note:
            FAISS.from_embeddings 不支持空列表，需要特殊处理
            FAISS.from_embeddings does not support empty lists, requires special handling
            使用虚拟文档初始化后删除它
            Initialize with a dummy document then remove it
        """
        import numpy as np

        # 创建一个虚拟文档和它的 embedding 来初始化索引
        dummy_text = "__init_empty_index__"
        dummy_embedding = embedding_function.embed_query(dummy_text)

        # 使用虚拟 embedding 创建索引
        faiss_instance = FAISS.from_embeddings(
            text_embeddings=[(dummy_text, dummy_embedding)],
            embedding=embedding_function
        )

        # 获取虚拟文档的 ID
        dummy_id = list(faiss_instance.index_to_docstore_id.values())[0]

        # 从 docstore 删除文档
        if hasattr(faiss_instance.docstore, '_dict'):
            faiss_instance.docstore._dict.pop(dummy_id, None)

        # 清空 index_to_docstore_id 映射
        faiss_instance.index_to_docstore_id = {}

        # 从 FAISS 索引删除向量（重建空索引）
        import faiss
        embedding_dim = len(dummy_embedding)
        faiss_instance.index = faiss.IndexFlatL2(embedding_dim)

        return faiss_instance
