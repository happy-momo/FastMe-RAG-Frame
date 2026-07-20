import re
from typing import List

from core.models import FastMeDocument, FastMeChunk
from splitters.base import BaseSplitter


class ManualSplitter(BaseSplitter):
    """
    设备手册拆解器
    Equipment Manual Splitter

    适用于：设备操作手册、维修手册、技术规格书等文档
    Applicable to: equipment operation manuals, maintenance manuals, technical specification documents

    拆解规则：
    Splitting rules:
    1. 识别章节标题（如"第 1 章"、"1.1"、"Chapter 1"等）
       Identify chapter headings (e.g. "第 1 章", "1.1", "Chapter 1")
    2. 按章节边界切块，每个章节独立成一个 chunk
       Split at chapter boundaries; each chapter becomes an independent chunk
    3. 提取章节编号、章节标题、层级深度作为 metadata
       Extract chapter number, title, and hierarchy depth as metadata
    4. 识别"设备型号"、"技术参数"等特殊段落，标记为独立 chunk
       Identify special paragraphs like "device model" and "technical specs" as independent chunks
    5. 图纸/表格备注关联所属章节
       Associate drawing/table notes with their parent chapter

    尺寸限制：
    Size limits:
    - 单个 chunk 最大字符数：max_chunk_size (默认 1500 字)
      Max characters per chunk: max_chunk_size (default 1500)
    - 超大章节会自动拆分为多个 sub-chunks
      Oversized chapters are automatically split into sub-chunks

    Args:
        max_chunk_size: 单个 chunk 最大字符数，默认 1500 / Max characters per chunk, default 1500

    Example:
        >>> splitter = ManualSplitter()  # 默认 1500 字 / Default 1500 chars
        >>> splitter = ManualSplitter(max_chunk_size=2000)  # 自定义 2000 字 / Custom 2000 chars
    """

    # 手册推荐 chunk 大小 / Recommended chunk size for manuals
    DEFAULT_MAX_CHUNK_SIZE = 1500

    def __init__(self, max_chunk_size: int = None):
        # 调用基类构造函数，使用类默认值或传入值
        # Call base constructor, use class default or provided value
        super().__init__(max_chunk_size or self.DEFAULT_MAX_CHUNK_SIZE)
        # 章节标题匹配模式（支持中英文多种格式）
        self.chapter_patterns = [
            # 中文格式：第 X 章、第 X 节（允许中文数字与章节字之间有空格）
            re.compile(r"^第\s*([一二三四五六七八九十百\d]+)\s*[章节]\s*(.*)$", re.IGNORECASE),
            # 数字格式：1.1、1.1.1
            re.compile(r"^(\d+(?:\.\d+)*)\s*[、.:\s]*(.*)$"),
            # 英文格式：Chapter 1, Section 1.1
            re.compile(r"^(?:Chapter|Section)\s*(\d+(?:\.\d+)*)\s*[.:]?\s*(.*)$", re.IGNORECASE),
        ]

        # 设备型号匹配模式
        self.device_model_patterns = [
            re.compile(r"设备型号 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"产品型号 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"型号规格 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"Model[：:\s]*([A-Za-z0-9\-_]+)", re.IGNORECASE),
        ]

        # 技术参数段落识别
        self.spec_keywords = [
            "技术参数", "技术规格", "规格参数", "主要参数",
            "性能指标", "技术指标", "Specification", "Technical Data"
        ]

    def _parse_chapter_level(self, chapter_num: str) -> int:
        """
        解析章节编号，返回层级深度
        Parse chapter number and return hierarchy depth

        Args:
            chapter_num: 章节编号（如 "1", "1.1", "1.1.1"）/ Chapter number (e.g. "1", "1.1", "1.1.1")

        Returns:
            层级深度（1 表示顶层章节）/ Hierarchy depth (1 for top-level chapter)
        """
        if not chapter_num:
            return 1
        parts = chapter_num.split(".")
        return len(parts)

    def _extract_chapter_title(self, line: str) -> tuple:
        """
        尝试从一行中提取章节信息
        Try to extract chapter information from a line

        Returns:
            (chapter_num, chapter_title, level) 或 (None, None, None) / (chapter_num, chapter_title, level) or (None, None, None)
        """
        line = line.strip()
        if not line:
            return None, None, None

        for pattern in self.chapter_patterns:
            match = pattern.match(line)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    chapter_num = groups[0]
                    chapter_title = groups[1].strip()
                    level = self._parse_chapter_level(chapter_num)
                    return chapter_num, chapter_title, level

        return None, None, None

    def _extract_device_model(self, text: str) -> str | None:
        """
        从文本中提取设备型号
        Extract device model from text

        Args:
            text: 要搜索的文本 / Text to search

        Returns:
            设备型号，未找到则返回 None / Device model, or None if not found
        """
        return self._extract_with_patterns(text, self.device_model_patterns)

    def _is_spec_section(self, text: str) -> bool:
        """
        判断是否为技术参数段落
        Determine if the text is a technical specification section

        Args:
            text: 要检查的文本 / Text to check

        Returns:
            True 如果是技术参数段落 / True if it is a technical specification section
        """
        for keyword in self.spec_keywords:
            if keyword in text:
                return True
        return False

    def split(self, document: FastMeDocument) -> List[FastMeChunk]:
        """
        拆分手册文档为多个 chunk
        Split manual document into multiple chunks

        Args:
            document: FastMeDocument 实例 / FastMeDocument instance

        Returns:
            FastMeChunk 列表 / List of FastMeChunk
        """
        lines = document.text.splitlines()

        chapters: list[dict] = []
        current_chapter: dict = {
            "chapter_num": None,
            "chapter_title": None,
            "level": 1,
            "content": [],
            "device_model": None,
            "is_spec_section": False
        }

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # 检查是否是章节标题
            chapter_num, chapter_title, level = self._extract_chapter_title(line_stripped)

            if chapter_num is not None:
                # 保存当前章节
                if current_chapter["content"]:
                    chapters.append(current_chapter)

                # 开启新章节
                current_chapter = {
                    "chapter_num": chapter_num,
                    "chapter_title": chapter_title,
                    "level": level,
                    "content": [line_stripped],
                    "device_model": None,
                    "is_spec_section": self._is_spec_section(line_stripped)
                }

                # 尝试从章节标题附近提取设备型号
                device_model = self._extract_device_model(line_stripped)
                if device_model:
                    current_chapter["device_model"] = device_model
            else:
                # 非章节标题，归入当前章节内容
                current_chapter["content"].append(line_stripped)

                # 检查是否包含设备型号
                if not current_chapter["device_model"]:
                    device_model = self._extract_device_model(line_stripped)
                    if device_model:
                        current_chapter["device_model"] = device_model

                # 检查是否为技术参数段落
                if not current_chapter["is_spec_section"]:
                    current_chapter["is_spec_section"] = self._is_spec_section(line_stripped)

        # 保存最后一个章节
        if current_chapter["content"]:
            chapters.append(current_chapter)

        # 如果没有识别到章节，将整个文档作为一个 chunk
        if not chapters:
            chapters = [{
                "chapter_num": "1",
                "chapter_title": document.file_name,
                "level": 1,
                "content": lines,
                "device_model": None,
                "is_spec_section": False
            }]

        # 生成 chunks
        chunks: List[FastMeChunk] = []
        chunk_index = 0

        for chapter in chapters:
            # 使用基类方法拆分超大章节
            sub_chunks = self._split_by_paragraphs(chapter["content"])

            for sub_idx, sub_content in enumerate(sub_chunks):
                content_text = "\n".join(sub_content)

                # 使用基类方法生成 chunk_id
                sub_chunk_id = self._generate_chunk_id(
                    document.doc_id, chunk_index, len(sub_chunks), sub_idx
                )

                # 使用基类方法构建 metadata
                metadata = self._build_chunk_metadata(
                    document, sub_chunk_id, sub_chunks, sub_idx,
                    extra_metadata={
                        "chapter_num": chapter["chapter_num"],
                        "chapter_title": chapter["chapter_title"],
                        "chapter_level": chapter["level"],
                        "is_spec_section": chapter["is_spec_section"],
                    }
                )

                if chapter["device_model"]:
                    metadata["device_model"] = chapter["device_model"]

                chunks.append(FastMeChunk(
                    chunk_id=metadata["chunk_id"],
                    doc_id=metadata["doc_id"],
                    doc_type=metadata["doc_type"],
                    text=content_text,
                    metadata=metadata
                ))

                chunk_index += 1

        return chunks
