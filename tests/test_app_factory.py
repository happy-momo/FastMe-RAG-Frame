"""
FastMe RAG 集成测试

注意：这些测试需要：
1. 有效的 LLM API 配置
2. HuggingFace Embedding 模型
3. Chroma 向量库

如果没有配置，可以跳过需要实际调用的测试。

运行测试:
    pytest tests/test_app_factory.py -v --skip-import-errors

如果遇到 ImportError (langchain-huggingface 版本问题)，请先升级依赖:
    pip install --upgrade langchain-huggingface langchain-core
"""

import pytest
import os
from pathlib import Path

# 检查是否有有效的 API 配置
@pytest.fixture(scope="session")
def has_llm_config():
    """检查是否有 LLM 配置"""
    llm_base_url = os.getenv("LLM_BASE_URL")
    llm_api_key = os.getenv("LLM_API_KEY")
    # 只要有配置就返回 True，不验证有效性
    return bool(llm_base_url and llm_api_key)


@pytest.fixture(scope="session")
def rag():
    """创建 FastMeRAG 实例"""
    try:
        from app_factory import FastMeRAG

        # 使用测试配置
        return FastMeRAG(
            chroma_dir="./data/chroma_test",
            chroma_collection="test_collection"
        )
    except ImportError as e:
        pytest.skip(f"无法导入 FastMeRAG: {e}")


class TestFormatContext:
    """PromptAdapter._format_context 方法测试（不需要 LLM 配置）"""

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

    @pytest.fixture
    def prompt_adapter(self):
        """创建 PromptAdapter 实例"""
        from adapters.prompt_adapter import PromptAdapter
        return PromptAdapter(
            path=Path(__file__).parent.parent / "config" / "prompt_templates.yaml",
            field_labels_path=Path(__file__).parent.parent / "config" / "field_labels.yaml"
        )

    def test_format_context_empty(self, prompt_adapter):
        """测试空结果"""
        result = prompt_adapter._format_context([])
        assert result == "没有检索到相关上下文信息"

    def test_format_context_with_fields(self, mock_results, prompt_adapter):
        """测试带字段列表的格式化"""
        result = prompt_adapter._format_context(
            mock_results,
            source_fields=["device_id", "fault_code", "timestamp"]
        )
        assert "设备: EQ001" in result
        assert "故障码: ERR001" in result
        assert "时间: 2024-01-01 10:00:00" in result
        assert "内容：\n设备 EQ001 故障" in result

    def test_format_context_different_fields(self, mock_results, prompt_adapter):
        """测试不同场景的字段格式化"""
        from core.models import FastMeSearchResult

        # 手册查询场景
        manual_results = [
            FastMeSearchResult(
                chunk_id="manual_001",
                doc_id="manual_001",
                doc_type="manual",
                text="设备操作步骤",
                score=0.95,
                metadata={
                    "source": "manual.pdf",
                    "chapter_num": "1",
                    "chapter_title": "设备概述",
                    "device_model": "EQ-1000"
                }
            )
        ]

        result = prompt_adapter._format_context(
            manual_results,
            source_fields=["chapter_num", "chapter_title", "device_model", "source"]
        )
        assert "章节号: 1" in result
        assert "章节标题: 设备概述" in result
        assert "设备型号: EQ-1000" in result
        assert "来源: manual.pdf" in result

    def test_format_context_no_fields(self, mock_results, prompt_adapter):
        """测试不指定字段列表（显示所有非空字段）"""
        result = prompt_adapter._format_context(mock_results, source_fields=None)
        # 应该显示所有非空字段
        assert "来源: test.log" in result
        assert "设备: EQ001" in result
        assert "内容：\n设备 EQ001 故障" in result

    def test_format_context_field_labels(self, mock_results, prompt_adapter):
        """测试字段中文映射"""
        result = prompt_adapter._format_context(
            mock_results,
            source_fields=["device_id", "fault_code", "timestamp", "source"]
        )
        assert "设备: " in result
        assert "故障码: " in result
        assert "时间: " in result
        assert "来源: " in result


class TestFastMeRAGInit:
    """FastMeRAG 初始化测试"""

    def test_init_default(self):
        """测试默认初始化"""
        try:
            from app_factory import FastMeRAG
        except ImportError as e:
            pytest.skip(f"无法导入 FastMeRAG: {e}")

        rag = FastMeRAG(
            chroma_dir="./data/chroma_test_init",
            chroma_collection="test_init"
        )
        assert rag is not None
        assert rag.vectorstore is not None
        assert rag.embeddings is not None
        assert rag.llm is not None

    def test_get_scenes(self, rag):
        """测试获取场景列表"""
        scenes = rag.get_scenes()
        assert isinstance(scenes, list)
        assert len(scenes) >= 4  # 至少 4 个场景
        assert "default" in scenes
        assert "fault_diagnosis" in scenes

    def test_get_doc_types(self, rag):
        """测试获取文档类型"""
        doc_types = rag.get_doc_types()
        assert isinstance(doc_types, list)
        assert "log" in doc_types
        assert "manual" in doc_types
        assert "business" in doc_types
        assert "sop" in doc_types

    def test_get_vector_count_empty(self, rag):
        """测试空向量库计数"""
        count = rag.get_vector_count()
        assert count >= 0  # 可能已有数据


