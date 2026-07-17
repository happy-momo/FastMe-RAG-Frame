"""
拆解器基类模块
Base Splitter Module

提供文档拆解器的注册表和公共基类。
Provides the splitter registry and common base class for document splitters.

Classes:
    SplitterRegistry: 拆解器注册表 / Splitter registry
    BaseSplitter: 拆解器公共基类，提供通用的文本拆分逻辑 / Base splitter class with common text splitting logic
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import re

from core.models import FastMeDocument, FastMeChunk


class SplitterRegistry:
    """
    拆解器注册表
    Splitter Registry

    管理不同文档类型的拆解器实例。
    Manages splitter instances for different document types.

    Example:
        >>> registry = SplitterRegistry()
        >>> registry.register("log", LogSplitter())
        >>> splitter = registry.get("log")
    """

    def __init__(self):
        self._splitters = {}

    def register(self, doc_type: str, splitter):
        """
        注册拆解器
        Register a splitter

        Args:
            doc_type: 文档类型 / Document type
            splitter: 拆解器实例 / Splitter instance
        """
        self._splitters[doc_type] = splitter

    def get(self, doc_type: str):
        """
        获取指定文档类型的拆解器
        Get the splitter for a given document type

        Args:
            doc_type: 文档类型 / Document type

        Returns:
            对应的拆解器实例 / Corresponding splitter instance

        Raises:
            ValueError: 未注册该文档类型的拆解器 / No splitter registered for this document type
        """
        splitter = self._splitters.get(doc_type)
        if not splitter:
            raise ValueError(f"Splitter not registered for doc type: {doc_type}")
        return splitter


class BaseSplitter(ABC):
    """
    拆解器公共基类
    Base Splitter

    提供通用的文本拆分逻辑，包括：
    Provides common text splitting logic, including:
    - 按段落拆分超大文本 / Split oversized text by paragraphs
    - 按行拆分超大段落 / Split oversized paragraphs by lines
    - chunk ID 生成逻辑 / Chunk ID generation logic

    子类需要实现：
    Subclasses must implement:
    - max_chunk_size 属性 / max_chunk_size property
    - split() 方法 / split() method

    Example:
        >>> class MySplitter(BaseSplitter):
        ...     def __init__(self, max_chunk_size=1000):
        ...         self.max_chunk_size = max_chunk_size
        ...
        ...     def split(self, document: FastMeDocument) -> list[FastMeChunk]:
        ...         # 实现具体的拆分逻辑 / Implement specific splitting logic
        ...         pass
    """

    def __init__(self, max_chunk_size: int = 1000):
        """
        初始化基类
        Initialize base splitter

        Args:
            max_chunk_size: 单个 chunk 最大字符数，默认 1000 / Max characters per chunk, default 1000
        """
        self.max_chunk_size = max_chunk_size

    def _split_by_paragraphs(self, lines: List[str], max_size: int = None) -> List[List[str]]:
        """
        将文本按段落拆分为多个块
        Split text into multiple chunks by paragraphs

        Args:
            lines: 文本行列表 / List of text lines
            max_size: 单个块最大字符数，默认使用 self.max_chunk_size / Max characters per chunk, defaults to self.max_chunk_size

        Returns:
            拆分后的块列表，每个块是一个行列表 / List of chunks, each chunk is a list of lines
        """
        if max_size is None:
            max_size = self.max_chunk_size

        # 按空行识别段落
        paragraphs = []
        current_para = []

        for line in lines:
            if not line.strip():
                if current_para:
                    paragraphs.append(current_para)
                    current_para = []
            else:
                current_para.append(line)

        if current_para:
            paragraphs.append(current_para)

        # 按段落累积，超过阈值就拆分
        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_text = "\n".join(para)
            para_size = len(para_text)

            # 单个段落就超限，强制按行拆分
            if para_size > max_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_size = 0

                # 按行拆分大段落
                sub_chunk = []
                sub_size = 0
                for line in para:
                    line_size = len(line)
                    if sub_size + line_size > max_size:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = [line]
                        sub_size = line_size
                    else:
                        sub_chunk.append(line)
                        sub_size += line_size
                if sub_chunk:
                    chunks.append(sub_chunk)
            else:
                # 当前段落加入后是否超限
                if current_size + para_size + 1 > max_size:  # +1 是换行符
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para
                    current_size = para_size
                else:
                    current_chunk.extend(para)
                    current_size += para_size + 1

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_large_text(self, content: List[str], max_size: int = None) -> List[List[str]]:
        """
        将超大文本块拆分为多个子块
        Split oversized text blocks into multiple sub-blocks

        这是 _split_by_paragraphs 的别名，为了统一的接口。
        This is an alias for _split_by_paragraphs, for a unified interface.

        Args:
            content: 文本内容行列表 / List of text content lines
            max_size: 单个块最大字符数，默认使用 self.max_chunk_size / Max characters per chunk, defaults to self.max_chunk_size

        Returns:
            拆分后的块列表，每个块是一个行列表 / List of chunks, each chunk is a list of lines
        """
        return self._split_by_paragraphs(content, max_size)

    def _generate_chunk_id(
        self,
        doc_id: str,
        chunk_index: int,
        total_sub_chunks: int = 1,
        sub_chunk_index: int = 0
    ) -> str:
        """
        生成 chunk ID
        Generate chunk ID

        Args:
            doc_id: 文档 ID / Document ID
            chunk_index: chunk 索引 / Chunk index
            total_sub_chunks: 总 sub-chunk 数量 / Total number of sub-chunks
            sub_chunk_index: 当前 sub-chunk 索引（从 0 开始） / Current sub-chunk index (0-based)

        Returns:
            生成的 chunk ID / Generated chunk ID
        """
        if total_sub_chunks == 1:
            return f"{doc_id}_{chunk_index}"
        else:
            return f"{doc_id}_{chunk_index}_part{sub_chunk_index + 1}of{total_sub_chunks}"

    def _build_chunk_metadata(
        self,
        document: FastMeDocument,
        chunk_id: str,
        sub_chunks: list,
        sub_idx: int,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        构建 chunk 元数据（通用逻辑）
        Build chunk metadata (common logic)

        所有 splitter 子类可以复用此方法构建标准的 metadata 字典。
        All splitter subclasses can reuse this method to build a standard metadata dictionary.

        Args:
            document: FastMeDocument 实例 / FastMeDocument instance
            chunk_id: chunk ID / Chunk ID
            sub_chunks: sub-chunk 列表（用于计算总数） / List of sub-chunks (for total count)
            sub_idx: 当前 sub-chunk 索引 / Current sub-chunk index
            extra_metadata: 额外的元数据字段（可选） / Additional metadata fields (optional)

        Returns:
            元数据字典 / Metadata dictionary

        Example:
            >>> metadata = self._build_chunk_metadata(
            ...     document, chunk_id, sub_chunks, sub_idx,
            ...     extra_metadata={"process_num": "1", "device_id": "EQ001"}
            ... )
        """
        metadata = {
            **document.metadata,
            "doc_id": document.doc_id,
            "doc_type": document.doc_type,
            "chunk_id": chunk_id,
            "splitter": self.__class__.__name__.lower().replace("splitter", "_splitter"),
            "is_sub_chunk": len(sub_chunks) > 1,
            "sub_chunk_index": sub_idx if len(sub_chunks) > 1 else None,
            "sub_chunk_total": len(sub_chunks) if len(sub_chunks) > 1 else None
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        return metadata

    def _extract_with_patterns(
        self,
        text: str,
        patterns: List[re.Pattern],
        findall: bool = False
    ) -> Optional[Any]:
        r"""
        使用正则模式提取字段（通用逻辑）
        Extract fields using regex patterns (common logic)

        所有 splitter 子类可以复用此方法提取字段，避免重复编写相同的模式匹配代码。
        All splitter subclasses can reuse this method to extract fields, avoiding duplicate pattern-matching code.

        Args:
            text: 要提取的文本 / Text to extract from
            patterns: 正则表达式模式列表 / List of regex patterns
            findall: 是否使用 findall 返回所有匹配，默认 False（只返回第一个匹配） / Whether to use findall for all matches, default False (first match only)

        Returns:
            提取的结果：
            Extraction results:
            - findall=True: 返回所有匹配的列表 / Returns list of all matches
            - findall=False: 返回第一个匹配的 group(1)，如果没有匹配则返回 None / Returns first match group(1), or None if no match

        Example:
            >>> import re
            >>> patterns = [re.compile(r"设备 ID[：:\s]*([A-Za-z0-9\-_]+)")]
            >>> device_id = self._extract_with_patterns(text, patterns)

            >>> bom_patterns = [re.compile(r"BOM[：:\s]*(.+)")]
            >>> bom_items = self._extract_with_patterns(text, bom_patterns, findall=True)
        """
        if findall:
            results = []
            for pattern in patterns:
                results.extend(pattern.findall(text))
            return results

        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None

    def _create_default_unit(
        self,
        document: FastMeDocument,
        unit_type: str = "default"
    ) -> Dict[str, Any]:
        """
        创建默认单元（当没有识别到任何逻辑单元时的兜底处理）
        Create default unit (fallback when no logical unit is recognized)

        子类可以根据需要覆盖此方法，提供特定于文档类型的默认单元结构。
        Subclasses can override this method to provide document-type-specific default unit structures.

        Args:
            document: FastMeDocument 实例 / FastMeDocument instance
            unit_type: 单元类型提示（子类可用于区分不同的默认结构） / Unit type hint (subclasses can use to distinguish default structures)

        Returns:
            默认单元字典，包含 content 和其他必要字段 / Default unit dict with content and other required fields

        Example:
            >>> # 在子类中覆盖 / Override in subclass
            >>> def _create_default_unit(self, document, unit_type="default"):
            ...     return {
            ...         "chapter_num": "1",
            ...         "chapter_title": document.file_name,
            ...         "level": 1,
            ...         "content": document.text.splitlines()
            ...     }
        """
        # 默认实现：将整个文档作为一个单元
        return {
            "content": document.text.splitlines(),
            "title": document.file_name
        }

    @abstractmethod
    def split(self, document: FastMeDocument) -> List[FastMeChunk]:
        """
        拆分文档为多个 chunk
        Split document into multiple chunks

        Args:
            document: FastMeDocument 实例 / FastMeDocument instance

        Returns:
            FastMeChunk 列表 / List of FastMeChunk
        """
        pass