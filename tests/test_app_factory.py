"""
FastMe RAG 集成测试
FastMe RAG Integration Tests

注意：这些测试需要：
Note: These tests require:
1. 有效的 LLM API 配置 / Valid LLM API configuration
2. HuggingFace Embedding 模型 / HuggingFace Embedding model
3. Chroma 向量库 / Chroma vector store

如果没有配置，可以跳过需要实际调用的测试。
If not configured, tests requiring actual calls can be skipped.

运行测试 / Run tests:
    pytest tests/test_app_factory.py -v --skip-import-errors

如果遇到 ImportError (langchain-huggingface 版本问题)，请先升级依赖：
If encountering ImportError (langchain-huggingface version issue), upgrade dependencies first:
    pip install --upgrade langchain-huggingface langchain-core
"""

import pytest
import os
import tempfile
from pathlib import Path

# 检查是否有有效的 API 配置 / Check if valid API configuration exists
@pytest.fixture(scope="session")
def has_llm_config():
    """
    检查是否有 LLM 配置
    Check if LLM configuration exists
    """
    llm_base_url = os.getenv("LLM_BASE_URL")
    llm_api_key = os.getenv("LLM_API_KEY")
    # 只要有配置就返回 True，不验证有效性
    # Return True if configuration exists, don't validate
    return bool(llm_base_url and llm_api_key)


@pytest.fixture(scope="session")
def rag():
    """
    创建 FastMeRAG 实例
    Create FastMeRAG instance
    """
    try:
        from app_factory import FastMeRAG

        # 使用配置字典初始化（新方式）
        # Initialize with config dictionary (new way)
        return FastMeRAG(config={
            "vector_store": {
                "type": "chroma",
                "config": {
                    "persist_directory": "./data/chroma_test",
                    "collection_name": "test_collection"
                }
            },
            "embedding": {"model_name": "BAAI/bge-m3"},
            "llm": {"model_name": "qwen-plus"}
        })
    except ImportError as e:
        pytest.skip(f"无法导入 FastMeRAG: {e}")


class TestFastMeRAGFromConfig:
    """
    FastMeRAG 配置加载测试
    FastMeRAG configuration loading tests
    """

    def test_from_config_yaml(self):
        """
        测试从 YAML 配置文件加载
        Test loading from YAML config file
        """
        from app_factory import FastMeRAG

        config_content = """
vector_store:
  type: chroma
  config:
    persist_directory: ./data/chroma_test_yaml
    collection_name: test_yaml_coll
embedding:
  model_name: BAAI/bge-m3
llm:
  model_name: qwen-plus
"""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w', encoding='utf-8') as f:
            f.write(config_content)
            f.flush()

            rag = FastMeRAG.from_config(f.name)

            assert rag.config['vector_store']['type'] == 'chroma'
            assert rag.config['vector_store']['config']['collection_name'] == 'test_yaml_coll'

            Path(f.name).unlink()

    def test_from_config_dict(self):
        """
        测试从配置字典加载
        Test loading from config dictionary
        """
        from app_factory import FastMeRAG

        rag = FastMeRAG(config={
            "vector_store": {
                "type": "chroma",
                "config": {
                    "persist_directory": "./data/chroma_test_dict",
                    "collection_name": "test_dict_coll"
                }
            },
            "embedding": {"model_name": "BAAI/bge-m3"},
            "llm": {"model_name": "qwen-plus"}
        })

        assert rag.config['vector_store']['type'] == 'chroma'
        assert rag.config['vector_store']['config']['collection_name'] == 'test_dict_coll'

    def test_from_config_with_overrides(self):
        """
        测试从配置加载并覆盖
        Test loading from config with overrides
        """
        from app_factory import FastMeRAG

        config_content = """
vector_store:
  type: chroma
  config:
    persist_directory: ./data/chroma_test_override
    collection_name: original_coll
embedding:
  model_name: BAAI/bge-m3
llm:
  model_name: qwen-plus
"""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w', encoding='utf-8') as f:
            f.write(config_content)
            f.flush()

            rag = FastMeRAG.from_config(
                f.name,
                overrides={"vector_store": {"config": {"collection_name": "overridden_coll"}}}
            )

            assert rag.config['vector_store']['config']['collection_name'] == 'overridden_coll'

            Path(f.name).unlink()

    def test_from_config_faiss(self):
        """
        测试从 FAISS 配置加载
        Test loading from FAISS config
        """
        from app_factory import FastMeRAG

        config_content = """
vector_store:
  type: faiss
  config:
    index_path: ./data/faiss_test_config
embedding:
  model_name: BAAI/bge-m3
llm:
  model_name: qwen-plus
"""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w', encoding='utf-8') as f:
            f.write(config_content)
            f.flush()

            rag = FastMeRAG.from_config(f.name)

            assert rag.config['vector_store']['type'] == 'faiss'
            assert rag.config['vector_store']['config']['index_path'] == './data/faiss_test_config'

            Path(f.name).unlink()


