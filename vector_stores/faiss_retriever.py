"""
FAISS 检索器实现 - 支持后过滤
FAISS Retriever Implementation - Supports Post-filtering

将 FAISSAdapter 包装为 BaseRetriever 接口，采用"召回 + 后过滤"策略。
Wraps FAISSAdapter into the BaseRetriever interface, using "recall + post-filter" strategy.
"""

import logging
from typing import List, Optional, Any

from core.retriever import BaseRetriever, FilterCondition, ResultConverterMixin
from core.models import FastMeSearchResult
from vector_stores.base import VectorStoreAdapter

logger = logging.getLogger("fastme_rag")


class FAISSRetriever(BaseRetriever, ResultConverterMixin):
    """
    FAISS 向量库检索器
    FAISS Vector Store Retriever

    包装 FAISSAdapter，实现 BaseRetriever 接口。
    Wraps FAISSAdapter, implementing the BaseRetriever interface.
    由于 FAISS 不支持原生过滤，采用"召回 + 后过滤"策略。
    Since FAISS does not support native filtering, uses "recall + post-filter" strategy.

    Args:
        adapter: FAISSAdapter 实例 / FAISSAdapter instance
        post_filter_multiplier: 后过滤倍数，默认召回 top_k * 5 再过滤 / Post-filter multiplier, defaults to recalling top_k * 5 then filtering

    Example:
        >>> from vector_stores import FAISSAdapter
        >>> from vector_stores.faiss_retriever import FAISSRetriever
        >>>
        >>> adapter = FAISSAdapter(...)
        >>> retriever = FAISSRetriever(adapter, post_filter_multiplier=5)
        >>> results = retriever.retrieve(
        ...     query="设备报警怎么处理？",
        ...     top_k=5,
        ...     filters=[FilterCondition(field="device_id", operator="$eq", value="EQ001")]
        ... )
    """

    def __init__(self, adapter: VectorStoreAdapter, post_filter_multiplier: int = 5):
        self.adapter = adapter
        self.post_filter_multiplier = post_filter_multiplier

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
        if not filters:
            # 无过滤时直接返回
            results = self.adapter.similarity_search_with_score(query=query, k=top_k)
            return self._to_fastme_results(results)

        # 有过滤时，先召回更多结果
        recall_k = top_k * self.post_filter_multiplier
        results = self.adapter.similarity_search_with_score(query=query, k=recall_k)

        # 后过滤
        filtered_results = self._filter_results(results, filters)

        # 截断到 top_k
        return filtered_results[:top_k]

    def _filter_results(
        self,
        results: List,
        filters: List[FilterCondition]
    ) -> List[FastMeSearchResult]:
        """
        在应用层过滤结果
        Filter results at the application layer

        Args:
            results: [(Document, score), ...] / List of (Document, score) tuples
            filters: FilterCondition 列表 / List of FilterCondition

        Returns:
            过滤后的 FastMeSearchResult 列表 / Filtered list of FastMeSearchResult
        """
        filtered = []

        for doc, score in results:
            if self._match_filters(doc.metadata, filters):
                filtered.append((doc, score))

        return self._to_fastme_results(filtered)

    def _match_filters(
        self,
        metadata: dict,
        filters: List[FilterCondition]
    ) -> bool:
        """
        检查元数据是否满足所有过滤条件
        Check if metadata satisfies all filter conditions

        Args:
            metadata: 元数据字典 / Metadata dict
            filters: FilterCondition 列表 / List of FilterCondition

        Returns:
            True 如果满足所有条件 / True if all conditions are satisfied
        """
        for condition in filters:
            field_value = metadata.get(condition.field)

            if field_value is None:
                return False

            if not self._match_condition(field_value, condition.operator, condition.value):
                return False

        return True

    def _match_condition(self, field_value: Any, operator: str, filter_value: Any) -> bool:
        """
        匹配单个条件
        Match a single condition

        Args:
            field_value: 字段值 / Field value
            operator: 运算符 ($eq, $ne, $in, etc.) / Operator ($eq, $ne, $in, etc.)
            filter_value: 过滤值 / Filter value

        Returns:
            True 如果匹配 / True if matched
        """
        if operator == "$eq":
            return field_value == filter_value
        elif operator == "$ne":
            return field_value != filter_value
        elif operator == "$in":
            return field_value in filter_value
        elif operator == "$nin":
            return field_value not in filter_value
        elif operator == "$gt":
            return field_value > filter_value
        elif operator == "$gte":
            return field_value >= filter_value
        elif operator == "$lt":
            return field_value < filter_value
        elif operator == "$lte":
            return field_value <= filter_value

        logger.warning(f"[FAISSRetriever] 未知运算符：{operator}，视为不匹配")
        return False

    def supports_filter(self) -> bool:
        """
        FAISS 支持过滤（通过应用层后过滤实现）
        FAISS supports filtering (via application-layer post-filtering)

        Returns:
            始终返回 True / Always returns True
        """
        return True
