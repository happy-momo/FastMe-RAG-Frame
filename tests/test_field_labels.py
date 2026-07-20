"""
field_labels 配置化单元测试

测试字段标签配置化功能，支持中英文切换
"""

import pytest
from pathlib import Path
import yaml


class TestFieldLabelsConfig:
    """field_labels.yaml 配置测试"""

    @pytest.fixture
    def field_labels_file(self):
        """获取配置文件路径"""
        return Path(__file__).parent.parent / "config" / "field_labels.yaml"

    @pytest.fixture
    def field_labels(self, field_labels_file):
        """加载配置文件"""
        with open(field_labels_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_config_file_exists(self, field_labels_file):
        """测试配置文件存在"""
        assert field_labels_file.exists(), f"Config file not found: {field_labels_file}"

    def test_config_has_languages(self, field_labels):
        """测试配置包含中英文"""
        assert "zh" in field_labels, "Missing Chinese (zh) configuration"
        assert "en" in field_labels, "Missing English (en) configuration"

    def test_zh_labels(self, field_labels):
        """测试中文字段标签"""
        zh = field_labels["zh"]
        assert zh.get("device_id") == "设备"
        assert zh.get("fault_code") == "故障码"
        assert zh.get("quality_result") == "质检结果"
        assert zh.get("no_results") == "没有检索到相关上下文信息"

    def test_en_labels(self, field_labels):
        """测试英文字段标签"""
        en = field_labels["en"]
        assert en.get("device_id") == "Device"
        assert en.get("fault_code") == "Fault Code"
        assert en.get("quality_result") == "Quality Result"
        assert en.get("no_results") == "No relevant context found"

    def test_all_fields_translated(self, field_labels):
        """测试所有字段都有中英文翻译"""
        zh = field_labels["zh"]
        en = field_labels["en"]

        # 检查中文有的字段，英文也有
        for key in zh.keys():
            assert key in en, f"Missing English translation for field: {key}"

        # 检查英文有的字段，中文也有
        for key in en.keys():
            assert key in zh, f"Missing Chinese translation for field: {key}"


class TestFieldLabelsUsage:
    """field_labels 使用测试（模拟实际使用场景）"""

    @pytest.fixture
    def mock_rag_zh(self):
        """模拟中文版 RAG"""
        from core.models import FastMeSearchResult

        class MockRAG:
            def __init__(self):
                self.language = "zh"
                self.field_labels = {
                    "device_id": "设备",
                    "fault_code": "故障码",
                    "no_results": "没有检索到相关上下文信息"
                }

            def _format_context(self, results: list, source_fields: list = None) -> str:
                if not results:
                    return self.field_labels.get("no_results", "No results")

                parts = []
                for i, item in enumerate(results):
                    field_lines = []
                    if source_fields:
                        for field in source_fields:
                            value = item.metadata.get(field)
                            if value is not None:
                                label = self.field_labels.get(field, field)
                                field_lines.append(f"{label}: {value}")

                    if field_lines:
                        parts.append(f"[片段 {i+1}]\n" + "\n".join(field_lines) + f"\n\n内容:\n{item.text}")
                    else:
                        parts.append(f"[片段 {i+1}]\n内容:\n{item.text}")

                return "\n\n".join(parts)

        return MockRAG()

    @pytest.fixture
    def mock_rag_en(self):
        """模拟英文版 RAG"""
        from core.models import FastMeSearchResult

        class MockRAG:
            def __init__(self):
                self.language = "en"
                self.field_labels = {
                    "device_id": "Device",
                    "fault_code": "Fault Code",
                    "no_results": "No relevant context found"
                }

            def _format_context(self, results: list, source_fields: list = None) -> str:
                if not results:
                    return self.field_labels.get("no_results", "No results")

                parts = []
                for i, item in enumerate(results):
                    field_lines = []
                    if source_fields:
                        for field in source_fields:
                            value = item.metadata.get(field)
                            if value is not None:
                                label = self.field_labels.get(field, field)
                                field_lines.append(f"{label}: {value}")

                    if field_lines:
                        parts.append(f"[Chunk {i+1}]\n" + "\n".join(field_lines) + f"\n\nContent:\n{item.text}")
                    else:
                        parts.append(f"[Chunk {i+1}]\nContent:\n{item.text}")

                return "\n\n".join(parts)

        return MockRAG()

    def test_chinese_format(self, mock_rag_zh):
        """测试中文版格式化"""
        from core.models import FastMeSearchResult

        results = [
            FastMeSearchResult(
                chunk_id="test_001",
                doc_id="doc_001",
                doc_type="log",
                text="设备故障",
                score=0.95,
                metadata={"device_id": "EQ001", "fault_code": "ERR001"}
            )
        ]

        result = mock_rag_zh._format_context(results, source_fields=["device_id", "fault_code"])

        # 验证字段存在（注意冒号可能是英文或中文）
        assert "设备" in result and "EQ001" in result
        assert "故障码" in result and "ERR001" in result

    def test_english_format(self, mock_rag_en):
        """测试英文版格式化"""
        from core.models import FastMeSearchResult

        results = [
            FastMeSearchResult(
                chunk_id="test_001",
                doc_id="doc_001",
                doc_type="log",
                text="Equipment fault",
                score=0.95,
                metadata={"device_id": "EQ001", "fault_code": "ERR001"}
            )
        ]

        result = mock_rag_en._format_context(results, source_fields=["device_id", "fault_code"])

        assert "Device: EQ001" in result
        assert "Fault Code: ERR001" in result

    def test_no_results_chinese(self, mock_rag_zh):
        """测试无结果提示（中文）"""
        result = mock_rag_zh._format_context([])
        assert result == "没有检索到相关上下文信息"

    def test_no_results_english(self, mock_rag_en):
        """测试无结果提示（英文）"""
        result = mock_rag_en._format_context([])
        assert result == "No relevant context found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
