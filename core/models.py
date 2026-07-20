"""
核心数据模型
Core Data Models

提供统一的数据结构用于文档处理、切片和检索结果。
Provides unified data structures for document processing, chunking, and retrieval results.

Classes:
    FastMeDocument: 文档级数据模型，表示原始文档 / Document-level data model representing a raw document
    FastMeChunk: 切片级数据模型，表示文档拆分后的片段 / Chunk-level data model representing a document fragment
    FastMeSearchResult: 检索结果模型，表示向量检索返回的结果 / Search result model representing a vector retrieval result

Example:
    >>> from core.models import FastMeDocument, FastMeChunk
    >>> doc = FastMeDocument(
    ...     doc_id="doc_001",
    ...     doc_type="manual",
    ...     file_name="equipment.pdf",
    ...     file_path="/path/to/file.pdf",
    ...     text="设备操作说明...",
    ...     metadata={"device_id": "EQ001"}
    ... )
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FastMeDocument:
    """
    文档级数据模型
    Document-level Data Model

    表示原始文档，包含文件基本信息和完整文本内容。
    Represents a raw document with basic file information and full text content.

    Attributes:
        doc_id (str): 文档唯一标识符 / Unique document identifier
        doc_type (str): 文档类型 (log/manual/business/sop) / Document type (log/manual/business/sop)
        file_name (str): 文件名 / File name
        file_path (str): 文件完整路径 / Full file path
        text (str): 文档完整文本内容 / Full document text content
        metadata (dict): 文档元数据，可包含设备 ID、产线号等工业字段 / Document metadata, may include industrial fields like device ID, production line number

    Example:
        >>> doc = FastMeDocument(
        ...     doc_id="manual_001",
        ...     doc_type="manual",
        ...     file_name="equipment_manual.pdf",
        ...     file_path="/docs/manual.pdf",
        ...     text="设备操作手册全文...",
        ...     metadata={"device_model": "EQ-1000"}
        ... )
    """
    doc_id: str
    doc_type: str
    file_name: str
    file_path: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FastMeChunk:
    """
    切片级数据模型
    Chunk-level Data Model

    表示文档拆分后的片段，是向量化和检索的基本单位。
    Represents a document fragment after splitting; the basic unit for vectorization and retrieval.

    Attributes:
        chunk_id (str): 切片唯一标识符 / Unique chunk identifier
        doc_id (str): 所属文档 ID / Parent document ID
        doc_type (str): 文档类型 / Document type
        text (str): 切片文本内容 / Chunk text content
        metadata (dict): 切片元数据，可包含章节号、时间戳等字段 / Chunk metadata, may include chapter number, timestamp, etc.

    Example:
        >>> chunk = FastMeChunk(
        ...     chunk_id="chunk_001",
        ...     doc_id="manual_001",
        ...     doc_type="manual",
        ...     text="第一章 设备概述...",
        ...     metadata={"chapter_num": "1", "page": 5}
        ... )
    """
    chunk_id: str
    doc_id: str
    doc_type: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FastMeSearchResult:
    """
    检索结果模型
    Search Result Model

    表示向量检索返回的结果，包含相似度评分和溯源信息。
    Represents a vector retrieval result with similarity score and source tracing information.

    Attributes:
        chunk_id (str): 切片 ID / Chunk ID
        doc_id (str): 文档 ID / Document ID
        doc_type (str): 文档类型 / Document type
        text (str): 切片文本内容 / Chunk text content
        score (float): 相似度得分，范围 [0, 1]，越高越相关 / Similarity score in [0, 1], higher is more relevant
        metadata (dict): 切片元数据，用于溯源展示 / Chunk metadata for source tracing display

    Example:
        >>> result = FastMeSearchResult(
        ...     chunk_id="chunk_001",
        ...     doc_id="manual_001",
        ...     doc_type="manual",
        ...     text="设备操作步骤...",
        ...     score=0.95,
        ...     metadata={"source": "manual.pdf", "chapter": "1"}
        ... )
    """
    chunk_id: str
    doc_id: str
    doc_type: str
    text: str
    score: float
    metadata: dict[str, Any]
