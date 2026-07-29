"""
P0-P1 修复验证测试
P0-P1 Fix Verification Tests

验证分析报告中确认的 P0/P1 级别 bug 修复，覆盖：
- P0-1: os.getenv 逻辑错误（CHROMA_COLLECTION 旧别名）
- P0-2: embedding device 配置生效
- P0-3: LLM api_key 环境变量名一致性（FASTME_LLM_API_KEY / ${VAR}）
- P0-4: DEFAULT_CONFIG / _deep_merge 深拷贝独立性
- P1-5: ingest 末尾调用 persist（FAISS 落盘）
- P1-6: ChatPipeline 使用 default_top_k / max_context_length
- P1-8: 空回答兜底不入记忆
- P1-9: prompt_templates.yaml default 引号闭合
"""

import os
import copy
import pytest
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from core.models import FastMeDocument, FastMeChunk


# =============================================================================
# P0-1: os.getenv 逻辑错误修复
# =============================================================================

class TestP01ChromaCollectionAlias:
    """P0-1: CHROMA_COLLECTION 旧别名现在可被正确读取"""

    def test_legacy_chroma_collection_alias(self, monkeypatch):
        """仅设置旧别名 CHROMA_COLLECTION 时应生效（修复前返回默认值）"""
        from app_factory import FastMeRAG

        monkeypatch.setenv("FASTME_VECTOR_STORE_TYPE", "chroma")
        monkeypatch.setenv("CHROMA_COLLECTION", "my_legacy_coll")
        monkeypatch.delenv("FASTME_CHROMA_COLLECTION", raising=False)

        config = FastMeRAG._build_config_from_env()

        assert config["vector_store"]["config"]["collection_name"] == "my_legacy_coll"

    def test_canonical_chroma_collection_takes_priority(self, monkeypatch):
        """规范名 FASTME_CHROMA_COLLECTION 优先于旧别名"""
        from app_factory import FastMeRAG

        monkeypatch.setenv("FASTME_VECTOR_STORE_TYPE", "chroma")
        monkeypatch.setenv("FASTME_CHROMA_COLLECTION", "canonical_coll")
        monkeypatch.setenv("CHROMA_COLLECTION", "legacy_coll")

        config = FastMeRAG._build_config_from_env()

        assert config["vector_store"]["config"]["collection_name"] == "canonical_coll"


# =============================================================================
# P0-2: embedding device 配置生效
# =============================================================================

class TestP02EmbeddingDeviceConfig:
    """P0-2: embedding.device 配置应传入 HuggingFaceEmbeddings"""

    def test_device_cuda_from_config(self):
        """配置 device=cuda 时应传入 model_kwargs（修复前硬编码 cpu）"""
        from app_factory import FastMeRAG

        rag = FastMeRAG.__new__(FastMeRAG)  # 跳过 __init__
        rag.config = {
            "embedding": {"model_name": "BAAI/bge-m3", "device": "cuda", "normalize": False}
        }

        with patch("langchain_huggingface.HuggingFaceEmbeddings") as mock_emb:
            mock_emb.return_value = MagicMock()
            rag._create_embeddings()

        _, kwargs = mock_emb.call_args
        assert kwargs["model_kwargs"]["device"] == "cuda", \
            "embedding.device 配置未生效，仍硬编码为 cpu"

    def test_device_defaults_to_cpu(self):
        """未配置 device 时回退到 cpu"""
        from app_factory import FastMeRAG

        rag = FastMeRAG.__new__(FastMeRAG)
        rag.config = {"embedding": {"model_name": "BAAI/bge-m3"}}

        with patch("langchain_huggingface.HuggingFaceEmbeddings") as mock_emb:
            mock_emb.return_value = MagicMock()
            rag._create_embeddings()

        _, kwargs = mock_emb.call_args
        assert kwargs["model_kwargs"]["device"] == "cpu"


# =============================================================================
# P0-3: LLM api_key 环境变量名一致性
# =============================================================================

