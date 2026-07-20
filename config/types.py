"""
配置类型定义
Configuration Type Definitions

提供配置结构的类型定义，支持 IDE 自动补全和类型检查。
Provides type definitions for configuration structures, supporting IDE auto-completion and type checking.
"""

from typing import TypedDict, Optional, Dict, Any, List, Literal


# =============================================================================
# 向量库配置 / Vector Store Configuration
# =============================================================================

class ChromaVectorStoreConfig(TypedDict, total=False):
    """
    Chroma 向量库配置
    Chroma Vector Store Configuration

    Attributes:
        persist_directory: 持久化目录 / Persist directory
        collection_name: 集合名称 / Collection name
    """
    persist_directory: str
    collection_name: str


class FAISSVectorStoreConfig(TypedDict, total=False):
    """
    FAISS 向量库配置
    FAISS Vector Store Configuration

    Attributes:
        index_path: 索引持久化路径 / Index persist path
    """
    index_path: str


class MilvusVectorStoreConfig(TypedDict, total=False):
    """
    Milvus 向量库配置（未来扩展）
    Milvus Vector Store Configuration (Future Extension)

    Attributes:
        uri: Milvus 服务地址 / Milvus server URI
        collection_name: 集合名称 / Collection name
        database: 数据库名称 / Database name
    """
    uri: str
    collection_name: str
    database: str


# 支持的向量库类型 / Supported vector store types
VectorStoreType = Literal["chroma", "faiss", "milvus", "qdrant", "weaviate"]


class VectorStoreConfig(TypedDict, total=False):
    """
    向量库配置
    Vector Store Configuration

    Attributes:
        type: 向量库类型 / Vector store type
        config: 向量库特定配置 / Vector store specific configuration

    Example:
        >>> config: VectorStoreConfig = {
        ...     "type": "chroma",
        ...     "config": {
        ...         "persist_directory": "./data/chroma",
        ...         "collection_name": "fastme_rag"
        ...     }
        ... }
    """
    type: VectorStoreType
    config: Dict[str, Any]


# =============================================================================
# Embedding 配置 / Embedding Configuration
# =============================================================================

class EmbeddingConfig(TypedDict, total=False):
    """
    Embedding 模型配置
    Embedding Model Configuration

    Attributes:
        model_name: 模型名称（HuggingFace 格式或本地路径）
                    / Model name (HuggingFace format or local path)
        cache_dir: 模型缓存目录 / Model cache directory
        batch_size: Embedding 批量大小 / Embedding batch size
        device: 计算设备 (cpu/cuda) / Computing device (cpu/cuda)
        normalize: 是否归一化 / Whether to normalize embeddings
    """
    model_name: str
    cache_dir: str
    batch_size: int
    device: str
    normalize: bool


# =============================================================================
# LLM 配置 / LLM Configuration
# =============================================================================

class LLMConfig(TypedDict, total=False):
    """
    LLM 配置
    LLM Configuration

    Attributes:
        model_name: 模型名称 / Model name
        base_url: API 地址 / API base URL
        api_key: API Key（支持 ${VAR} 语法引用环境变量）
                 / API Key (supports ${VAR} syntax for environment variables)
        temperature: 温度参数 / Temperature parameter
        max_tokens: 最大生成长度 / Max generation length
        streaming: 是否启用流式输出 / Whether to enable streaming output
    """
    model_name: str
    base_url: str
    api_key: str
    temperature: float
    max_tokens: int
    streaming: bool


# =============================================================================
# Chunking 配置 / Chunking Configuration
# =============================================================================

class ChunkingConfig(TypedDict, total=False):
    """
    Chunking 配置
    Chunking Configuration

    Attributes:
        default_max_size: 全局默认 chunk 大小 / Global default chunk size
        by_type: 按文档类型覆盖 / Override by document type

    Example:
        >>> config: ChunkingConfig = {
        ...     "default_max_size": 1000,
        ...     "by_type": {
        ...         "log": 600,      # 日志推荐值 / Log recommended
        ...         "manual": 1500,  # 手册推荐值 / Manual recommended
        ...         "business": 1000,# 工单推荐值 / Business recommended
        ...         "sop": 800       # SOP 推荐值 / SOP recommended
        ...     }
        ... }
    """
    default_max_size: int
    by_type: Dict[str, int]


# =============================================================================
# Pipeline 配置 / Pipeline Configuration
# =============================================================================

class IngestPipelineConfig(TypedDict, total=False):
    """
    入库 Pipeline 配置
    Ingest Pipeline Configuration

    Attributes:
        batch_size: 入库分批大小 / Ingestion batch size
        show_progress_bar: 是否显示进度条 / Whether to show progress bar
    """
    batch_size: int
    show_progress_bar: bool


class ChatPipelineConfig(TypedDict, total=False):
    """
    对话 Pipeline 配置
    Chat Pipeline Configuration

    Attributes:
        default_top_k: 默认召回数量 / Default retrieval count
        max_context_length: 最大上下文长度 / Max context length
    """
    default_top_k: int
    max_context_length: int


# =============================================================================
# 完整配置 / Full Configuration
# =============================================================================

class FastMeRAGConfig(TypedDict, total=False):
    """
    FastMeRAG 完整配置
    FastMeRAG Full Configuration

    Example:
        >>> config: FastMeRAGConfig = {
        ...     "vector_store": {
        ...         "type": "chroma",
        ...         "config": {
        ...             "persist_directory": "./data/chroma",
        ...             "collection_name": "fastme_rag"
        ...         }
        ...     },
        ...     "embedding": {
        ...         "model_name": "BAAI/bge-m3",
        ...         "cache_dir": "./models"
        ...     },
        ...     "llm": {
        ...         "model_name": "qwen-plus",
        ...         "base_url": "http://localhost:8000/v1"
        ...     },
        ...     "chunking": {
        ...         "default_max_size": 1000,
        ...         "by_type": {"log": 600, "manual": 1500}
        ...     }
        ... }

    Attributes:
        vector_store: 向量库配置 / Vector store configuration
        embedding: Embedding 模型配置 / Embedding model configuration
        llm: LLM 配置 / LLM configuration
        chunking: Chunking 配置 / Chunking configuration
        ingest_pipeline: 入库 Pipeline 配置 / Ingest pipeline configuration
        chat_pipeline: 对话 Pipeline 配置 / Chat pipeline configuration
        language: 语言 (zh/en) / Language (zh/en)
        config_dir: 配置文件目录 / Config directory
        data_dir: 数据目录 / Data directory
        log_level: 日志级别 / Log level
    """
    # 核心组件配置 / Core component configuration
    vector_store: VectorStoreConfig
    embedding: EmbeddingConfig
    llm: LLMConfig

    # Chunking 配置 / Chunking configuration
    chunking: ChunkingConfig

    # Pipeline 配置 / Pipeline configuration
    ingest_pipeline: IngestPipelineConfig
    chat_pipeline: ChatPipelineConfig

    # 其他配置 / Other configuration
    language: str
    config_dir: str
    data_dir: str
    log_level: str
