"""
IndustrialMetadataExtractor 单元测试
"""

import pytest
from pathlib import Path

from manufacturing.metadata_extractor import IndustrialMetadataExtractor


class TestIndustrialMetadataExtractor:
    """IndustrialMetadataExtractor 测试类"""

    @pytest.fixture
    def extractor(self):
        """创建元数据抽取器实例"""
        config_path = Path(__file__).parent.parent / "config" / "metadata_rules.yaml"
        return IndustrialMetadataExtractor(config_path=str(config_path))

    def test_extract_device_id(self, extractor):
        """测试设备 ID 抽取"""
        text = "设备 ID: EQ001 发生故障"
        metadata = extractor.extract_from_text(text)
        assert "device_id" in metadata
        assert metadata["device_id"] == "EQ001"

    def test_extract_device_id_alt_format(self, extractor):
        """测试设备 ID  alternate 格式抽取"""
        text = "设备编号 EQ-002 的维修记录"
        metadata = extractor.extract_from_text(text)
        assert "device_id" in metadata
        assert metadata["device_id"] == "EQ-002"

    def test_extract_line_id(self, extractor):
        """测试产线 ID 抽取"""
        text = "产线：LN01 的生产记录"
        metadata = extractor.extract_from_text(text)
        assert "line_id" in metadata
        assert metadata["line_id"] == "LN01"

    def test_extract_fault_code(self, extractor):
        """测试故障码抽取"""
        text = "故障码 ERR123 出现 3 次"
        metadata = extractor.extract_from_text(text)
        assert "fault_code" in metadata
        assert metadata["fault_code"] == "ERR123"

    def test_extract_work_order_id(self, extractor):
        """测试工单号抽取"""
        text = "工单 ID: WO-2024001 已完成"
        metadata = extractor.extract_from_text(text)
        assert "work_order_id" in metadata
        assert metadata["work_order_id"] == "WO-2024001"

    def test_extract_material_id(self, extractor):
        """测试物料号抽取"""
        text = "物料 ID: MT001 已入库"
        metadata = extractor.extract_from_text(text)
        assert "material_id" in metadata
        assert metadata["material_id"] == "MT001"

    def test_extract_multiple_fields(self, extractor):
        """测试多字段同时抽取"""
        text = "设备 EQ001 在产线 LN01 上出现故障码 ERR999"
        metadata = extractor.extract_from_text(text)
        assert metadata.get("device_id") == "EQ001"
        assert metadata.get("line_id") == "LN01"
        assert metadata.get("fault_code") == "ERR999"

    def test_extract_no_match(self, extractor):
        """测试无匹配情况"""
        text = "这是一段普通文本，没有工业元数据"
        metadata = extractor.extract_from_text(text)
        assert metadata == {}

    def test_get_available_fields(self, extractor):
        """测试获取可用字段列表"""
        fields = extractor.get_available_fields()
        assert isinstance(fields, list)
        assert len(fields) > 0
        assert "device_id" in fields
        assert "line_id" in fields
        assert "fault_code" in fields

    def test_add_metadata_rule(self, extractor):
        """测试动态添加规则"""
        extractor.add_metadata_rule(
            field="test_field",
            patterns=[r"测试字段.*?([A-Za-z0-9]+)"]  # 使用.*?匹配任意字符（包括中文冒号）
        )
        text = "测试字段：TEST123"
        metadata = extractor.extract_from_text(text)
        assert "test_field" in metadata
        assert metadata["test_field"] == "TEST123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
