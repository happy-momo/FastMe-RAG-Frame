"""
Chroma 检索器实现
Chroma Retriever Implementation

将 ChromaAdapter 包装为 BaseRetriever 接口。
Wraps ChromaAdapter into the BaseRetriever interface.
"""

import logging
from typing import List, Optional

from core.retriever import BaseRetriever, FilterCondition, ResultConverterMixin
from core.models import FastMeSearchResult
from vector_stores.base import VectorStoreAdapter

logger = logging.getLogger("fastme_rag")


class ChromaRetriever(BaseRetriever, ResultConverterMixin):
    """
    Chroma 向量库检索器
    Chroma Vector Store Retriever

    包装 ChromaAdapter，实现 BaseRetriever 接口。
    Wraps ChromaAdapter, implementing the BaseRetriever interface.

    Args:
        adapter: ChromaAdapter 实例 / ChromaAdapter instance

    Example:
        >>> from vector_stores import ChromaAdapter
        >>> from vector_stores.chroma_retriever import ChromaRetriever
        >>>
        >>> adapter = ChromaAdapter(...)
        >>> retriever = ChromaRetriever(adapter)
        >>> results = retriever.retrieve(
        ...     query="设备报警怎么处理？",
        ...     top_k=5,
        ...     filters=[FilterCondition(field="device_id", operator="$eq", value="EQ001")]
        ... )
    """

    def __init__(self, adapter: VectorStoreAdapter):
        self.adapter = adapter

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
        # 将 FilterCondition 转换为 Chroma 语法
        chroma_filter = self._to_chroma_filter(filters) if filters else None

        # 调用 ChromaAdapter
        results = self.adapter.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=chroma_filter
        )

        # 转换为 FastMeSearchResult
        return self._to_fastme_results(results)

    def _to_chroma_filter(self, conditions: List[FilterCondition]) -> Optional[dict]:
        """
        将 FilterCondition 列表转换为 Chroma 过滤语法
        Convert FilterCondition list to Chroma filter syntax

        Args:
            conditions: FilterCondition 列表 / List of FilterCondition

        Returns:
            Chroma 过滤字典，如 {"$and": [{"field": {"$op": value}}, ...]} / Chroma filter dict, e.g. {"$and": [{"field": {"$op": value}}, ...]}
        """
        if not conditions:
            return None

        if len(conditions) == 1:
            c = conditions[0]
            return {c.field: {c.operator: c.value}}

        # 多条件用 $and 连接
        return {
            "$and": [
                {c.field: {c.operator: c.value}}
                for c in conditions
            ]
        }

    def supports_filter(self) -> bool:
        """
        Chroma 支持元数据过滤
        Chroma supports metadata filtering

        Returns:
            始终返回 True / Always returns True
        """
        return True