class TestChunkingConfig:
    """
    Chunking 配置测试
    Chunking configuration tests
    """

    def test_chunking_by_type(self):
        """
        测试按类型配置 chunk 大小
        Test chunk size configuration by type
        """
        from app_factory import FastMeRAG

        config_content = """
vector_store:
  type: chroma
  config:
    persist_directory: ./data/chroma_test_chunk
    collection_name: test_chunk_coll
embedding:
  model_name: BAAI/bge-m3
llm:
  model_name: qwen-plus
chunking:
  default_max_size: 1000
  by_type:
    log: 500
    manual: 1500
"""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w', encoding='utf-8') as f:
            f.write(config_content)
            f.flush()

            rag = FastMeRAG.from_config(f.name)

            # 验证 splitter 使用了正确的 chunk 大小
            # Verify splitter uses correct chunk size
            log_splitter = rag.splitter_registry.get("log")
            manual_splitter = rag.splitter_registry.get("manual")

            assert log_splitter.max_chunk_size == 500
            assert manual_splitter.max_chunk_size == 1500

            Path(f.name).unlink()

    def test_chunking_default_values(self):
        """
        测试使用 Splitter 类默认值
        Test using Splitter class default values
        """
        from app_factory import FastMeRAG

        # 不配置 chunking，使用各 splitter 的默认值
        # No chunking config, use each splitter's default
        rag = FastMeRAG(config={
            "vector_store": {
                "type": "chroma",
                "config": {"persist_directory": "./data/chroma_test_default_chunk"}
            },
            "embedding": {"model_name": "BAAI/bge-m3"},
            "llm": {"model_name": "qwen-plus"}
        })

        # 验证使用 Splitter 类的 DEFAULT_MAX_CHUNK_SIZE
        # Verify using Splitter class DEFAULT_MAX_CHUNK_SIZE
        from splitters.log_splitter import LogSplitter
        from splitters.manual_splitter import ManualSplitter

        log_splitter = rag.splitter_registry.get("log")
        manual_splitter = rag.splitter_registry.get("manual")

        assert log_splitter.max_chunk_size == LogSplitter.DEFAULT_MAX_CHUNK_SIZE
        assert manual_splitter.max_chunk_size == ManualSplitter.DEFAULT_MAX_CHUNK_SIZE


class TestFormatContext:
    """
    PromptAdapter._format_context 方法测试（不需要 LLM 配置）
    PromptAdapter._format_context method tests (no LLM config needed)
    """

    @pytest.fixture
    def mock_results(self):
        """模拟检索结果 / Mock search results"""
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
        """创建 PromptAdapter 实例 / Create PromptAdapter instance"""
        from adapters.prompt_adapter import PromptAdapter
        return PromptAdapter(
            path=Path(__file__).parent.parent / "config" / "prompt_templates.yaml",
            field_labels_path=Path(__file__).parent.parent / "config" / "field_labels.yaml"
        )

    def test_format_context_empty(self, prompt_adapter):
        """测试空结果 / Test empty results"""
        result = prompt_adapter._format_context([])
        assert result == "没有检索到相关上下文信息"

    def test_format_context_with_fields(self, mock_results, prompt_adapter):
        """测试带字段列表的格式化 / Test formatting with field list"""
        result = prompt_adapter._format_context(
            mock_results,
            source_fields=["device_id", "fault_code", "timestamp"]
        )
        assert "设备: EQ001" in result
        assert "故障码: ERR001" in result
        assert "时间: 2024-01-01 10:00:00" in result
        assert "内容：\n设备 EQ001 故障" in result


