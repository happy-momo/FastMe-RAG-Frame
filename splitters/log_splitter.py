import re
from typing import List

from core.models import FastMeDocument, FastMeChunk
from splitters.base import BaseSplitter


class LogSplitter(BaseSplitter):
    """
    运维日志拆解器
    Operations Log Splitter

    规则：
    Rules:
    1. 遇到时间戳，就开启新的一条日志记录
       Start a new log entry when a timestamp is encountered
    2. 没有遇到时间戳就将日志拼接到上一条记录
       Append to the previous entry when no timestamp is found
    3. 每个日志生成一个 chunk
       Each log entry generates one chunk

    尺寸限制：
    Size limits:
    - 单个 chunk 最大字符数：max_chunk_size (默认 600 字)
      Max characters per chunk: max_chunk_size (default 600)
    - 超大日志条目会自动拆分为多个 sub-chunks
      Oversized log entries are automatically split into sub-chunks

    Args:
        max_chunk_size: 单个 chunk 最大字符数，默认 600 / Max characters per chunk, default 600

    Example:
        >>> splitter = LogSplitter()  # 默认 600 字 / Default 600 chars
        >>> splitter = LogSplitter(max_chunk_size=500)  # 自定义 500 字 / Custom 500 chars
    """

    # 日志推荐 chunk 大小 / Recommended chunk size for logs
    DEFAULT_MAX_CHUNK_SIZE = 600

    def __init__(self, max_chunk_size: int = None):
        # 调用基类构造函数，使用类默认值或传入值
        # Call base constructor, use class default or provided value
        super().__init__(max_chunk_size or self.DEFAULT_MAX_CHUNK_SIZE)
        # 时间戳匹配：只匹配行首的时间戳部分，允许后面跟日志内容
        # 支持：2024-01-15 10:30:00、2024/01/15 10:30:00.123 等格式
        # 不要求时间戳独占一行，实际日志通常为 "2024-01-15 10:30:00 ERROR: ..."
        self.timestamp_pattern = re.compile(
            r"^\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)"
            )

    def _split_large_entry(self, entry: str, max_size: int = None) -> List[str]:
        """
        将超大日志条目拆分为多个 sub-chunks
        Split oversized log entries into multiple sub-chunks

        Args:
            entry: 日志条目文本 / Log entry text
            max_size: 单个 chunk 最大字符数，默认使用 self.max_chunk_size / Max characters per chunk, defaults to self.max_chunk_size

        Returns:
            拆分后的文本列表 / List of split text segments
        """
        if max_size is None:
            max_size = self.max_chunk_size

        if len(entry) <= max_size:
            return [entry]

        # 按行拆分
        lines = entry.splitlines()
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line)

            # 单行就超限，强制切割
            if line_size > max_size:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # 按固定长度切割超长行
                for i in range(0, len(line), max_size):
                    chunks.append(line[i:i + max_size])
            else:
                # 当前行加入后是否超限
                if current_size + line_size + 1 > max_size:  # +1 是换行符
                    if current_chunk:
                        chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                    current_size = line_size
                else:
                    current_chunk.append(line)
                    current_size += line_size + 1

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def split(self, document: FastMeDocument) -> List[FastMeChunk]:
        """
        拆分日志文档为多个 chunk
        Split log document into multiple chunks

        Args:
            document: FastMeDocument 实例 / FastMeDocument instance

        Returns:
            FastMeChunk 列表 / List of FastMeChunk
        """

        lines = document.text.splitlines()

        entries: list[str] = []
        current: list[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if self.timestamp_pattern.match(line):
                if current:
                    entries.append("\n".join(current))
                    current.clear()
                current.append(line)
            else:
                current.append(line)

        if current:
            entries.append("\n".join(current))
            current.clear()

        # 拆分超大日志条目并生成 chunks
        chunks: list[FastMeChunk] = []
        chunk_index = 0

        for entry in entries:
            # 拆分超大条目
            sub_chunks = self._split_large_entry(entry)

            for sub_idx, sub_text in enumerate(sub_chunks):
                # 使用基类方法生成 chunk_id
                sub_chunk_id = self._generate_chunk_id(
                    document.doc_id, chunk_index, len(sub_chunks), sub_idx
                )

                # 使用基类方法构建 metadata
                metadata = self._build_chunk_metadata(
                    document, sub_chunk_id, sub_chunks, sub_idx,
                    extra_metadata={}
                )

                timestamp_match = self.timestamp_pattern.match(sub_text)
                if timestamp_match:
                    metadata["timestamp"] = timestamp_match.group(1)

                chunks.append(FastMeChunk(
                    chunk_id=metadata["chunk_id"],
                    doc_id=metadata["doc_id"],
                    doc_type=metadata["doc_type"],
                    text=sub_text,
                    metadata=metadata
                ))

                chunk_index += 1

        return chunks