class TestFastMeRAGIngest:
    """FastMeRAG 入库测试"""

    @pytest.fixture
    def sample_log_file(self, tmp_path):
        """创建临时日志文件"""
        log_file = tmp_path / "test.log"
        log_content = """2024-01-01 10:00:00
设备 EQ001 启动运行

2024-01-01 10:05:00
设备 EQ001 出现故障码 ERR001
"""
        log_file.write_text(log_content, encoding="utf-8")
        return str(log_file)

    def test_ingest_log(self, rag, sample_log_file):
        """测试日志入库"""
        result = rag.ingest(
            file_path=sample_log_file,
            doc_type="log",
            extra_metadata={"device_id": "EQ001"}
        )
        assert result["status"] == "success"
        assert "doc_id" in result
        assert result["chunks_count"] >= 1

    def test_ingest_require_review(self, rag, sample_log_file):
        """测试审核模式入库"""
        result = rag.ingest(
            file_path=sample_log_file,
            doc_type="log",
            require_review=True
        )
        assert result["status"] == "waiting_review"
        assert "chunks" in result
        assert len(result["chunks"]) >= 1


class TestFastMeRAGChat:
    """FastMeRAG 问答测试"""

    @pytest.mark.skipif(
        not os.getenv("LLM_BASE_URL"),
        reason="需要 LLM API 配置"
    )
    def test_chat_default(self, rag):
        """测试默认问答"""
        result = rag.chat(
            question="你好",
            scene="default"
        )
        assert "answer" in result
        assert "sources" in result
        assert isinstance(result["sources"], list)

    @pytest.mark.skipif(
        not os.getenv("LLM_BASE_URL"),
        reason="需要 LLM API 配置"
    )
    def test_chat_fault_diagnosis(self, rag):
        """测试故障诊断场景问答"""
        result = rag.chat(
            question="设备故障怎么处理？",
            scene="fault_diagnosis"
        )
        assert "answer" in result
        assert result["scene"] == "fault_diagnosis"

    def test_chat_stream(self, rag):
        """测试流式问答（不验证内容，只验证能生成）"""
        chunks = list(rag.chat_stream(
            question="测试",
            scene="default"
        ))
        # 不验证内容，因为可能需要 LLM
        assert isinstance(chunks, list)


class TestFastMeRAGConfig:
    """FastMeRAG 配置测试"""

    def test_add_scene(self, rag):
        """测试添加场景"""
        rag.add_scene(
            name="test_scene",
            doc_type="manual",
            prompt_template="default",
            description="测试场景"
        )
        scenes = rag.get_scenes()
        assert "test_scene" in scenes

    def test_add_metadata_rule(self, rag):
        """测试添加元数据规则"""
        rag.add_metadata_rule(
            field="test_field",
            patterns=[r"测试 [::\s]*([A-Za-z0-9]+)"]
        )
        # 验证规则已添加
        assert "test_field" in rag.metadata_extractor.rules

    def test_update_scene_top_k(self, rag):
        """测试更新场景 top_k"""
        original_top_k = rag.scene_router.scene_config["fault_diagnosis"]["top_k"]
        rag.update_scene_top_k("fault_diagnosis", 10)
        new_top_k = rag.scene_router.scene_config["fault_diagnosis"]["top_k"]
        assert new_top_k == 10
        # 恢复原值
        rag.update_scene_top_k("fault_diagnosis", original_top_k)


class TestFastMeRAGMemory:
    """FastMeRAG 记忆测试"""

    def test_create_memory(self, rag):
        """测试创建记忆"""
        rag.create_memory("test_session")
        memory = rag.get_memory("test_session")
        assert memory is not None

    def test_clear_memory(self, rag):
        """测试清除记忆"""
        rag.create_memory("test_session")
        rag.clear_memory("test_session")
        memory = rag.get_memory("test_session")
        assert memory is None

    @pytest.mark.skipif(
        not os.getenv("LLM_BASE_URL"),
        reason="需要 LLM API 配置"
    )
    def test_chat_with_memory(self, rag):
        """测试带记忆的对话"""
        # 第一轮
        result1 = rag.chat_with_memory(
            question="我叫张三",
            session_id="test_session",
            scene="default"
        )
        assert "answer" in result1

        # 第二轮 - 应该能记住名字
        result2 = rag.chat_with_memory(
            question="我叫什么名字？",
            session_id="test_session",
            scene="default"
        )
        assert "answer" in result2
        # 理论上答案应该包含"张三"，但取决于 LLM


class TestFastMeRAGBatchIngest:
    """FastMeRAG 批量入库测试"""

    @pytest.fixture
    def sample_folder(self, tmp_path):
        """创建临时文件夹"""
        folder = tmp_path / "test_docs"
        folder.mkdir()

        # 创建测试文件
        (folder / "doc1.log").write_text(
            "2024-01-01 10:00:00\n设备 EQ001 运行",
            encoding="utf-8"
        )
        (folder / "doc2.log").write_text(
            "2024-01-01 11:00:00\n设备 EQ002 运行",
            encoding="utf-8"
        )
        (folder / "doc3.txt").write_text(
            "普通文本",
            encoding="utf-8"
        )

        return str(folder)

    def test_batch_ingest(self, rag, sample_folder):
        """测试批量入库"""
        results = rag.batch_ingest(
            folder_path=sample_folder,
            doc_type="log",
            file_extensions=[".log"]
        )
        assert len(results) == 2  # 2 个.log 文件
        success_count = sum(1 for r in results if r["status"] == "success")
        assert success_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
