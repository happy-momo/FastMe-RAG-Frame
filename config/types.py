"""
配置类型定义(基于 Pydantic)
Configuration Type Definitions (Pydantic-based)

提供配置结构的运行时校验与类型契约。运行时 FastMeRAG 仍以 dict 消费配置,
此处 model 作为"加载门禁 + 类型参考",并对关键字段做强校验。
Runtime FastMeRAG still consumes config as dict; these models act as a load-time
gate and type reference, enforcing strong validation on key fields.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class VectorStoreConfig(BaseModel):
    """
    向量库配置
    Vector Store Configuration

    Attributes:
        type: 向量库类型 (chroma/faiss/milvus/qdrant/weaviate)
        config: 向量库特定配置 (如 persist_directory / index_path)
    """
    model_config = {"extra": "allow"}
    type: str
    config: dict = Field(default_factory=dict)

    @field_validator("type")
    @classmethod
    def _valid_type(cls, v):
        valid = ("chroma", "faiss", "milvus", "qdrant", "weaviate")
        if v not in valid:
            raise ValueError(
                f"Invalid vector_store.type: {v}. Valid types: {list(valid)}"
            )
        return v

    @model_validator(mode="after")
    def _check_required_config(self):
        """校验按类型必须存在的配置字段 / Validate type-required config fields"""
        if self.type == "chroma" and "persist_directory" not in self.config:
            raise ValueError(
                "Chroma vector store requires 'persist_directory' in vector_store.config. "
                'Example: {"persist_directory": "./data/chroma"}'
            )
        if self.type == "faiss" and "index_path" not in self.config:
            raise ValueError(
                "FAISS vector store requires 'index_path' in vector_store.config. "
                'Example: {"index_path": "./data/faiss_index"}'
            )
        return self


class EmbeddingConfig(BaseModel):
    """
    Embedding 模型配置
    Embedding Model Configuration

    Attributes:
        model_name: 模型名称 (HuggingFace 格式或本地路径)
        cache_dir: 模型缓存目录
        batch_size: Embedding 批量大小
        device: 计算设备 (cpu/cuda)
        normalize: 是否归一化
    """
    model_config = {"extra": "allow"}
    model_name: str
    cache_dir: str = "./models"
    batch_size: int = 32
    device: str = "cpu"
    normalize: bool = True

    @model_validator(mode="after")
    def _non_empty_model_name(self):
        if not self.model_name:
            raise ValueError("'embedding.model_name' cannot be empty")
        return self


class LLMConfig(BaseModel):
    """
    LLM 配置
    LLM Configuration

    Attributes:
        model_name: 模型名称
        base_url: API 地址
        api_key: API Key
        temperature: 温度参数
        max_tokens: 最大生成长度
        streaming: 是否启用流式输出
        max_retries: 请求失败重试次数
    """
    model_config = {"extra": "allow"}
    model_name: str
    base_url: str = "http://localhost:8000/v1"
    api_key: str = ""
    temperature: float = 0.2
    max_tokens: int = 2048
    streaming: bool = True
    max_retries: int = 2

    @model_validator(mode="after")
    def _validate_llm(self):
        if not self.model_name:
            raise ValueError("'llm.model_name' cannot be empty")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid 'llm.base_url' format: {self.base_url}. "
                "Must start with http:// or https://"
            )
        if not (0 <= self.temperature <= 2):
            raise ValueError(
                f"Invalid 'llm.temperature': {self.temperature}. "
                "Must be between 0 and 2"
            )
        return self


class ChunkingConfig(BaseModel):
    """
    Chunking 配置
    Chunking Configuration

    Attributes:
        default_max_size: 全局默认 chunk 大小
        by_type: 按文档类型覆盖的 chunk 大小
    """
    model_config = {"extra": "allow"}
    default_max_size: int = 1000
    by_type: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def _positive_sizes(self):
        if self.default_max_size <= 0:
            raise ValueError(
                f"Invalid 'chunking.default_max_size': {self.default_max_size}. "
                "Must be a positive integer"
            )
        bad = {k: v for k, v in self.by_type.items()
               if not isinstance(v, int) or v <= 0}
        if bad:
            raise ValueError(f"Invalid chunk sizes (must be positive int): {bad}")
        return self


class IngestPipelineConfig(BaseModel):
    """
    入库 Pipeline 配置
    Ingest Pipeline Configuration
    """
    model_config = {"extra": "allow"}
    batch_size: int = 32
    show_progress_bar: bool = False


class ChatPipelineConfig(BaseModel):
    """
    对话 Pipeline 配置
    Chat Pipeline Configuration
    """
    model_config = {"extra": "allow"}
    default_top_k: int = 5
    max_context_length: Optional[int] = 4096


class FastMeRAGConfig(BaseModel):
    """
    顶层配置契约 / Top-level configuration contract
    required 字段保证与 DEFAULT_CONFIG 合并后必存在。
    Required fields are guaranteed present after merging with DEFAULT_CONFIG.
    """
    model_config = {"extra": "allow"}
    vector_store: VectorStoreConfig
    embedding: EmbeddingConfig
    llm: LLMConfig
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    ingest_pipeline: IngestPipelineConfig = Field(default_factory=IngestPipelineConfig)
    chat_pipeline: ChatPipelineConfig = Field(default_factory=ChatPipelineConfig)
    language: str = "zh"
    config_dir: str = "./config"
    data_dir: str = "./data"
    log_level: str = "INFO"