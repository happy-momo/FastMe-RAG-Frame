import re
from typing import List

from core.models import FastMeDocument, FastMeChunk
from splitters.base import BaseSplitter


class BusinessSplitter(BaseSplitter):
    """
    工单拆解器
    Business (Work Order) Splitter

    适用于：车间业务文档、工单、质检单、生产记录等文档
    Applicable to: workshop business documents, work orders, quality inspection records, production logs

    拆解规则：
    Splitting rules:
    1. 识别工单编号字段（工单号、WO-、WO#等模式）
       Identify work order ID fields (order number, WO-, WO# patterns)
    2. 按工单编号分块，每个工单独立 chunk
       Split by work order ID; each order becomes an independent chunk
    3. 提取表格字段：产线、工位、工序、物料号、质检结果
       Extract table fields: production line, station, process, material ID, quality result
    4. 表格每行作为子 chunk，关联父工单
       Each table row as a sub-chunk, linked to the parent work order

    尺寸限制：
    Size limits:
    - 单个 chunk 最大字符数：max_chunk_size (默认 1000 字)
      Max characters per chunk: max_chunk_size (default 1000)
    - 超大工单会自动拆分为多个 sub-chunks
      Oversized work orders are automatically split into sub-chunks

    Args:
        max_chunk_size: 单个 chunk 最大字符数，默认 1000 / Max characters per chunk, default 1000

    Example:
        >>> splitter = BusinessSplitter()  # 默认 1000 字 / Default 1000 chars
        >>> splitter = BusinessSplitter(max_chunk_size=800)  # 自定义 800 字 / Custom 800 chars
    """

    def __init__(self, max_chunk_size: int = 1000):
        # 调用基类构造函数
        super().__init__(max_chunk_size)
        # 工单编号匹配模式
        self.work_order_patterns = [
            # 工单 ID/工单编号
            re.compile(r"工单 (?:ID|编号)?[：:\s]*([A-Za-z0-9\-_]+)"),
            # WO-xxx、WO#xxx、WOxxx
            re.compile(r"\b(WO[-_#]?\d{3,})\b", re.IGNORECASE),
            # 生产批号
            re.compile(r"生产批 (?:号)?[：:\s]*([A-Za-z0-9\-_]+)"),
            # 订单号
            re.compile(r"订单 (?:号)?[：:\s]*([A-Za-z0-9\-_]+)"),
        ]

        # 产线匹配模式
        self.line_patterns = [
            re.compile(r"产线 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"生产线 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"线体 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"\b(LN[-_]?\d{3,})\b", re.IGNORECASE),
        ]

        # 工位匹配模式
        self.station_patterns = [
            re.compile(r"工位 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"工站 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"站点 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"Station[：:\s]*([A-Za-z0-9\-_]+)", re.IGNORECASE),
        ]

        # 工序匹配模式
        self.process_patterns = [
            re.compile(r"工序 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"工艺 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"制程 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"工序编号 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"第 ([一二三四五六七八九十\d]+) 道工序"),
        ]

        # 物料号匹配模式
        self.material_patterns = [
            re.compile(r"物料 (?:ID|编号 | 号)?[：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"物料编码 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"零件号 [：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"\b(MT[-_]?\d{3,})\b", re.IGNORECASE),
            re.compile(r"\b(MAT[-_]?\d{3,})\b", re.IGNORECASE),
        ]

        # 质检结果匹配模式
        self.quality_patterns = [
            re.compile(r"质检结果[：:\s]*(合格|不合格|良品|不良品|OK|NG)"),
            re.compile(r"检验结果[：:\s]*(合格|不合格|良品|不良品|OK|NG)"),
            re.compile(r"判定结果[：:\s]*(合格|不合格|良品|不良品|OK|NG)"),
            re.compile(r"质量状态[：:\s]*(合格|不合格|良品|不良品|OK|NG)"),
        ]

    def _extract_field(self, text: str, patterns: list) -> str | None:
        """
        使用多个正则模式提取字段
        Extract a field using multiple regex patterns

        Args:
            text: 要搜索的文本 / Text to search
            patterns: 正则模式列表 / List of regex patterns

        Returns:
            提取的字段值，未找到则返回 None / Extracted field value, or None if not found
        """
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1)
        return None

    def _split_by_work_order(self, text: str) -> List[dict]:
        """
        按工单分割文本
        Split text by work orders

        Returns:
            工单列表，每个工单包含 work_order_id 和 content / List of work orders, each containing work_order_id and content
        """
        lines = text.splitlines()
        work_orders = []
        current_order = {
            "work_order_id": None,
            "content": [],
            "start_line": 0
        }

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # 尝试从当前行提取工单号
            work_order_id = None
            for pattern in self.work_order_patterns:
                match = pattern.search(line_stripped)
                if match:
                    work_order_id = match.group(1)
                    break

            if work_order_id and current_order["content"]:
                # 发现新工单，保存当前工单
                work_orders.append(current_order)
                current_order = {
                    "work_order_id": work_order_id,
                    "content": [line_stripped],
                    "start_line": i
                }
            elif work_order_id and not current_order["work_order_id"]:
                # 第一个工单
                current_order["work_order_id"] = work_order_id
                current_order["content"].append(line_stripped)
            else:
                # 归入当前工单
                current_order["content"].append(line_stripped)

        # 保存最后一个工单
        if current_order["content"]:
            work_orders.append(current_order)

        return work_orders

    def _extract_metadata(self, content: list[str]) -> dict:
        """
        从工单内容中提取元数据
        Extract metadata from work order content

        Args:
            content: 工单内容行列表 / List of work order content lines

        Returns:
            元数据字典，包含 line_id, station, process 等字段 / Metadata dict with line_id, station, process, etc.
        """
        full_text = "\n".join(content)
        metadata = {}

        metadata["line_id"] = self._extract_field(full_text, self.line_patterns)
        metadata["station"] = self._extract_field(full_text, self.station_patterns)
        metadata["process"] = self._extract_field(full_text, self.process_patterns)
        metadata["material_id"] = self._extract_field(full_text, self.material_patterns)

        quality_result = self._extract_field(full_text, self.quality_patterns)
        if quality_result:
            # 统一中文输出
            quality_map = {
                "OK": "合格",
                "NG": "不合格",
                "合格": "合格",
                "不合格": "不合格",
                "良品": "合格",
                "不良品": "不合格"
            }
            metadata["quality_result"] = quality_map.get(quality_result, quality_result)

        return metadata

    def split(self, document: FastMeDocument) -> list[FastMeChunk]:
        """
        拆分工单文档为多个 chunk
        Split business document into multiple chunks

        Args:
            document: FastMeDocument 实例 / FastMeDocument instance

        Returns:
            FastMeChunk 列表 / List of FastMeChunk
        """
        work_orders = self._split_by_work_order(document.text)

        # 如果没有识别到工单，将整个文档作为一个 chunk
        if not work_orders:
            work_orders = [{
                "work_order_id": f"UNKNOWN_{document.doc_id}",
                "content": document.text.splitlines(),
                "start_line": 0
            }]

        # 生成 chunks
        chunks: List[FastMeChunk] = []
        chunk_index = 0

        for order in work_orders:
            # 使用基类方法拆分超大工单
            sub_chunks = self._split_by_paragraphs(order["content"])

            for sub_idx, sub_content in enumerate(sub_chunks):
                content_text = "\n".join(sub_content)
                extra_metadata = self._extract_metadata(sub_content)

                # 使用基类方法生成 chunk_id
                sub_chunk_id = self._generate_chunk_id(
                    document.doc_id, chunk_index, len(sub_chunks), sub_idx
                )

                # 使用基类方法构建 metadata
                metadata = self._build_chunk_metadata(
                    document, sub_chunk_id, sub_chunks, sub_idx,
                    extra_metadata={
                        "work_order_id": order["work_order_id"],
                        **extra_metadata
                    }
                )

                chunks.append(FastMeChunk(
                    chunk_id=metadata["chunk_id"],
                    doc_id=metadata["doc_id"],
                    doc_type=metadata["doc_type"],
                    text=content_text,
                    metadata=metadata
                ))

                chunk_index += 1

        return chunks