class TestFastMeRAGInit:
    """
    FastMeRAG 初始化测试
    FastMeRAG initialization tests
    """

    def test_init_default(self):
        """测试默认初始化 / Test default initialization"""
        try:
            from app_factory import FastMeRAG
        except ImportError as e:
            pytest.skip(f"无法导入 FastMeRAG: {e}")

        rag = FastMeRAG(config={
            "vector_store": {
                "type": "chroma",
                "config": {
                    "persist_directory": "./data/chroma_test_init",
                    "collection_name": "test_init"
                }
            },
            "embedding": {"model_name": "BAAI/bge-m3"},
            "llm": {"model_name": "qwen-plus"}
        })

        assert rag is not None
        assert rag.vectorstore is not None
        assert rag.embeddings is not None
        assert rag.llm is not None

    def test_get_scenes(self, rag):
        """测试获取场景列表 / Test getting scene list"""
        scenes = rag.get_scenes()
        assert isinstance(scenes, list)
        assert len(scenes) >= 4  # 至少 4 个场景 / At least 4 scenes
        assert "default" in scenes
        assert "fault_diagnosis" in scenes

    def test_get_doc_types(self, rag):
        """测试获取文档类型 / Test getting document types"""
        doc_types = rag.get_doc_types()
        assert isinstance(doc_types, list)
        assert "log" in doc_types
        assert "manual" in doc_types
        assert "business" in doc_types
        assert "sop" in doc_types

    def test_get_vector_count_empty(self, rag):
        """测试空向量库计数 / Test empty vector store count"""
        count = rag.get_vector_count()
        assert count >= 0  # 可能已有数据 / May have existing data


class TestFastMeRAGIngest:
    """
    FastMeRAG 入库测试
    FastMeRAG ingestion tests
    """

    @pytest.fixture
    def sample_log_file(self, tmp_path):
        """创建临时日志文件 / Create temporary log file"""
        log_file = tmp_path / "test.log"
        log_content = """2024-01-01 10:00:00
设备 EQ001 启动运行

2024-01-01 10:05:00
设备 EQ001 出现故障码 ERR001
"""
        log_file.write_text(log_content, encoding="utf-8")
        return str(log_file)

    def test_ingest_log(self, rag, sample_log_file):
        """测试日志入库 / Test log ingestion"""
        result = rag.ingest(
            file_path=sample_log_file,
            doc_type="log",
            extra_metadata={"device_id": "EQ001"}
        )
        assert result["status"] == "success"
        assert "doc_id" in result
        assert result["chunks_count"] >= 1

    def test_ingest_require_review(self, rag, sample_log_file):
        """测试审核模式入库 / Test review mode ingestion"""
        result = rag.ingest(
            file_path=sample_log_file,
            doc_type="log",
            require_review=True
        )
        assert result["status"] == "waiting_review"
        assert "chunks" in result
        assert len(result["chunks"]) >= 1


