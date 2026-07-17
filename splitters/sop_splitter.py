import re
from typing import List

from core.models import FastMeDocument, FastMeChunk
from splitters.base import BaseSplitter


class SopSplitter(BaseSplitter):
    """
    工艺拆解器
    SOP (Standard Operating Procedure) Splitter

    适用于：工艺 SOP、作业指导书、BOM 文档等
    Applicable to: process SOPs, work instructions, BOM documents

    拆解规则：
    Splitting rules:
    1. 识别工序编号体系（工序 1→工序 2 或 Step1→Step2）
       Identify process step numbering (工序 1→工序 2 or Step1→Step2)
    2. 按工序分块，每个工序独立 chunk
       Split by process step; each step becomes an independent chunk
    3. 上下工序上下文绑定：当前 chunk 携带前一步骤摘要
       Bind context across steps: current chunk carries the previous step summary
    4. BOM 物料清单单独抽取为附属标签
       Extract BOM material lists as auxiliary tags

    尺寸限制：
    Size limits:
    - 单个 chunk 最大字符数：max_chunk_size (默认 1000 字)
      Max characters per chunk: max_chunk_size (default 1000)
    - 超大工序会自动拆分为多个 sub-chunks
      Oversized process steps are automatically split into sub-chunks

    Args:
        max_chunk_size: 单个 chunk 最大字符数，默认 1000 / Max characters per chunk, default 1000

    Example:
        >>> splitter = SopSplitter()  # 默认 1000 字 / Default 1000 chars
        >>> splitter = SopSplitter(max_chunk_size=1200)  # 自定义 1200 字 / Custom 1200 chars
    """

    def __init__(self, max_chunk_size: int = 1000):
        # 调用基类构造函数
        super().__init__(max_chunk_size)
        # 工序编号匹配模式
        self.process_patterns = [
            # 工序 X、第 X 工序
            re.compile(r"^工序 ([一二三四五六七八九十\d]+)[：:\s]*(.*)$"),
            re.compile(r"^第\s*([一二三四五六七八九十\d]+)\s*道工序[：:\s]*(.*)$"),
            # Step 1, Stage 1
            re.compile(r"^(?:Step|Stage)\s*(\d+)[.:]?\s*(.*)$", re.IGNORECASE),
            # 数字编号：1.、1,
            re.compile(r"^(\d+)[.、:]\s*(.*)$"),
            # 作业步骤
            re.compile(r"^作业步骤 ([一二三四五六七八九十\d]+)[：:\s]*(.*)$"),
        ]

        # BOM 物料匹配模式
        self.bom_patterns = [
            re.compile(r"BOM[：:\s]*(.+)"),
            re.compile(r"物料清单[：:\s]*(.+)"),
            re.compile(r"物料编号[：:\s]*([A-Za-z0-9\-_]+)"),
            re.compile(r"零件编号[：:\s]*([A-Za-z0-9\-_]+)"),
        ]

        # 材料/原料匹配
        self.material_patterns = [
            re.compile(r"材料[：:\s]*([A-Za-z0-9一-龥\-_]+)"),
            re.compile(r"原料[：:\s]*([A-Za-z0-9一-龥\-_]+)"),
            re.compile(r"材质[：:\s]*([A-Za-z0-9一-龥\-_]+)"),
        ]

        # 工具/设备匹配
        self.tool_patterns = [
            re.compile(r"工具[：:\s]*([A-Za-z0-9一-龥\-_]+)"),
            re.compile(r"设备[：:\s]*([A-Za-z0-9一-龥\-_]+)"),
            re.compile(r"仪器[：:\s]*([A-Za-z0-9一-龥\-_]+)"),
        ]

        # 工艺参数匹配
        self.param_patterns = [
            re.compile(r"温度[：:\s]*(\d+(?:\.\d+)?\s*(?:°C|°F|°K|C|F|K)?)"),
            re.compile(r"压力[：:\s]*(\d+(?:\.\d+)?\s*(?:MPa|kPa|Bar|psi)?)"),
            re.compile(r"速度[：:\s]*(\d+(?:\.\d+)?\s*(?:m/s|mm/s|rpm)?)"),
            re.compile(r"时间[：:\s]*(\d+(?:\.\d+)?\s*(?:小时|分钟|秒|min|h|s)?)"),
        ]

    def _extract_process_num(self, line: str) -> tuple:
        """
        从一行中提取工序编号和标题
        Extract process step number and title from a line

        Returns:
            (process_num_str, process_title) 或 (None, None) / (process_num_str, process_title) or (None, None)
        """
        line = line.strip()
        if not line:
            return None, None

        for pattern in self.process_patterns:
            match = pattern.match(line)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    return groups[0], groups[1].strip()
                elif len(groups) == 1:
                    return groups[0], ""
        return None, None

    def _extract_bom_items(self, text: str) -> List[str]:
        """
        从文本中提取 BOM 物料项
        Extract BOM material items from text

        Args:
            text: 要搜索的文本 / Text to search

        Returns:
            BOM 物料项列表 / List of BOM material items
        """
        results = self._extract_with_patterns(text, self.bom_patterns, findall=True)
        return [r.strip() for r in results] if results else []

    def _extract_materials(self, text: str) -> list[str]:
        """
        从文本中提取材料信息
        Extract material information from text

        Args:
            text: 要搜索的文本 / Text to search

        Returns:
            材料信息列表 / List of material information
        """
        results = self._extract_with_patterns(text, self.material_patterns, findall=True)
        return [m.strip() for m in results] if results else []

    def _extract_tools(self, text: str) -> list[str]:
        """
        从文本中提取工具/设备信息
        Extract tool/equipment information from text

        Args:
            text: 要搜索的文本 / Text to search

        Returns:
            工具/设备信息列表 / List of tool/equipment information
        """
        results = self._extract_with_patterns(text, self.tool_patterns, findall=True)
        return [t.strip() for t in results] if results else []

    def _extract_params(self, text: str) -> dict:
        """
        从文本中提取工艺参数
        Extract process parameters from text

        Args:
            text: 要搜索的文本 / Text to search

        Returns:
            工艺参数字典（temperature, pressure, speed, time 等）/ Process parameter dict (temperature, pressure, speed, time, etc.)
        """
        params = {}

        # 温度
        for pattern in self.param_patterns:
            if "温度" in pattern.pattern:
                matches = pattern.findall(text)
                if matches:
                    params["temperature"] = matches[0]
            elif "压力" in pattern.pattern:
                matches = pattern.findall(text)
                if matches:
                    params["pressure"] = matches[0]
            elif "速度" in pattern.pattern:
                matches = pattern.findall(text)
                if matches:
                    params["speed"] = matches[0]
            elif "时间" in pattern.pattern:
                matches = pattern.findall(text)
                if matches:
                    params["time"] = matches[0]

        return params

    def _summarize_process(self, content: list[str], max_length: int = 50) -> str:
        """
        生成工序摘要
        Generate a summary of the process step

        Args:
            content: 工序内容行列表 / List of process step content lines
            max_length: 摘要最大长度 / Maximum summary length

        Returns:
            工序摘要文本 / Process step summary text
        """
        text = " ".join(content)
        # 提取关键动词或操作
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def split(self, document: FastMeDocument) -> list[FastMeChunk]:
        """
        拆分 SOP 文档为多个 chunk
        Split SOP document into multiple chunks

        Args:
            document: FastMeDocument 实例 / FastMeDocument instance

        Returns:
            FastMeChunk 列表 / List of FastMeChunk
        """
        lines = document.text.splitlines()

        processes: list[dict] = []
        current_process: dict = {
            "process_num": None,
            "process_title": None,
            "content": [],
            "bom_items": [],
            "materials": [],
            "tools": [],
            "params": {}
        }

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # 检查是否是工序标题
            process_num, process_title = self._extract_process_num(line_stripped)

            if process_num is not None:
                # 保存当前工序
                if current_process["content"]:
                    processes.append(current_process)

                # 开启新工序
                current_process = {
                    "process_num": process_num,
                    "process_title": process_title,
                    "content": [line_stripped],
                    "bom_items": [],
                    "materials": [],
                    "tools": [],
                    "params": {}
                }
            else:
                # 非工序标题，归入当前工序内容
                current_process["content"].append(line_stripped)

        # 保存最后一个工序
        if current_process["content"]:
            processes.append(current_process)

        # 如果没有识别到工序，将整个文档作为一个 chunk
        if not processes:
            processes = [{
                "process_num": "1",
                "process_title": "作业步骤",
                "content": lines,
                "bom_items": [],
                "materials": [],
                "tools": [],
                "params": {}
            }]

        # 为每个工序提取元数据并生成 chunks
        chunks: List[FastMeChunk] = []
        chunk_index = 0
        prev_process_summary = None

        for process in processes:
            # 使用基类方法拆分超大工序
            sub_chunks = self._split_by_paragraphs(process["content"])

            for sub_idx, sub_content in enumerate(sub_chunks):
                content_text = "\n".join(sub_content)
                full_text = content_text

                # 提取 BOM 物料（只在第一个 sub-chunk 中提取一次）
                bom_items = []
                materials = []
                tools = []
                params = {}

                if sub_idx == 0:
                    bom_items = self._extract_bom_items(full_text)
                    if not bom_items:
                        bom_items = self._extract_bom_items(document.text)
                    materials = self._extract_materials(full_text)
                    tools = self._extract_tools(full_text)
                    params = self._extract_params(full_text)

                # 使用基类方法生成 chunk_id
                sub_chunk_id = self._generate_chunk_id(
                    document.doc_id, chunk_index, len(sub_chunks), sub_idx
                )

                # 使用基类方法构建 metadata
                metadata = self._build_chunk_metadata(
                    document, sub_chunk_id, sub_chunks, sub_idx,
                    extra_metadata={
                        "process_num": process["process_num"],
                        "process_title": process["process_title"],
                        "bom_items": ",".join(bom_items) if bom_items else None,
                        "materials": ",".join(materials) if materials else None,
                        "tools": ",".join(tools) if tools else None,
                        "prev_process_summary": prev_process_summary,
                    }
                )

                # 添加工艺参数
                for param_name, param_value in params.items():
                    metadata[f"param_{param_name}"] = param_value

                # 生成当前工序摘要，供下一个工序使用（只在最后一个 sub-chunk 更新）
                if sub_idx == len(sub_chunks) - 1:
                    prev_process_summary = self._summarize_process(process["content"])

                chunks.append(FastMeChunk(
                    chunk_id=metadata["chunk_id"],
                    doc_id=metadata["doc_id"],
                    doc_type=metadata["doc_type"],
                    text=content_text,
                    metadata=metadata
                ))

                chunk_index += 1

        return chunks
