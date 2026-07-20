"""
测试 fixtures - 共享测试配置和数据

本模块提供所有测试文件共享的 fixtures，避免重复代码。
"""

import pytest
import shutil
import tempfile
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings


@pytest.fixture(scope="session")
def embeddings():
    """
    创建 Embedding 函数（会话级共享）

    使用本地模型路径，避免重复下载。
    """
    model_path = Path(__file__).parent.parent / "models" / "bge-m3"
    return HuggingFaceEmbeddings(
        model_name=str(model_path),
        model_kwargs={"device": "cpu", "trust_remote_code": True},
        encode_kwargs={"normalize_embeddings": True}
    )


@pytest.fixture
def chroma_test_dir():
    """
    Chroma 测试目录（每个测试独立）

    测试完成后自动清理。
    """
    dir_path = tempfile.mkdtemp(prefix="chroma_test_")
    yield dir_path
    if Path(dir_path).exists():
        shutil.rmtree(dir_path)


@pytest.fixture
def faiss_test_dir():
    """
    FAISS 测试目录（每个测试独立）

    测试完成后自动清理。
    """
    dir_path = tempfile.mkdtemp(prefix="faiss_test_")
    yield dir_path
    if Path(dir_path).exists():
        shutil.rmtree(dir_path)


@pytest.fixture
def mock_search_results():
    """
    创建 mock 检索结果

    用于测试 PromptAdapter._format_context() 等方法。
    """
    from core.models import FastMeSearchResult

    return [
        FastMeSearchResult(
            chunk_id="chunk_1",
            doc_id="doc_1",
            doc_type="log",
            text="设备 EQ001 故障",
            score=0.95,
            metadata={
                "device_id": "EQ001",
                "fault_code": "ERR001",
                "timestamp": "2024-01-01 10:00:00",
                "line_id": "LN01"
            }
        ),
        FastMeSearchResult(
            chunk_id="chunk_2",
            doc_id="doc_2",
            doc_type="log",
            text="设备 EQ002 故障",
            score=0.85,
            metadata={
                "device_id": "EQ002",
                "fault_code": "ERR002",
                "timestamp": "2024-01-02 11:00:00",
                "line_id": "LN02"
            }
        )
    ]


@pytest.fixture
def sample_documents():
    """
    创建样本测试文档

    用于测试向量库适配器的 add_documents 方法。
    """
    from langchain_core.documents import Document

    return [
        Document(page_content="设备报警处理方法", metadata={"device_id": "EQ001", "doc_type": "log"}),
        Document(page_content="设备维护手册", metadata={"device_id": "EQ002", "doc_type": "manual"})
    ]