class TestP03LlmApiKeyResolution:
    """P0-3: api_key 应能从 FASTME_LLM_API_KEY 解析，且 ${VAR} 未解析时回退"""

    def test_api_key_from_fastme_env(self, monkeypatch):
        """配置无 api_key 时从 FASTME_LLM_API_KEY 读取"""
        from app_factory import FastMeRAG

        monkeypatch.setenv("FASTME_LLM_API_KEY", "fastme_key_value")
        monkeypatch.delenv("LLM_API_KEY", raising=False)

        rag = FastMeRAG.__new__(FastMeRAG)
        rag.config = {"llm": {"model_name": "qwen-plus"}}

        with patch("langchain_openai.ChatOpenAI") as mock_llm:
            mock_llm.return_value = MagicMock()
            rag._create_llm()

        _, kwargs = mock_llm.call_args
        assert kwargs["api_key"] == "fastme_key_value"

    def test_unresolved_var_falls_back_to_fastme(self, monkeypatch):
        """YAML 中 ${LLM_API_KEY} 未解析（字面量）时应回退到 FASTME_LLM_API_KEY"""
        from app_factory import FastMeRAG

        monkeypatch.setenv("FASTME_LLM_API_KEY", "fastme_key_value")
        monkeypatch.delenv("LLM_API_KEY", raising=False)

        rag = FastMeRAG.__new__(FastMeRAG)
        # 模拟 ConfigLoader._expand_env_vars 未能解析（LLM_API_KEY 不存在）后的字面量
        rag.config = {"llm": {"model_name": "qwen-plus", "api_key": "${LLM_API_KEY}"}}

        with patch("langchain_openai.ChatOpenAI") as mock_llm:
            mock_llm.return_value = MagicMock()
            rag._create_llm()

        _, kwargs = mock_llm.call_args
        assert kwargs["api_key"] == "fastme_key_value", \
            "${LLM_API_KEY} 未解析时应回退到 FASTME_LLM_API_KEY"

    def test_yaml_uses_canonical_var_name(self):
        """配置文件应引用规范名 ${FASTME_LLM_API_KEY}"""
        import yaml
        for path in ["./config/fastme_chroma.yaml", "./config/fastme_faiss.yaml"]:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "${FASTME_LLM_API_KEY}" in content, \
                f"{path} 应使用 ${FASTME_LLM_API_KEY} 而非 ${LLM_API_KEY}"


# =============================================================================
# P0-4: DEFAULT_CONFIG / _deep_merge 深拷贝独立性
# =============================================================================

class TestP04DeepCopyIndependence:
    """P0-4: 合并结果与 base 完全独立，修改不影响 DEFAULT_CONFIG"""

    def test_deep_merge_does_not_share_nested_refs(self):
        from config.loader import ConfigLoader

        base = {"vs": {"config": {"collection_name": "fastme_rag"}}, "lang": "zh"}
        override = {"lang": "en"}  # 不覆盖 vs.config

        merged = ConfigLoader._deep_merge(base, override)

        # 修改合并结果的嵌套字典
        merged["vs"]["config"]["collection_name"] = "MUTATED"

        assert base["vs"]["config"]["collection_name"] == "fastme_rag", \
            "base 的嵌套字典被合并结果污染（浅拷贝问题未修复）"

    def test_deep_merge_override_values_also_independent(self):
        from config.loader import ConfigLoader

        nested = {"by_type": {"log": 600}}
        base = {"chunking": {"default": 1000}}
        override = {"chunking": nested}

        merged = ConfigLoader._deep_merge(base, override)

        # 修改传入 override 的嵌套对象，不应影响已合并的结果
        nested["by_type"]["log"] = 9999
        assert merged["chunking"]["by_type"]["log"] == 600

    def test_default_config_not_polluted_after_build_from_env(self, monkeypatch):
        """_build_config_from_env 不应污染类级 DEFAULT_CONFIG"""
        from app_factory import FastMeRAG

        original = copy.deepcopy(FastMeRAG.DEFAULT_CONFIG)
        monkeypatch.setenv("FASTME_VECTOR_STORE_TYPE", "chroma")
        monkeypatch.setenv("FASTME_CHROMA_COLLECTION", "temp_coll")

        config = FastMeRAG._build_config_from_env()
        config["vector_store"]["config"]["collection_name"] = "MUTATED"

        assert FastMeRAG.DEFAULT_CONFIG["vector_store"]["config"]["collection_name"] == \
            original["vector_store"]["config"]["collection_name"]


# =============================================================================
# P1-5: ingest 末尾调用 persist
# =============================================================================

class _StubSplitter:
    def split(self, document):
        return [FastMeChunk(
            chunk_id="c1", doc_id=document.doc_id,
            doc_type=document.doc_type, text="chunk text",
            metadata={}
        )]


class _StubMetadataExtractor:
    def enrich_chunk(self, chunks):
        return chunks

    def get_available_fields(self):
        return []


class _StubSplitterRegistry:
    def get(self, doc_type):
        return _StubSplitter()


