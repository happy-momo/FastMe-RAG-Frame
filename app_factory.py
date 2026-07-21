"""
FastMe RAG - 制造业专属 RAG 框架（工厂类）
FastMe RAG - Manufacturing-Specific RAG Framework (Factory Class)

FastMeRAG 是一个工厂类，负责：
FastMeRAG is a factory class responsible for:
1. 加载配置 / Loading configuration
2. 创建和组装组件 / Creating and assembling components
3. 委托 Pipeline 提供业务方法 / Delegating to pipelines for business methods

快速开始 / Quick Start:
    # 方式 1: 从配置文件加载（推荐）
    # Method 1: Load from config file (recommended)
    from app_factory import FastMeRAG
    rag = FastMeRAG.from_config("./config/fastme_chroma.yaml")

    # 方式 2: 从配置字典加载
    # Method 2: Load from config dictionary
    rag = FastMeRAG(config={
        "vector_store": {"type": "faiss", "config": {"index_path": "./data/faiss"}},
        "embedding": {"model_name": "BAAI/bge-m3"},
        "llm": {"model_name": "qwen-plus"},
    })

    # 方式 3: 使用默认配置
    # Method 3: Use default configuration
    rag = FastMeRAG()

    # 使用业务方法 / Use business methods
    rag.ingest("manual.pdf", doc_type="manual")
    result = rag.chat("设备报警怎么处理？", scene="fault_diagnosis")
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Union

from dotenv import load_dotenv

# 配置加载器 / Configuration loader
from config.loader import ConfigLoader

# 工厂模块 / Factory modules
from vector_stores.factory import VectorStoreFactory
from retrievers import RetrieverFactory
from core.ingest_pipeline import IngestPipeline
from core.chat_pipeline import ChatPipeline

# 组件 / Components
from adapters import SimpleDocumentLoader, PromptAdapter
from splitters.base import SplitterRegistry
from manufacturing.metadata_extractor import IndustrialMetadataExtractor
from routers.scene_router import SceneRouter

# 加载 .env 环境变量 / Load .env environment variables
load_dotenv(Path(__file__).parent / ".env")

# 日志配置 / Logging configuration
logger = logging.getLogger("fastme_rag")

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

# 抑制第三方库日志噪音 / Suppress third-party library log noise
for _lib in ["sentence_transformers", "urllib3", "chromadb",
             "httpx", "httpcore", "huggingface_hub", "openai"]:
    logging.getLogger(_lib).setLevel(logging.WARNING)


class FastMeRAG:
    """
    FastMe RAG 工厂类
    FastMe RAG Factory Class

    负责创建和组装 RAG 系统的所有组件，并提供统一的业务接口。
    Responsible for creating and assembling all components of the RAG system
    and providing a unified business interface.

    支持场景 / Supported Scenes:
        - fault_diagnosis: 故障诊断（基于运维日志、故障记录）
          Fault diagnosis (based on operation logs and fault records)
        - manual_query: 设备手册查询
          Equipment manual query
        - work_order_trace: 工单追溯
          Work order tracing
        - default: 默认问答
          Default Q&A

    支持文档类型 / Supported Document Types:
        - log: 运维日志 / Operation logs
        - manual: 设备手册 / Equipment manuals
        - business: 工单/业务文档 / Work orders/business documents
        - sop: 工艺 SOP / Process SOPs

    Example:
        >>> # 从配置文件加载 / Load from config file
        >>> rag = FastMeRAG.from_config("./config/fastme_chroma.yaml")
        >>>
        >>> # 文档入库 / Document ingestion
        >>> rag.ingest("manual.pdf", doc_type="manual")
        >>>
        >>> # 场景化问答 / Scene-aware Q&A
        >>> result = rag.chat("设备报警怎么处理？", scene="fault_diagnosis")
        >>> print(result["answer"])
    """

    # =========================================================================
    # 默认配置 / Default Configuration
    # =========================================================================

    DEFAULT_CONFIG: Dict[str, Any] = {
        # 向量库配置 / Vector Store Configuration
        "vector_store": {
            "type": "chroma",
            "config": {
                "persist_directory": "./data/chroma",      # Chroma 持久化目录
                "collection_name": "fastme_rag",           # Chroma 集合名称
                # "index_path": "./data/faiss_index",      # FAISS 索引路径 (当 type=faiss 时)
            }
        },
        # Embedding 模型配置 / Embedding Model Configuration
        "embedding": {
            "model_name": "BAAI/bge-m3",
            "cache_dir": "./models",
            "batch_size": 32,
            "device": "cpu",               # 计算设备：cpu 或 cuda
            "normalize": True,             # 是否归一化 embeddings
        },
        # LLM 配置 / LLM Configuration
        "llm": {
            "model_name": "qwen-plus",
            "base_url": "http://localhost:8000/v1",
            "api_key": "",                 # API Key（建议从环境变量读取）
            "temperature": 0.2,
            "max_tokens": 2048,
            "streaming": True,             # 是否启用流式输出
        },
        # Chunking 配置 / Chunking Configuration
        "chunking": {
            "default_max_size": 1000,
            "by_type": {
                "log": 600,                # 日志条目通常较短
                "manual": 1500,            # 章节结构完整，需要保留上下文
                "business": 1000,          # 业务记录中等长度
                "sop": 800,                # 操作步骤需要精确
            }
        },
        # Pipeline 配置 / Pipeline Configuration
        "ingest_pipeline": {
            "batch_size": 32,
            "show_progress_bar": False,
        },
        "chat_pipeline": {
            "default_top_k": 5,
            "max_context_length": 4096,
        },
        # 其他配置 / Other Configuration
        "language": "zh",
        "config_dir": "./config",
        "data_dir": "./data",
        "log_level": "INFO",
    }

    # =========================================================================
    # 初始化方法 / Initialization Methods
    # =========================================================================

    def __init__(self, config: Optional[Union[Dict[str, Any], str, Path]] = None):
        """
        初始化 FastMeRAG
        Initialize FastMeRAG

        Args:
            config: 配置字典、YAML 文件路径、或 JSON 文件路径
                - dict: 直接使用配置字典
                - str/Path 且以 .yaml/.yml/.json 结尾：加载配置文件
                - None: 优先使用 .env 环境变量配置，否则使用默认配置

        Example:
            >>> # 使用 .env 配置（推荐）/ Use .env config (recommended)
            >>> rag = FastMeRAG()
            >>>
            >>> # 使用配置文件 / Use config file
            >>> rag = FastMeRAG("./config/fastme_chroma.yaml")
            >>>
            >>> # 使用配置字典 / Use config dictionary
            >>> rag = FastMeRAG(config={
            ...     "vector_store": {"type": "faiss"},
            ...     "embedding": {"model_name": "BAAI/bge-m3"},
            ...     "llm": {"model_name": "qwen-plus"}
            ... })
        """
        # 1. 加载配置 / Load configuration
        # 如果 config 为 None，优先尝试从环境变量加载
        # If config is None, try loading from environment variables first
        if config is None:
            self.config = self._load_config_from_env_or_default()
        else:
            self.config = self._load_config(config)

        # 2. 创建核心组件 / Create core components
        self.embeddings = self._create_embeddings()
        self.vectorstore = self._create_vectorstore()
        self.llm = self._create_llm()

        # 3. 创建制造业组件 / Create manufacturing components
        self._init_manufacturing_components()

        # 4. 创建 Pipeline / Create pipelines
        self._init_pipelines()

        # 5. 绑定业务方法（委托给 Pipeline）/ Bind business methods (delegate to pipelines)
        self._bind_methods()

        # 6. 日志记录 / Logging
        self._log_initialization()

    @classmethod
    def from_config(
        cls,
        config: Union[Dict[str, Any], str, Path],
        overrides: Optional[Dict[str, Any]] = None
    ) -> "FastMeRAG":
        """
        从配置文件或字典创建 FastMeRAG 实例
        Create FastMeRAG instance from config file or dictionary

        Args:
            config: 配置文件路径或配置字典
                    / Config file path or configuration dictionary
            overrides: 覆盖配置（会合并到原配置）
                      / Override configuration (merged into original)

        Returns:
            FastMeRAG 实例 / FastMeRAG instance

        Example:
            >>> # 从 YAML 文件加载 / Load from YAML file
            >>> rag = FastMeRAG.from_config("./config/fastme_chroma.yaml")
            >>>
            >>> # 从配置字典加载 / Load from config dictionary
            >>> rag = FastMeRAG.from_config({
            ...     "vector_store": {"type": "faiss"},
            ...     "embedding": {"model_name": "BAAI/bge-m3"},
            ...     "llm": {"model_name": "qwen-plus"}
            ... })
            >>>
            >>> # 加载并覆盖部分配置 / Load and override partial config
            >>> rag = FastMeRAG.from_config(
            ...     "./config/fastme_chroma.yaml",
            ...     overrides={"vector_store": {"config": {"collection_name": "new_coll"}}}
            ... )
        """
        if isinstance(config, dict):
            if overrides:
                config = ConfigLoader._deep_merge(config, overrides)
            return cls(config=config)
        loaded = ConfigLoader.load(config, overrides)
        return cls(config=loaded)

    @classmethod
    def from_env(cls) -> "FastMeRAG":
        """
        从环境变量创建 FastMeRAG 实例
        Create FastMeRAG instance from environment variables

        读取的环境变量 / Environment variables read:
        - FASTME_CONFIG: 配置文件路径 / Config file path
        - FASTME_VECTOR_STORE_TYPE: 向量库类型 / Vector store type
        - EMBEDDING_MODEL: Embedding 模型名称 / Embedding model name
        - LLM_MODEL: LLM 模型名称 / LLM model name
        - LLM_BASE_URL: LLM API 地址 / LLM API base URL
        - LLM_API_KEY: LLM API Key

        Returns:
            FastMeRAG 实例 / FastMeRAG instance

        Example:
            >>> # .env 文件 / .env file
            >>> # FASTME_CONFIG=./config/fastme_faiss.yaml
            >>> # FASTME_VECTOR_STORE_TYPE=faiss
            >>> # EMBEDDING_MODEL=BAAI/bge-m3
            >>> rag = FastMeRAG.from_env()
        """
        config_path = os.getenv("FASTME_CONFIG")
        if config_path:
            return cls.from_config(config_path)
        config = cls._build_config_from_env()
        return cls(config=config)

    # =========================================================================
    # 内部方法 - 配置加载 / Internal Methods - Configuration Loading
    # =========================================================================

    def _load_config(self, config: Optional[Union[Dict, str, Path]]) -> Dict[str, Any]:
        """
        加载并合并配置
        Load and merge configuration

        Args:
            config: 配置字典或文件路径 / Config dictionary or file path

        Returns:
            合并后的配置字典 / Merged configuration dictionary

        Note:
            配置合并逻辑 / Configuration merge logic:
            - dict: 与 DEFAULT_CONFIG 深度合并
            - str/Path (文件): 加载文件后与 DEFAULT_CONFIG 深度合并
            - None: 返回 DEFAULT_CONFIG 副本
        """
        if config is None:
            return self.DEFAULT_CONFIG.copy()
        elif isinstance(config, dict):
            logger.debug("[FastMeRAG] 从配置字典加载（与默认配置合并）")
            return ConfigLoader._deep_merge(self.DEFAULT_CONFIG, config)
        elif isinstance(config, (str, Path)):
            logger.debug(f"[FastMeRAG] 从配置文件加载：{config}（与默认配置合并）")
            file_config = ConfigLoader.load(config)
            return ConfigLoader._deep_merge(self.DEFAULT_CONFIG, file_config)
        raise ValueError(f"Unsupported config type: {type(config)}")

    def _load_config_from_env_or_default(self) -> Dict[str, Any]:
        """
        从环境变量加载配置，如果环境变量不存在则使用默认配置
        Load configuration from environment variables, use default if not set

        优先级 / Priority:
        1. FASTME_CONFIG 环境变量指向的配置文件
        2. 单独的环境变量（EMBEDDING_MODEL, LLM_MODEL 等）
        3. 默认配置

        Returns:
            配置字典 / Configuration dictionary
        """
        # 检查是否有 FASTME_CONFIG 环境变量
        # Check if FASTME_CONFIG environment variable exists
        config_path = os.getenv("FASTME_CONFIG")
        if config_path:
            logger.info(f"[FastMeRAG] 从配置文件加载: {config_path}")
            return ConfigLoader.load(config_path)

        # 检查是否有必要的环境变量配置（支持 FASTME_ 前缀和无前缀别名）
        # Check if required environment variables are set (supports FASTME_ prefix and alias)
        embedding_model = (
            os.getenv("FASTME_EMBEDDING_MODEL") or
            os.getenv("EMBEDDING_MODEL")
        )
        llm_model = (
            os.getenv("FASTME_LLM_MODEL") or
            os.getenv("LLM_MODEL")
        )

        if embedding_model or llm_model:
            # 有环境变量配置，从环境变量构建配置
            # Environment variables set, build config from env
            logger.info("[FastMeRAG] 从环境变量加载配置")
            return self._build_config_from_env()

        # 没有环境变量配置，使用默认配置
        # No environment variables, use default config
        logger.info("[FastMeRAG] 使用默认配置")
        return self.DEFAULT_CONFIG.copy()

    @staticmethod
    def _build_config_from_env() -> Dict[str, Any]:
        """
        从环境变量构建配置
        Build configuration from environment variables

        支持的环境变量 / Supported environment variables:
        - FASTME_EMBEDDING_MODEL / EMBEDDING_MODEL: Embedding 模型名称
        - FASTME_MODEL_CACHE_DIR / MODEL_CACHE_DIR: 模型缓存目录
        - FASTME_LLM_MODEL / LLM_MODEL: LLM 模型名称
        - FASTME_LLM_BASE_URL / LLM_BASE_URL: LLM API 地址
        - FASTME_LLM_API_KEY / LLM_API_KEY: LLM API Key
        - FASTME_VECTOR_STORE_TYPE: 向量库类型
        - FASTME_CHROMA_PERSIST_DIR / CHROMA_DIR: Chroma 持久化目录
        - FASTME_CHROMA_COLLECTION / CHROMA_COLLECTION: Chroma 集合名称
        - FASTME_FAISS_INDEX_PATH / FAISS_INDEX_PATH: FAISS 索引路径
        - FASTME_LANGUAGE: 语言设置

        Returns:
            配置字典 / Configuration dictionary
        """
        config: Dict[str, Any] = {
            "vector_store": {
                "type": os.getenv("FASTME_VECTOR_STORE_TYPE", "chroma"),
                "config": {}
            },
            "embedding": {
                "model_name": os.getenv("FASTME_EMBEDDING_MODEL") or os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"),
                "cache_dir": os.getenv("FASTME_MODEL_CACHE_DIR") or os.getenv("MODEL_CACHE_DIR", "./models"),
            },
            "llm": {
                "model_name": os.getenv("FASTME_LLM_MODEL") or os.getenv("LLM_MODEL", "qwen-plus"),
                "base_url": os.getenv("FASTME_LLM_BASE_URL") or os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
                "api_key": os.getenv("FASTME_LLM_API_KEY") or os.getenv("LLM_API_KEY", "")
            },
            "language": os.getenv("FASTME_LANGUAGE", "zh")
        }

        # 向量库特定配置 / Vector store specific configuration
        vs_type = config["vector_store"]["type"]
        if vs_type == "chroma":
            # 支持两种环境变量名：CHROMA_DIR（旧）和 FASTME_CHROMA_PERSIST_DIR（新）
            # Support both: CHROMA_DIR (old) and FASTME_CHROMA_PERSIST_DIR (new)
            persist_dir = (
                os.getenv("FASTME_CHROMA_PERSIST_DIR") or
                os.getenv("CHROMA_PERSIST_DIR") or
                os.getenv("CHROMA_DIR", "./data/chroma")
            )
            config["vector_store"]["config"]["persist_directory"] = persist_dir
            config["vector_store"]["config"]["collection_name"] = os.getenv(
                "FASTME_CHROMA_COLLECTION" or "CHROMA_COLLECTION", "fastme_rag"
            )
        elif vs_type == "faiss":
            config["vector_store"]["config"]["index_path"] = (
                os.getenv("FASTME_FAISS_INDEX_PATH") or
                os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
            )

        return config

    # =========================================================================
    # 内部方法 - 组件创建 / Internal Methods - Component Creation
    # =========================================================================

    def _create_embeddings(self):
        """
        创建 Embedding 模型
        Create Embedding model

        Returns:
            HuggingFaceEmbeddings 实例 / HuggingFaceEmbeddings instance
        """
        from langchain_huggingface import HuggingFaceEmbeddings

        cfg = self.config.get("embedding", {})
        return HuggingFaceEmbeddings(
            model_name=cfg.get("model_name", "BAAI/bge-m3"),
            cache_folder=cfg.get("cache_dir", "./models"),
            model_kwargs={"device": "cpu", "trust_remote_code": True},
            encode_kwargs={
                "normalize_embeddings": cfg.get("normalize", True),
                "batch_size": cfg.get("batch_size", 32)
            },
        )

    def _create_vectorstore(self):
        """
        创建向量库适配器
        Create vector store adapter

        Returns:
            VectorStoreAdapter 实例 / VectorStoreAdapter instance
        """
        cfg = self.config.get("vector_store", {})
        return VectorStoreFactory.create(
            vector_store_type=cfg.get("type", "chroma"),
            embeddings=self.embeddings,
            vector_store_config=cfg.get("config", {}),
        )

    def _create_llm(self):
        """
        创建 LLM
        Create LLM

        Returns:
            ChatOpenAI 实例 / ChatOpenAI instance
        """
        from langchain_openai import ChatOpenAI

        cfg = self.config.get("llm", {})
        api_key = cfg.get("api_key", os.getenv("LLM_API_KEY", ""))

        # 支持 ${VAR} 语法引用环境变量
        # Support ${VAR} syntax for environment variable reference
        if isinstance(api_key, str) and api_key.startswith("${") and api_key.endswith("}"):
            api_key = os.getenv(api_key[2:-1], "")

        return ChatOpenAI(
            model_name=cfg.get("model_name", "qwen-plus"),
            api_key=api_key,
            base_url=cfg.get("base_url", "http://localhost:8000/v1"),
            temperature=cfg.get("temperature", 0.2),
        )

    def _init_manufacturing_components(self):
        """
        创建制造业专属组件
        Create manufacturing-specific components
        """
        cfg = self.config.get("chunking", {})
        config_dir = Path(self.config.get("config_dir", "./config"))

        # 拆解器注册表（按类型配置不同的 max_chunk_size）
        # Splitter registry (different max_chunk_size per type)
        self.splitter_registry = self._create_splitters(cfg)

        # 元数据抽取器 / Metadata extractor
        self.metadata_extractor = IndustrialMetadataExtractor(
            config_path=config_dir / "metadata_rules.yaml"
        )

        # 场景路由 / Scene router
        self.scene_router = SceneRouter(config_path=config_dir / "scenes.yaml")

        # Prompt 适配器 / Prompt adapter
        language = self.config.get("language", "zh")
        self.prompt_adapter = PromptAdapter(
            path=config_dir / "prompt_templates.yaml",
            field_labels_path=config_dir / "field_labels.yaml",
            language=language,
        )

    def _create_splitters(self, chunking_config: Dict[str, Any]) -> SplitterRegistry:
        """
        创建拆解器注册表（支持按类型配置）
        Create splitter registry (supports per-type configuration)

        Args:
            chunking_config: Chunking 配置 / Chunking configuration

        Returns:
            SplitterRegistry 实例 / SplitterRegistry instance

        Note:
            chunk 大小优先级 / Chunk size priority:
            1. by_type 配置 / by_type configuration
            2. Splitter 类的 DEFAULT_MAX_CHUNK_SIZE
            3. default_max_size 全局默认值
        """
        from splitters.log_splitter import LogSplitter
        from splitters.manual_splitter import ManualSplitter
        from splitters.business_splitter import BusinessSplitter
        from splitters.sop_splitter import SopSplitter

        registry = SplitterRegistry()
        default_max = chunking_config.get("default_max_size", 1000)
        by_type = chunking_config.get("by_type", {})

        def get_size(doc_type: str, splitter_cls) -> int:
            """获取指定类型的 max_chunk_size / Get max_chunk_size for specified type"""
            # 优先级 1: by_type 配置 / Priority 1: by_type configuration
            if doc_type in by_type:
                return by_type[doc_type]
            # 优先级 2: Splitter 类默认值 / Priority 2: Splitter class default
            if hasattr(splitter_cls, "DEFAULT_MAX_CHUNK_SIZE"):
                return splitter_cls.DEFAULT_MAX_CHUNK_SIZE
            # 优先级 3: 全局默认值 / Priority 3: Global default
            return default_max

        registry.register("log", LogSplitter(max_chunk_size=get_size("log", LogSplitter)))
        registry.register("manual", ManualSplitter(max_chunk_size=get_size("manual", ManualSplitter)))
        registry.register("business", BusinessSplitter(max_chunk_size=get_size("business", BusinessSplitter)))
        registry.register("sop", SopSplitter(max_chunk_size=get_size("sop", SopSplitter)))

        return registry

    def _init_pipelines(self):
        """
        创建 Pipeline
        Create pipelines
        """
        cfg = self.config.get("ingest_pipeline", {})

        # IngestPipeline
        self.ingest_pipeline = IngestPipeline(
            document_loader=SimpleDocumentLoader(),
            splitter_registry=self.splitter_registry,
            metadata_extractor=self.metadata_extractor,
            vector_store=self.vectorstore,
            ingest_batch_size=cfg.get("batch_size", 32),
            show_progress_bar=cfg.get("show_progress_bar", False),
        )

        # 场景化检索器 / Scene-aware retriever
        vector_store_type = self.config.get("vector_store", {}).get("type", "chroma")
        self.scene_aware_retriever = RetrieverFactory.create(
            vector_store_type=vector_store_type,
            vector_store_adapter=self.vectorstore,
            scene_router=self.scene_router,
        )

        # ChatPipeline
        self.chat_pipeline = ChatPipeline(
            scene_aware_retriever=self.scene_aware_retriever,
            prompt_adapter=self.prompt_adapter,
            llm=self.llm,
        )

    def _bind_methods(self):
        """
        绑定业务方法（委托给 Pipeline）
        Bind business methods (delegate to pipelines)
        """
        # IngestPipeline 方法 / IngestPipeline methods
        self.ingest = self.ingest_pipeline.ingest
        self.batch_ingest = self.ingest_pipeline.batch_ingest

        # ChatPipeline 方法 / ChatPipeline methods
        self.chat = self.chat_pipeline.chat
        self.chat_stream = self.chat_pipeline.chat_stream
        self.create_memory = self.chat_pipeline.create_memory
        self.get_memory = self.chat_pipeline.get_memory
        self.clear_memory = self.chat_pipeline.clear_memory
        self.chat_with_memory = self.chat_pipeline.chat_with_memory

    def _log_initialization(self):
        """
        记录初始化信息
        Log initialization information
        """
        vs_cfg = self.config.get("vector_store", {})
        emb_cfg = self.config.get("embedding", {})
        llm_cfg = self.config.get("llm", {})

        logger.info("=" * 60)
        logger.info("FastMe RAG 初始化完成 / FastMe RAG Initialization Complete")
        logger.info(f"  向量库 / Vector Store: {vs_cfg.get('type', 'chroma')}")
        logger.info(f"  Embedding: {emb_cfg.get('model_name', 'BAAI/bge-m3')}")
        logger.info(f"  LLM: {llm_cfg.get('model_name', 'qwen-plus')}")
        logger.info(f"  语言 / Language: {self.config.get('language', 'zh')}")
        logger.info("=" * 60)

    # =========================================================================
    # 配置管理方法 / Configuration Management Methods
    # =========================================================================

    def add_scene(
        self,
        name: str,
        doc_type: str,
        prompt_template: str,
        top_k: int = 5,
        source_fields: list = None,
        description: str = ""
    ):
        """
        动态添加场景配置
        Dynamically add scene configuration

        Args:
            name: 场景名称 / Scene name
            doc_type: 文档类型 / Document type
            prompt_template: Prompt 模板名称 / Prompt template name
            top_k: 召回数量 / Retrieval count
            source_fields: 溯源字段列表 / Source field list
            description: 场景描述 / Scene description

        Example:
            >>> rag.add_scene(
            ...     name="custom_scene",
            ...     doc_type="log",
            ...     prompt_template="fault_diagnosis",
            ...     top_k=10
            ... )
        """
        self.scene_router.scene_config[name] = {
            "doc_type": doc_type,
            "prompt_template": prompt_template,
            "top_k": top_k,
            "source_fields": source_fields or ["chunk_id", "doc_id", "doc_type", "source"],
            "description": description
        }

    def add_metadata_rule(self, field: str, patterns: list, description: str = ""):
        """
        动态添加元数据抽取规则
        Dynamically add metadata extraction rule

        Args:
            field: 字段名称 / Field name
            patterns: 正则模式列表 / Regex pattern list
            description: 规则描述 / Rule description

        Example:
            >>> rag.add_metadata_rule(
            ...     field="custom_field",
            ...     patterns=[r"模式1", r"模式2"],
            ...     description="自定义字段抽取"
            ... )
        """
        self.metadata_extractor.add_metadata_rule(field, patterns, description)

    def update_scene_top_k(self, scene: str, top_k: int):
        """
        更新场景的 top_k 配置
        Update scene top_k configuration

        Args:
            scene: 场景名称 / Scene name
            top_k: 新的召回数量 / New retrieval count
        """
        if scene in self.scene_router.scene_config:
            self.scene_router.scene_config[scene]["top_k"] = top_k

    def set_language(self, language: str):
        """
        切换语言
        Switch language

        Args:
            language: 语言代码 ("zh" | "en") / Language code

        Example:
            >>> rag.set_language("en")  # 切换到英文 / Switch to English
        """
        self.prompt_adapter.set_language(language)
        self.language = language

    # =========================================================================
    # 查询和统计方法 / Query and Statistics Methods
    # =========================================================================

    def get_scenes(self) -> list:
        """
        获取所有可用场景
        Get all available scenes

        Returns:
            场景名称列表 / List of scene names

        Example:
            >>> scenes = rag.get_scenes()
            >>> print(scenes)
            ['fault_diagnosis', 'manual_query', 'work_order_trace', 'default']
        """
        return list(self.scene_router.scene_config.keys())

    def get_doc_types(self) -> list:
        """
        获取所有支持的文档类型
        Get all supported document types

        Returns:
            文档类型列表 / List of document types

        Example:
            >>> doc_types = rag.get_doc_types()
            >>> print(doc_types)
            ['log', 'manual', 'business', 'sop']
        """
        return list(self.splitter_registry._splitters.keys())

    def get_vector_count(self) -> int:
        """
        获取向量库中的向量总数
        Get total vector count in vector store

        Returns:
            向量数量 / Number of vectors

        Example:
            >>> count = rag.get_vector_count()
            >>> print(f"向量总数 / Total vectors: {count}")
        """
        return self.vectorstore.get_count()

    def delete_collection(self):
        """
        删除当前集合
        Delete current collection

        警告：此操作不可逆，会删除所有数据
        Warning: This operation is irreversible and deletes all data

        Example:
            >>> rag.delete_collection()  # 删除所有向量数据 / Delete all vector data
        """
        try:
            self.vectorstore.delete_collection()
        except Exception:
            pass
