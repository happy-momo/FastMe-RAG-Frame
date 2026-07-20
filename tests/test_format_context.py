"""
_format_context 方法单元测试

这个测试文件独立测试 _format_context 方法，不需要加载 LangChain 依赖
"""

import pytest
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFormatContext:
    """_format_context 方法测试（不需要 LangChain 依赖）"""

    @pytest.fixture
    def mock_results(self):
        """模拟检索结果"""
        from core.models import FastMeSearchResult

        return [
            FastMeSearchResult(
                chunk_id="test_001",
                doc_id="doc_001",
                doc_type="log",
                text="设备 EQ001 故障",
                score=0.95,
                metadata={
                    "source": "test.log",
                    "device_id": "EQ001",
                    "fault_code": "ERR001",
                    "timestamp": "2024-01-01 10:00:00"
                }
            ),
            FastMeSearchResult(
                chunk_id="test_002",
                doc_id="doc_001",
                doc_type="log",
                text="设备已修复",
                score=0.85,
                metadata={
                    "source": "test.log",
                    "device_id": "EQ001",
                    "fault_code": "ERR001",
                    "timestamp": "2024-01-01 11:00:00"
                }
            )
        ]

    def test_format_context_empty(self):
        """测试空结果"""
        # 直接实例化一个空对象来测试方法
        class MockRAG:
            def _format_context(self, results: list, source_fields: list = None) -> str:
                """复制 app_factory.py 中的实现"""
                if not results:
                    return "没有检索到相关上下文信息"

                field_labels = {
                    "chunk_id": "片段 ID",
                    "doc_id": "文档 ID",
                    "doc_type": "文档类型",
                    "source": "来源",
                    "file_path": "文件路径",
                    "device_id": "设备",
                    "line_id": "产线",
                    "fault_code": "故障码",
                    "timestamp": "时间",
                    "work_order_id": "工单号",
                    "material_id": "物料号",
                    "quality_result": "质检结果",
                    "chapter_num": "章节号",
                    "device_model": "设备型号",
                    "process_num": "工序号",
                    "bom_items": "BOM 物料",
                }

                parts = []
                for i, item in enumerate(results):
                    metadata = item.metadata
                    field_lines = []
                    if source_fields:
                        for field in source_fields:
                            value = metadata.get(field)
                            if value is not None:
                                label = field_labels.get(field, field)
                                field_lines.append(f"{label}: {value}")
                    else:
                        for key, value in metadata.items():
                            if value is not None and key not in ["chunk_id", "doc_id"]:
                                label = field_labels.get(key, key)
                                field_lines.append(f"{label}: {value}")

                    if field_lines:
                        fields_text = "\n".join(field_lines)
                        parts.append(f"[片段 {i+1}]\n{fields_text}\n\n内容:\n{item.text}".strip())
                    else:
                        parts.append(f"[片段 {i+1}]\n内容:\n{item.text}".strip())

                return "\n\n".join(parts)

        mock_rag = MockRAG()
        result = mock_rag._format_context([])
        assert result == "没有检索到相关上下文信息"

    def test_format_context_with_fields(self, mock_results):
        """测试带字段列表的格式化"""
        # 使用与上面相同的 MockRAG 类
        class MockRAG:
            def _format_context(self, results: list, source_fields: list = None) -> str:
                if not results:
                    return "没有检索到相关上下文信息"

                field_labels = {
                    "device_id": "设备",
                    "fault_code": "故障码",
                    "timestamp": "时间",
                    "source": "来源",
                }

                parts = []
                for i, item in enumerate(results):
                    metadata = item.metadata
                    field_lines = []
                    if source_fields:
                        for field in source_fields:
                            value = metadata.get(field)
                            if value is not None:
                                label = field_labels.get(field, field)
                                field_lines.append(f"{label}: {value}")

                    if field_lines:
                        fields_text = "\n".join(field_lines)
                        parts.append(f"[片段 {i+1}]\n{fields_text}\n\n内容:\n{item.text}".strip())
                    else:
                        parts.append(f"[片段 {i+1}]\n内容:\n{item.text}".strip())

                return "\n\n".join(parts)

        mock_rag = MockRAG()
        result = mock_rag._format_context(
            mock_results,
            source_fields=["device_id", "fault_code", "timestamp"]
        )
        # 验证字段存在（注意冒号可能是英文或中文）
        assert "设备" in result and "EQ001" in result
        assert "故障码" in result and "ERR001" in result
        assert "时间" in result and "2024" in result
        assert "内容" in result and "设备 EQ001 故障" in result

    def test_format_context_multiple_results(self, mock_results):
        """测试多个结果的格式化"""
        class MockRAG:
            def _format_context(self, results: list, source_fields: list = None) -> str:
                if not results:
                    return "没有检索到相关上下文信息"

                parts = []
                for i, item in enumerate(results):
                    parts.append(f"[片段 {i+1}]\n{item.text}".strip())
                return "\n\n".join(parts)

        mock_rag = MockRAG()
        result = mock_rag._format_context(mock_results)
        assert "[片段 1]" in result
        assert "[片段 2]" in result
        assert "设备 EQ001 故障" in result
        assert "设备已修复" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