class _StubDocumentLoader:
    def load(self, file_path, doc_type, extra_metadata=None):
        return FastMeDocument(
            doc_id="doc_1", doc_type=doc_type,
            file_name="test.txt", file_path=str(file_path),
            text="hello world", metadata={}
        )


class TestP15IngestPersists:
    """P1-5: ingest 完成后应调用 vector_store.persist()（FAISS 落盘）"""

    def test_ingest_calls_persist(self, tmp_path):
        from core.ingest_pipeline import IngestPipeline

        mock_store = MagicMock()
        mock_store.get_count.return_value = 1

        pipeline = IngestPipeline(
            document_loader=_StubDocumentLoader(),
            splitter_registry=_StubSplitterRegistry(),
            metadata_extractor=_StubMetadataExtractor(),
            vector_store=mock_store,
            ingest_batch_size=32,
        )

        result = pipeline.ingest(file_path=str(tmp_path / "test.txt"), doc_type="log")

        assert result["status"] == "success"
        mock_store.add_documents.assert_called_once()
        mock_store.persist.assert_called_once(), \
            "ingest 完成后未调用 persist()，FAISS 数据不会落盘"

    def test_ingest_swallows_persist_failure(self, tmp_path):
        """persist 失败不应让 ingest 整体失败（数据已在内存）"""
        from core.ingest_pipeline import IngestPipeline

        mock_store = MagicMock()
        mock_store.get_count.return_value = 1
        mock_store.persist.side_effect = RuntimeError("disk full")

        pipeline = IngestPipeline(
            document_loader=_StubDocumentLoader(),
            splitter_registry=_StubSplitterRegistry(),
            metadata_extractor=_StubMetadataExtractor(),
            vector_store=mock_store,
        )

        result = pipeline.ingest(file_path=str(tmp_path / "test.txt"), doc_type="log")
        assert result["status"] == "success"  # persist 失败被记录但不中断


# =============================================================================
# P1-6: ChatPipeline 使用 default_top_k / max_context_length
# =============================================================================

def _build_chat_pipeline(default_top_k=5, max_context_length=None):
    """构建带 mock 依赖的 ChatPipeline"""
    from core.chat_pipeline import ChatPipeline

    retriever = MagicMock()
    retriever.scene_router.route.return_value = {"prompt_template": "default"}
    retriever.retrieve.return_value = ([], ["chunk_id", "doc_id"])

    prompt_adapter = MagicMock()
    prompt_adapter._format_context.return_value = "ctx"
    prompt_adapter.get_system_prompt.return_value = "system prompt"

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="answer")

    return ChatPipeline(
        scene_aware_retriever=retriever,
        prompt_adapter=prompt_adapter,
        llm=llm,
        default_top_k=default_top_k,
        max_context_length=max_context_length,
    )


class TestP16ChatPipelineConfig:
    """P1-6: ChatPipeline 应使用 default_top_k 与 max_context_length"""

    def test_resolve_top_k_explicit_arg_wins(self):
        pipe = _build_chat_pipeline(default_top_k=7)
        assert pipe._resolve_top_k(10, "default") == 10

    def test_resolve_top_k_uses_scene_config(self):
        pipe = _build_chat_pipeline(default_top_k=7)
        pipe.scene_aware_retriever.scene_router.route.return_value = {"top_k": 3}
        assert pipe._resolve_top_k(None, "default") == 3

    def test_resolve_top_k_falls_back_to_default(self):
        """场景配置无 top_k 时回退到 default_top_k（修复前硬编码 5）"""
        pipe = _build_chat_pipeline(default_top_k=12)
        pipe.scene_aware_retriever.scene_router.route.return_value = {}
        assert pipe._resolve_top_k(None, "default") == 12

    def test_truncate_context_respects_limit(self):
        pipe = _build_chat_pipeline(max_context_length=10)
        truncated = pipe._truncate_context("abcdefghijklmnopqrstuvwxyz")
        assert len(truncated) <= 10 + len("\n...(上下文已截断)")
        assert truncated.startswith("abcdefghij")

    def test_truncate_context_no_limit_passthrough(self):
        pipe = _build_chat_pipeline(max_context_length=None)
        text = "a" * 10000
        assert pipe._truncate_context(text) == text

    def test_chat_passes_resolved_top_k_to_retriever(self):
        pipe = _build_chat_pipeline(default_top_k=9)
        pipe.scene_aware_retriever.scene_router.route.return_value = {}
        pipe.chat(question="q", scene="default")
        _, kwargs = pipe.scene_aware_retriever.retrieve.call_args
        assert kwargs["top_k"] == 9, "chat 未将解析后的 top_k 传给检索器"


