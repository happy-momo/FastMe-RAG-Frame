"""
测试向量库适配器和检索器

测试 Chroma 和 FAISS 向量库适配器的功能，以及对应的检索器实现。
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


class TestChromaAdapter:
    """测试 Chroma 适配器"""

    def test_init(self, embeddings, chroma_test_dir):
        """测试初始化"""
        adapter = ChromaAdapter(
            collection_name="test_collection",
            persist_directory=chroma_test_dir,
            embedding_function=embeddings
        )
        assert adapter._collection_name == "test_collection"
        assert adapter._persist_directory == chroma_test_dir

    def test_add_documents(self, embeddings, chroma_test_dir):
        """测试添加文档"""
        adapter = ChromaAdapter(
            collection_name="test_collection",
            persist_directory=chroma_test_dir,
            embedding_function=embeddings
        )

        docs = [
            Document(page_content="测试内容 1", metadata={"source": "test1.txt"}),
            Document(page_content="测试内容 2", metadata={"source": "test2.txt"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2"])

        assert adapter.get_count() == 2

    def test_similarity_search(self, embeddings, chroma_test_dir):
        """测试相似度搜索"""
        adapter = ChromaAdapter(
            collection_name="test_collection",
            persist_directory=chroma_test_dir,
            embedding_function=embeddings
        )

        docs = [
            Document(page_content="设备报警处理方法", metadata={"device_id": "EQ001"}),
            Document(page_content="设备维护手册", metadata={"device_id": "EQ002"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2"])

        results = adapter.similarity_search_with_score("设备报警", k=1)
        assert len(results) == 1
        assert "报警" in results[0][0].page_content

    def test_get_config(self, embeddings, chroma_test_dir):
        """测试获取配置"""
        adapter = ChromaAdapter(
            collection_name="test_collection",
            persist_directory=chroma_test_dir,
            embedding_function=embeddings
        )

        config = adapter.get_config()
        assert config["collection_name"] == "test_collection"
        assert config["persist_directory"] == chroma_test_dir
        assert "vector_count" in config
        assert config["supports_filter"] is True

    def test_delete_collection(self, embeddings, chroma_test_dir):
        """测试删除集合"""
        adapter = ChromaAdapter(
            collection_name="test_collection",
            persist_directory=chroma_test_dir,
            embedding_function=embeddings
        )

        docs = [Document(page_content="测试内容", metadata={})]
        adapter.add_documents(docs, ids=["doc_1"])
        assert adapter.get_count() == 1

        adapter.delete_collection()
        # 删除后重新添加应该成功
        adapter.add_documents(docs, ids=["doc_1"])
        assert adapter.get_count() == 1


class TestFAISSAdapter:
    """测试 FAISS 适配器"""

    def test_init(self, embeddings, faiss_test_dir):
        """测试初始化"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )
        assert adapter._index_path == faiss_test_dir
        assert adapter.get_count() == 0  # 空索引

    def test_init_empty_index(self, embeddings):
        """测试创建空索引（不指定 index_path）"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=None
        )
        assert adapter.get_count() == 0

    def test_add_documents(self, embeddings, faiss_test_dir):
        """测试添加文档"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )

        docs = [
            Document(page_content="测试内容 1", metadata={"source": "test1.txt"}),
            Document(page_content="测试内容 2", metadata={"source": "test2.txt"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2"])

        assert adapter.get_count() == 2

    def test_similarity_search(self, embeddings, faiss_test_dir):
        """测试相似度搜索"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )

        docs = [
            Document(page_content="设备报警处理方法", metadata={"device_id": "EQ001"}),
            Document(page_content="设备维护手册", metadata={"device_id": "EQ002"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2"])

        results = adapter.similarity_search_with_score("设备报警", k=1)
        assert len(results) == 1

    def test_get_config(self, embeddings, faiss_test_dir):
        """测试获取配置"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )

        config = adapter.get_config()
        assert config["index_path"] == faiss_test_dir
        assert "vector_count" in config
        assert config["supports_filter"] is False

    def test_delete_collection(self, embeddings, faiss_test_dir):
        """测试删除集合（重置索引）"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )

        docs = [Document(page_content="测试内容", metadata={})]
        adapter.add_documents(docs, ids=["doc_1"])
        assert adapter.get_count() == 1

        adapter.delete_collection()
        assert adapter.get_count() == 0

    def test_persist(self, embeddings, faiss_test_dir):
        """测试持久化"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )

        docs = [Document(page_content="测试内容", metadata={})]
        adapter.add_documents(docs, ids=["doc_1"])
        adapter.persist()

        # 验证文件存在
        assert Path(faiss_test_dir).exists()

    def test_reset_for_memory_cleanup(self, embeddings, faiss_test_dir):
        """测试内存清理（原地更新，返回自身）"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )

        docs = [Document(page_content="测试内容", metadata={})]
        adapter.add_documents(docs, ids=["doc_1"])

        # 重置（原地更新，返回 self）
        result = adapter.reset_for_memory_cleanup()
        assert result is adapter  # 应返回自身，而非新实例
        assert adapter.get_count() == 1  # 数据应该保留


class TestVectorStoreIntegration:
    """向量库集成测试"""

    def test_chroma_with_metadata_filter(self, embeddings, chroma_test_dir):
        """测试 Chroma 元数据过滤"""
        adapter = ChromaAdapter(
            collection_name="test_collection",
            persist_directory=chroma_test_dir,
            embedding_function=embeddings
        )

        docs = [
            Document(page_content="设备 A 的日志", metadata={"device_id": "EQ001", "line_id": "LN01"}),
            Document(page_content="设备 B 的日志", metadata={"device_id": "EQ002", "line_id": "LN01"}),
            Document(page_content="设备 C 的日志", metadata={"device_id": "EQ003", "line_id": "LN02"})
        ]
        adapter.add_documents(docs, ids=["doc_1", "doc_2", "doc_3"])

        # 按设备 ID 过滤
        results = adapter.similarity_search_with_score(
            "设备日志",
            k=5,
            filter={"device_id": "EQ001"}
        )
        assert len(results) == 1
        assert results[0][0].metadata["device_id"] == "EQ001"

    def test_faiss_metadata_not_supported(self, embeddings, faiss_test_dir, caplog):
        """测试 FAISS 不支持元数据过滤时的警告"""
        adapter = FAISSAdapter(
            embedding_function=embeddings,
            index_path=faiss_test_dir
        )

        docs = [Document(page_content="测试内容", metadata={"device_id": "EQ001"})]
        adapter.add_documents(docs, ids=["doc_1"])

        # 应该发出警告
        results = adapter.similarity_search_with_score(
            "测试",
            k=1,
            filter={"device_id": "EQ001"}
        )
        # 警告应该被记录
        assert "不支持元数据过滤" in caplog.text