class TestFastMeRAGChat:
    """
    FastMeRAG 问答测试
    FastMeRAG chat tests
    """

    @pytest.mark.skipif(
        not os.getenv("LLM_BASE_URL"),
        reason="需要 LLM API 配置 / Requires LLM API configuration"
    )
    def test_chat_default(self, rag):
        """测试默认问答 / Test default chat"""
        result = rag.chat(
            question="你好",
            scene="default"
        )
        assert "answer" in result
        assert "sources" in result
        assert isinstance(result["sources"], list)

    @pytest.mark.skipif(
        not os.getenv("LLM_BASE_URL"),
        reason="需要 LLM API 配置 / Requires LLM API configuration"
    )
    def test_chat_fault_diagnosis(self, rag):
        """测试故障诊断场景问答 / Test fault diagnosis scene chat"""
        result = rag.chat(
            question="设备故障怎么处理？",
            scene="fault_diagnosis"
        )
        assert "answer" in result
        assert result["scene"] == "fault_diagnosis"

    def test_chat_stream(self, rag):
        """测试流式问答 / Test streaming chat"""
        chunks = list(rag.chat_stream(
            question="测试",
            scene="default"
        ))
        # 不验证内容，因为可能需要 LLM / Don't validate content, may need LLM
        assert isinstance(chunks, list)


class TestFastMeRAGConfig:
    """
    FastMeRAG 配置测试
    FastMeRAG configuration tests
    """

    def test_add_scene(self, rag):
        """测试添加场景 / Test adding scene"""
        rag.add_scene(
            name="test_scene",
            doc_type="manual",
            prompt_template="default",
            description="测试场景"
        )
        scenes = rag.get_scenes()
        assert "test_scene" in scenes

    def test_add_metadata_rule(self, rag):
        """测试添加元数据规则 / Test adding metadata rule"""
        rag.add_metadata_rule(
            field="test_field",
            patterns=[r"测试 [：:\s]*([A-Za-z0-9]+)"]
        )
        # 验证规则已添加 / Verify rule added
        assert "test_field" in rag.metadata_extractor.rules

    def test_update_scene_top_k(self, rag):
        """测试更新场景 top_k / Test updating scene top_k"""
        original_top_k = rag.scene_router.scene_config["fault_diagnosis"]["top_k"]
        rag.update_scene_top_k("fault_diagnosis", 10)
        new_top_k = rag.scene_router.scene_config["fault_diagnosis"]["top_k"]
        assert new_top_k == 10
        # 恢复原值 / Restore original value
        rag.update_scene_top_k("fault_diagnosis", original_top_k)


class TestFastMeRAGMemory:
    """
    FastMeRAG 记忆测试
    FastMeRAG memory tests
    """

    def test_create_memory(self, rag):
        """测试创建记忆 / Test creating memory"""
        rag.create_memory("test_session")
        memory = rag.get_memory("test_session")
        assert memory is not None

    def test_clear_memory(self, rag):
        """测试清除记忆 / Test clearing memory"""
        rag.create_memory("test_session")
        rag.clear_memory("test_session")
        memory = rag.get_memory("test_session")
        assert memory is None

    @pytest.mark.skipif(
        not os.getenv("LLM_BASE_URL"),
        reason="需要 LLM API 配置 / Requires LLM API configuration"
    )
    def test_chat_with_memory(self, rag):
        """测试带记忆的对话 / Test chat with memory"""
        # 第一轮 / First round
        result1 = rag.chat_with_memory(
            question="我叫张三",
            session_id="test_session",
            scene="default"
        )
        assert "answer" in result1

        # 第二轮 - 应该能记住名字 / Second round - should remember name
        result2 = rag.chat_with_memory(
            question="我叫什么名字？",
            session_id="test_session",
            scene="default"
        )
        assert "answer" in result2
        # 理论上答案应该包含"张三"，但取决于 LLM
        # Theoretically answer should contain "张三", but depends on LLM


class TestFastMeRAGBatchIngest:
    """
    FastMeRAG 批量入库测试
    FastMeRAG batch ingestion tests
    """

    @pytest.fixture
    def sample_folder(self, tmp_path):
        """创建临时文件夹 / Create temporary folder"""
        folder = tmp_path / "test_docs"
        folder.mkdir()

        # 创建测试文件 / Create test files
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
        """测试批量入库 / Test batch ingestion"""
        results = rag.batch_ingest(
            folder_path=sample_folder,
            doc_type="log",
            file_extensions=[".log"]
        )
        assert len(results) == 2  # 2 个.log 文件 / 2 .log files
        success_count = sum(1 for r in results if r["status"] == "success")
        assert success_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])