# =============================================================================
# P1-8: 空回答兜底不入记忆
# =============================================================================

class TestP18EmptyAnswerNotSavedToMemory:
    """P1-8: LLM 空回答时兜底文本不应存入记忆"""

    def _make_pipe(self, llm_content):
        from core.chat_pipeline import ChatPipeline

        retriever = MagicMock()
        retriever.scene_router.route.return_value = {"prompt_template": "default"}
        retriever.retrieve.return_value = ([], ["chunk_id"])

        prompt_adapter = MagicMock()
        prompt_adapter._format_context.return_value = "ctx"
        prompt_adapter.get_system_prompt.return_value = "sys"

        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content=llm_content)

        pipe = ChatPipeline(retriever, prompt_adapter, llm)

        # 用 MagicMock 作为 memory（ConversationBufferWindowMemory 是 pydantic 模型，
        # 不能直接替换方法），避免真实记忆的副作用
        mock_memory = MagicMock()
        mock_memory.load_memory_variables.return_value = {"history": []}
        pipe.memories["sess"] = mock_memory
        return pipe, mock_memory

    def test_empty_answer_skips_memory_save(self):
        pipe, mock_memory = self._make_pipe(llm_content="")

        result = pipe.chat_with_memory(question="q", session_id="sess", scene="default")

        assert "未能生成有效回答" in result["answer"]
        mock_memory.save_context.assert_not_called(), \
            "空回答的兜底文本被存入记忆，会污染后续多轮上下文"

    def test_normal_answer_saves_memory(self):
        pipe, mock_memory = self._make_pipe(llm_content="正常回答")

        pipe.chat_with_memory(question="q", session_id="sess", scene="default")
        mock_memory.save_context.assert_called_once()


# =============================================================================
# P1-9: prompt_templates.yaml default 引号闭合
# =============================================================================

class TestP19PromptTemplateQuote:
    """P1-9: default 模板引号应闭合"""

    def test_default_prompt_has_closed_quote(self):
        import yaml
        with open("./config/prompt_templates.yaml", "r", encoding="utf-8") as f:
            templates = yaml.safe_load(f)

        system = templates["default"]["system"]
        # 修复前: 回答"当前知识库无法得到相关的信息 （引号未闭合，缺句号）
        # 修复后: 回答"当前知识库无法得到相关的信息"。 （引号闭合 + 句号）
        # 兼容直引号 (") 与弯引号 (”) 两种闭合写法
        info_close_period = "信息"  # "信息"
        period = "。"  # "。"
        curly_close = "”"  # 弯引号 ”
        straight_close = '"'  # 直引号 "
        assert (info_close_period + curly_close + period) in system or \
               (info_close_period + straight_close + period) in system, \
            "default 模板引号未闭合或缺少句号"


# =============================================================================
# P0-10: score 语义归一化（L2 距离 -> [0,1] 相似度）
# =============================================================================

