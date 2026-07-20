"""
测试检索器实现

测试 ChromaRetriever, FAISSRetriever 和 SceneAwareRetriever 的功能。
"""

import pytest
import shutil
import tempfile
from pathlib import Path

from langchain_core.documents import Document

from vector_stores import ChromaAdapter, FAISSAdapter
from vector_stores.chroma_retriever import ChromaRetriever
from vector_stores.faiss_retriever import FAISSRetriever
from core.retriever import FilterCondition
from routers.scene_router import SceneRouter
from retrievers.scene_aware import SceneAwareRetriever


class TestChromaRetriever:
    """测试 ChromaRetriever"""

    def test_retrieve_basic(self, embeddings, chroma_test_dir):
        """测试基本检索功能"""
        adapter = ChromaAdapter(
            collection_name="test_collection",
            persist_directory=chroma_test_dir,
            embedding_function=embeddings
        )
        retriever = ChromaRetriever(adapter)

        # 添加测试文档
        docs = [
            Document(page_content="设备报警处理方法", metadata={"device_id": "EQ001", "doc_type": "log"}),
            Document(page_content="设备维护手册", metadata={"device_id": "EQ002", "doc_type": "manual"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2"])

        # 检索
        results = retriever.retrieve(query="设备报警", top_k=1)

        assert len(results) == 1
        assert "报警" in results[0].text

    def test_retrieve_with_filter(self, embeddings, chroma_test_dir):
        """测试带过滤条件的检索"""
        adapter = ChromaAdapter(
            collection_name="test_collection",
            persist_directory=chroma_test_dir,
            embedding_function=embeddings
        )
        retriever = ChromaRetriever(adapter)

        # 添加测试文档
        docs = [
            Document(page_content="设备报警处理", metadata={"device_id": "EQ001", "line_id": "LN01"}),
            Document(page_content="设备维护手册", metadata={"device_id": "EQ002", "line_id": "LN01"}),
            Document(page_content="另一设备报警", metadata={"device_id": "EQ003", "line_id": "LN02"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2", "doc_3"])

        # 带过滤检索
        filters = [FilterCondition(field="device_id", operator="$eq", value="EQ001")]
        results = retriever.retrieve(query="设备报警", top_k=5, filters=filters)

        assert len(results) >= 1
        assert results[0].metadata.get("device_id") == "EQ001"

    def test_retrieve_multiple_filters(self, embeddings, chroma_test_dir):
        """测试多条件过滤"""
        adapter = ChromaAdapter(
            collection_name="test_collection",
            persist_directory=chroma_test_dir,
            embedding_function=embeddings
        )
        retriever = ChromaRetriever(adapter)

        # 添加测试文档
        docs = [
            Document(page_content="LN01 设备报警", metadata={"device_id": "EQ001", "line_id": "LN01"}),
            Document(page_content="LN02 设备报警", metadata={"device_id": "EQ001", "line_id": "LN02"}),
            Document(page_content="LN01 设备维护", metadata={"device_id": "EQ002", "line_id": "LN01"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2", "doc_3"])

        # 多条件过滤
        filters = [
            FilterCondition(field="device_id", operator="$eq", value="EQ001"),
            FilterCondition(field="line_id", operator="$eq", value="LN01")
        ]
        results = retriever.retrieve(query="设备报警", top_k=5, filters=filters)

        assert len(results) >= 1
        assert results[0].metadata.get("device_id") == "EQ001"
        assert results[0].metadata.get("line_id") == "LN01"

    def test_supports_filter(self, embeddings, chroma_test_dir):
        """测试 supports_filter 方法"""
        adapter = ChromaAdapter(
            collection_name="test_collection",
            persist_directory=chroma_test_dir,
            embedding_function=embeddings
        )
        retriever = ChromaRetriever(adapter)
        assert retriever.supports_filter() is True


class TestFAISSRetriever:
    """测试 FAISSRetriever"""

    def test_retrieve_basic(self, embeddings, faiss_test_dir):
        """测试基本检索功能"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )
        retriever = FAISSRetriever(adapter, post_filter_multiplier=5)

        # 添加测试文档
        docs = [
            Document(page_content="设备报警处理方法", metadata={"device_id": "EQ001"}),
            Document(page_content="设备维护手册", metadata={"device_id": "EQ002"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2"])

        # 检索
        results = retriever.retrieve(query="设备报警", top_k=1)

        assert len(results) == 1
        assert "报警" in results[0].text

    def test_retrieve_with_filter(self, embeddings, faiss_test_dir):
        """测试带过滤条件的检索（后过滤）"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )
        retriever = FAISSRetriever(adapter, post_filter_multiplier=10)

        # 添加测试文档
        docs = [
            Document(page_content="设备报警处理", metadata={"device_id": "EQ001"}),
            Document(page_content="设备维护手册", metadata={"device_id": "EQ002"}),
            Document(page_content="另一设备报警", metadata={"device_id": "EQ003"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2", "doc_3"])

        # 带过滤检索
        filters = [FilterCondition(field="device_id", operator="$eq", value="EQ001")]
        results = retriever.retrieve(query="设备", top_k=5, filters=filters)

        # FAISS 后过滤应该只返回 EQ001 的结果
        assert len(results) >= 1
        for r in results:
            assert r.metadata.get("device_id") == "EQ001"

    def test_retrieve_no_filter(self, embeddings, faiss_test_dir):
        """测试无过滤检索"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )
        retriever = FAISSRetriever(adapter)

        docs = [
            Document(page_content="设备报警处理", metadata={"device_id": "EQ001"}),
            Document(page_content="设备维护手册", metadata={"device_id": "EQ002"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2"])

        results = retriever.retrieve(query="设备", top_k=2, filters=None)
        assert len(results) == 2

    def test_supports_filter(self, embeddings, faiss_test_dir):
        """测试 supports_filter 方法"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )
        retriever = FAISSRetriever(adapter)
        assert retriever.supports_filter() is True


class TestSceneAwareRetriever:
    """测试 SceneAwareRetriever"""

    @pytest.fixture
    def scene_router(self):
        """创建 SceneRouter 实例"""
        config_path = Path(__file__).parent.parent / "config" / "scenes.yaml"
        return SceneRouter(config_path=str(config_path))

    def test_scene_aware_chroma(self, embeddings, chroma_test_dir, scene_router):
        """测试 Chroma 场景感知检索"""
        adapter = ChromaAdapter(
            collection_name="test_collection",
            persist_directory=chroma_test_dir,
            embedding_function=embeddings
        )
        base_retriever = ChromaRetriever(adapter)
        scene_aware = SceneAwareRetriever(base_retriever, scene_router)

        # 添加测试文档
        docs = [
            Document(page_content="设备报警处理方法", metadata={"device_id": "EQ001", "doc_type": "log"}),
            Document(page_content="设备维护手册", metadata={"device_id": "EQ002", "doc_type": "manual"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2"])

        # 场景化检索
        results, source_fields = scene_aware.retrieve(
            question="设备报警怎么处理？",
            scene="fault_diagnosis",
            filters={"device_id": "EQ001"}
        )

        assert len(results) >= 1
        assert isinstance(source_fields, list)

    def test_scene_aware_faiss(self, embeddings, faiss_test_dir, scene_router):
        """测试 FAISS 场景感知检索"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )
        base_retriever = FAISSRetriever(adapter)
        scene_aware = SceneAwareRetriever(base_retriever, scene_router)

        # 添加测试文档
        docs = [
            Document(page_content="设备报警处理方法", metadata={"device_id": "EQ001", "doc_type": "log"}),
            Document(page_content="设备维护手册", metadata={"device_id": "EQ002", "doc_type": "manual"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2"])

        # 场景化检索
        results, source_fields = scene_aware.retrieve(
            question="设备报警怎么处理？",
            scene="fault_diagnosis",
            filters={"device_id": "EQ001"}
        )

        assert len(results) >= 1
        assert isinstance(source_fields, list)
