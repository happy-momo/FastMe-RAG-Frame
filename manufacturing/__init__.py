"""
制造业模块
Manufacturing Module

提供制造业场景化的元数据抽取等功能。
Provides manufacturing-scenario metadata extraction and other capabilities.

可用组件：
Available components:
- IndustrialMetadataExtractor: 工业元数据抽取器 / Industrial metadata extractor

Example:
    >>> from manufacturing import IndustrialMetadataExtractor
    >>> extractor = IndustrialMetadataExtractor()
    >>> chunks = extractor.enrich_chunk(chunks)
"""

from manufacturing.metadata_extractor import IndustrialMetadataExtractor

__all__ = ["IndustrialMetadataExtractor"]
