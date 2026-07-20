"""
检索器抽象层
Retriever Abstraction Layer

定义通用过滤语法和检索器抽象基类，支持多种向量库后端。
Defines common filter syntax and retriever abstract base classes, supporting multiple vector store backends.

Example:
    >>> from core.retriever import BaseRetriever, FilterCondition, ResultConverterMixin
    >>>
    >>> # 定义过滤条件 / Define filter condition
    >>> condition = FilterCondition(field="device_id", operator="$eq", value="EQ001")
    >>>
    >>> # 实现自定义检索器（使用 mixin 复用 _to_fastme_results）
    >>> # Implement custom retriever (using mixin to reuse _to_fastme_results)
    >>> class MyRetriever(BaseRetriever, ResultConverterMixin):
    ...     def retrieve(self, query, top_k, filters=None):
    ...         results = self.adapter.similarity_search_with_score(query, k=top_k)
    ...         return self._to_fastme_results(results)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Tuple
from dataclasses import dataclass

from core.models import FastMeSearchResult
from langchain_core.documents import Document


@dataclass
class FilterCondition:
    """
    通用过滤条件
    Common Filter Condition

    框架定义的标准过滤格式，各向量库适配器负责转换为各自语法。
    Standard filter format defined by the framework; each vector store adapter converts to its own syntax.

    支持的运算符：
    Supported operators:
    - $eq: 等于 / Equal to
    - $ne: 不等于 / Not equal to
    - $in: 属于列表 / In list
    - $nin: 不属于列表 / Not in list
    - $gt: 大于 / Greater than
    - $gte: 大于等于 / Greater than or equal to
    - $lt: 小于 / Less than
    - $lte: 小于等于 / Less than or equal to

    Example:
        # 等价于 Chroma: {"device_id": {"$eq": "EQ001"}}
        FilterCondition(field="device_id", operator="$eq", value="EQ001")

        # 等价于 Chroma: {"timestamp": {"$gte": "2025-01-01"}}
        FilterCondition(field="timestamp", operator="$gte", value="2025-01-01")

        # 组合条件 (AND) / Combined conditions (AND)
        [
            FilterCondition(field="device_id", operator="$eq", value="EQ001"),
            FilterCondition(field="line_id", operator="$in", value=["LN01", "LN02"])
        ]
    """
    field: str
    operator: str  # $eq, $ne, $in, $nin, $gt, $gte, $lt, $lte
    value: Any


class BaseRetriever(ABC):
    """
    检索器抽象基类
    Retriever Abstract Base Class

    所有向量库检索器必须实现此接口。
    All vector store retrievers must implement this interface.

    实现示例 / Implementation example:
        >>> class ChromaRetriever(BaseRetriever):
        ...     def __init__(self, chroma_adapter):
        ...         self.adapter = chroma_adapter
        ...
        ...     def retrieve(self, query, top_k, filters=None):
        ...         # 将 FilterCondition 转换为 Chroma 语法
        ...         # Convert FilterCondition to Chroma syntax
        ...         chroma_filter = self._to_chroma_filter(filters)
        ...         results = self.adapter.similarity_search_with_score(query, k=top_k, filter=chroma_filter)
        ...         return self._to_fastme_results(results)
        ...
        ...     def supports_filter(self) -> bool:
        ...         return True
    """

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[List[FilterCondition]] = None
    ) -> List[FastMeSearchResult]:
        """
        执行检索
        Execute retrieval

        Args:
            query: 查询文本 / Query text
            top_k: 返回数量 / Number of results to return
            filters: 过滤条件列表 / List of filter conditions

        Returns:
            FastMeSearchResult 列表 / List of FastMeSearchResult
        """
        pass

    @abstractmethod
    def supports_filter(self) -> bool:
        """
        是否支持元数据过滤
        Whether metadata filtering is supported

        Returns:
            True 如果支持过滤 / True if filtering is supported
        """
        pass


class ResultConverterMixin:
    """
    结果转换工具混入类
    Result Converter Mixin

    提供 _to_fastme_results 方法，将 (Document, score) 转换为 FastMeSearchResult 列表。
    Provides _to_fastme_results method to convert (Document, score) to FastMeSearchResult list.
    ChromaRetriever 和 FAISSRetriever 可以复用此方法，避免重复代码。
    ChromaRetriever and FAISSRetriever can reuse this method to avoid duplicate code.

    Example:
        >>> class ChromaRetriever(BaseRetriever, ResultConverterMixin):
        ...     def retrieve(self, query, top_k, filters=None):
        ...         results = self.adapter.similarity_search_with_score(query, k=top_k)
        ...         return self._to_fastme_results(results)  # 使用 mixin 方法 / Use mixin method
    """

    def _to_fastme_results(self, results: List[Tuple[Document, float]]) -> List[FastMeSearchResult]:
        """
        将 (Document, score) 转换为 FastMeSearchResult 列表
        Convert (Document, score) to FastMeSearchResult list

        Args:
            results: [(Document, score), ...] 列表 / List of (Document, score) tuples

        Returns:
            FastMeSearchResult 列表 / List of FastMeSearchResult

        Example:
            >>> results = adapter.similarity_search_with_score(query, k=5)
            >>> fastme_results = self._to_fastme_results(results)
        """
        return [
            FastMeSearchResult(
                chunk_id=doc.metadata.get("chunk_id"),
                doc_id=doc.metadata.get("doc_id"),
                doc_type=doc.metadata.get("doc_type"),
                score=float(score) if score is not None else 0.0,
                text=doc.page_content,
                metadata=doc.metadata
            )
            for doc, score in results
        ]
