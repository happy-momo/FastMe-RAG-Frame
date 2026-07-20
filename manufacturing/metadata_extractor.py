"""
制造业元数据抽取器
Manufacturing Metadata Extractor

从配置文件中加载正则规则，提取工业场景元数据字段。
Loads regex rules from configuration files and extracts industrial-scenario metadata fields.
"""

import re
import yaml
from pathlib import Path

from core.models import FastMeChunk


class IndustrialMetadataExtractor:
    """
    工业元数据提取器
    Industrial Metadata Extractor

    从配置文件中加载正则规则，提取以下元数据字段：
    Loads regex rules from configuration files and extracts the following metadata fields:
    - device_id: 设备 ID/设备编号 / Device ID
    - line_id: 产线 ID/线体编号 / Production line ID
    - fault_code: 故障码/告警码 / Fault code / Alarm code
    - work_order_id: 工单 ID/工单编号 / Work order ID
    - material_id: 物料 ID/物料编号 / Material ID

    将抽取的元数据更新到 FastMeChunk 的 metadata 字段中。
    Updates extracted metadata into the FastMeChunk metadata field.
    """

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "metadata_rules.yaml"

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 从配置加载规则，编译正则
        self.rules = {}
        self.compiled_patterns = {}

        for field, field_config in config.items():
            if isinstance(field_config, dict) and "patterns" in field_config:
                patterns = field_config["patterns"]
                self.rules[field] = patterns
                # 预编译正则，提升性能
                self.compiled_patterns[field] = [
                    re.compile(p) for p in patterns
                ]

    def extract_from_text(self, text: str) -> dict:
        """
        从文本中提取元数据
        Extract metadata from text

        Args:
            text: 待提取的文本内容 / Text content to extract from

        Returns:
            元数据字典 / Metadata dictionary
        """
        metadata = {}

        for field, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    metadata[field] = match.group(1)
                    break
        return metadata

    def enrich_chunk(self, chunks: list[FastMeChunk]) -> list[FastMeChunk]:
        """
        批量为 chunk 列表补充元数据
        Batch enrich chunk list with metadata

        Args:
            chunks: FastMeChunk 列表 / List of FastMeChunk objects

        Returns:
            原列表（已原地更新 metadata） / Original list with metadata updated in-place
        """
        for chunk in chunks:
            metadata = self.extract_from_text(chunk.text)
            chunk.metadata.update(metadata)
        return chunks

    def get_available_fields(self) -> list:
        """
        获取当前配置支持提取的字段列表
        Get list of fields supported by current configuration
        """
        return list(self.rules.keys())

    def add_metadata_rule(self, field: str, patterns: list, description: str = ""):
        """
        动态添加元数据抽取规则
        Dynamically add metadata extraction rule

        Args:
            field: 字段名称 / Field name
            patterns: 正则表达式列表 / List of regex patterns
            description: 字段描述（可选） / Field description (optional)
        """
        self.rules[field] = patterns
        self.compiled_patterns[field] = [re.compile(p) for p in patterns]