class TestP010ScoreSemanticNormalization:
    """P0-10: 检索结果 score 应为 [0,1] 相似度（越大越相关），而非原始 L2 距离

    修复前：FAISS/Chroma 返回的 L2 距离被原样塞入 score，方向相反且可能 > 1，
    与 FastMeSearchResult.score 文档声明的 "[0,1]，越高越相关" 矛盾。
    """

    def _make_converter(self):
        from core.retriever import BaseRetriever, ResultConverterMixin

        class _Conv(BaseRetriever, ResultConverterMixin):
            def retrieve(self, query, top_k, filters=None):
                return []

            def supports_filter(self):
                return True

        return _Conv()

    def test_distance_zero_is_perfect_match(self):
        conv = self._make_converter()
        assert conv._distance_to_similarity(0.0) == 1.0

    def test_larger_distance_means_lower_score(self):
        conv = self._make_converter()
        s1 = conv._distance_to_similarity(0.5)
        s2 = conv._distance_to_similarity(2.0)
        s3 = conv._distance_to_similarity(10.0)
        assert 0 < s3 < s2 < s1 < 1.0, \
            "距离越大相似度应越低（单调递减）"

    def test_score_always_in_unit_range(self):
        conv = self._make_converter()
        for d in [0.0, 0.1, 1.0, 4.0, 100.0, 10000.0]:
            s = conv._distance_to_similarity(d)
            assert 0.0 < s <= 1.0, f"距离 {d} 的相似度 {s} 超出 [0,1]"

    def test_none_and_invalid_distance_returns_zero(self):
        conv = self._make_converter()
        assert conv._distance_to_similarity(None) == 0.0
        assert conv._distance_to_similarity("abc") == 0.0
        # 负距离 clamp 到 0 -> 1/(1+0) = 1.0（防御性，正常不会出现负距离）
        assert conv._distance_to_similarity(-1.0) == 1.0

    def test_to_fastme_results_normalizes_score(self):
        from langchain_core.documents import Document
        conv = self._make_converter()
        # FAISS/Chroma 返回 (Document, L2距离)，距离越小越相关
        docs = [
            (Document(page_content="a", metadata={"chunk_id": "c1"}), 0.3),   # 更相关
            (Document(page_content="b", metadata={"chunk_id": "c2"}), 1.5),   # 较不相关
        ]
        results = conv._to_fastme_results(docs)
        assert results[0].score > results[1].score, \
            "距离小的应得到更高的相似度分数"
        assert all(0.0 < r.score <= 1.0 for r in results), \
            "归一化后 score 必须落在 [0,1]"

    def test_real_faiss_retrieval_scores_in_unit_range(self, embeddings, faiss_test_dir):
        """端到端：FAISS 真实检索的 score 落在 [0,1] 且按相关度降序"""
        from vector_stores.faiss import FAISSAdapter
        from vector_stores.faiss_retriever import FAISSRetriever
        from langchain_core.documents import Document

        adapter = FAISSAdapter(embedding_function=embeddings, index_path=faiss_test_dir)
        retriever = FAISSRetriever(adapter)
        adapter.add_documents(
            [
                Document(page_content="设备报警处理方法", metadata={"doc_type": "log"}),
                Document(page_content="设备维护手册内容", metadata={"doc_type": "manual"}),
            ],
            ids=["d1", "d2"],
        )
        results = retriever.retrieve(query="设备报警", top_k=2)
        assert len(results) == 2
        scores = [r.score for r in results]
        assert all(0.0 < s <= 1.0 for s in scores), \
            f"真实检索 score 超出 [0,1]: {scores}"
        # 最相关的（距离最小）应排在最前，分数最高
        assert scores == sorted(scores, reverse=True), \
            f"score 未按相关度降序排列: {scores}"


# =============================================================================
# P0-11: LLM max_tokens / streaming / max_retries 配置透传
# =============================================================================

class TestP011LlmConfigPassthrough:
    """P0-11: _create_llm 应将 max_tokens / streaming / max_retries 透传给 ChatOpenAI

    修复前：ChatOpenAI 只接收 model_name/api_key/base_url/temperature，
    配置中的 max_tokens、streaming 被静默丢弃。
    """

    def _make_rag(self, llm_cfg):
        from app_factory import FastMeRAG
        rag = FastMeRAG.__new__(FastMeRAG)  # 跳过 __init__
        rag.config = {"llm": llm_cfg}
        return rag

    def test_max_tokens_streaming_max_retries_passed(self):
        rag = self._make_rag({
            "model_name": "qwen-plus",
            "max_tokens": 1024,
            "streaming": True,
            "max_retries": 5,
        })
        with patch("langchain_openai.ChatOpenAI") as mock_llm:
            mock_llm.return_value = MagicMock()
            rag._create_llm()

        _, kwargs = mock_llm.call_args
        assert kwargs["max_tokens"] == 1024, "max_tokens 未透传"
        assert kwargs["streaming"] is True, "streaming 未透传"
        assert kwargs["max_retries"] == 5, "max_retries 未透传"

    def test_defaults_when_not_configured(self):
        """未配置时应使用安全默认值"""
        rag = self._make_rag({"model_name": "qwen-plus"})
        with patch("langchain_openai.ChatOpenAI") as mock_llm:
            mock_llm.return_value = MagicMock()
            rag._create_llm()

        _, kwargs = mock_llm.call_args
        assert kwargs["max_tokens"] is None
        assert kwargs["streaming"] is False
        assert kwargs["max_retries"] == 2

    def test_default_config_carries_max_retries(self):
        """DEFAULT_CONFIG 应包含 max_retries，保证默认配置下也透传"""
        from app_factory import FastMeRAG
        assert "max_retries" in FastMeRAG.DEFAULT_CONFIG["llm"], \
            "DEFAULT_CONFIG.llm 缺少 max_retries 字段"
