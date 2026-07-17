"""
FastMe RAG - 制造业专属 RAG 框架

基于 LangChain 构建，提供制造业场景化能力：
- 4 种制造业专属文档拆解器（日志/手册/工单/SOP）
- 场景化问答路由
- 工业元数据自动抽取
- 配置化驱动
- 支持多种向量库（Chroma、FAISS 等）

快速开始:
    from app_factory import FastMeRAG

    # 使用默认配置（Chroma 向量库）
    rag = FastMeRAG()
    rag.ingest("设备手册.pdf", doc_type="manual")
    result = rag.chat("设备报警怎么处理？", scene="fault_diagnosis")
    print(result["answer"])

    # 使用 FAISS 向量库
    rag = FastMeRAG(
        vector_store_type="faiss",
        vector_store_config={"index_path": "./data/faiss_index"}
    )
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Generator, Any

from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

# 制造业专属组件
from splitters.base import SplitterRegistry
from splitters.log_splitter import LogSplitter
from splitters.manual_splitter import ManualSplitter
from splitters.business_splitter import BusinessSplitter
from splitters.sop_splitter import SopSplitter

from manufacturing.metadata_extractor import IndustrialMetadataExtractor
from routers.scene_router import SceneRouter

# Pipeline 组件
from core.ingest_pipeline import IngestPipeline
from core.chat_pipeline import ChatPipeline
from adapters import SimpleDocumentLoader, PromptAdapter
from core.models import FastMeSearchResult

# 检索器和向量库
from retrievers import RetrieverFactory
from vector_stores import ChromaAdapter, FAISSAdapter, VectorStoreAdapter
from vector_stores.factory import VectorStoreFactory

load_dotenv()

# [必须] 框架日志配置
logger = logging.getLogger("fastme_rag")

# [必须] 初始化日志系统：默认 INFO 级别，用户可在 app.py 中通过 logging.basicConfig 覆盖
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

# [必须] 抑制第三方库日志噪音
for _lib in ["sentence_transformers", "urllib3", "chromadb",
             "httpx", "httpcore", "huggingface_hub", "openai"]:
    logging.getLogger(_lib).setLevel(logging.WARNING)


class FastMeRAG:
    """
    FastMe RAG - 制造业专属 RAG 框架

    支持场景:
        - fault_diagnosis: 故障诊断（基于运维日志、故障记录）
        - manual_query: 设备手册查询
        - work_order_trace: 工单追溯
        - default: 默认问答

    支持文档类型:
        - log: 运维日志
        - manual: 设备手册
        - business: 工单/业务文档
        - sop: 工艺 SOP
    """

    def __init__(
        self,
        embedding_model: str = None,
        model_cache_dir: str = None,
        chroma_dir: str = None,  # 向后兼容，用于 Chroma
        chroma_collection: str = None,  # 向后兼容，用于 Chroma
        llm_base_url: str = None,
        llm_api_key: str = None,
        llm_model: str = None,
        config_dir: str = None,
        temperature: float = 0.2,
        language: str = None,

        # ===== Chunk 与批量处理配置 =====
        chunk_max_size: int = 1000,       # splitter 的 chunk 最大字符数（用于初始化所有 splitter）
        ingest_batch_size: int = 32,      # 入库分批大小
        embedding_batch_size: int = 32,   # Embedding 批量大小
        show_progress_bar: bool = False,  # 显示进度条（ingest 时建议开启，chat 时建议关闭）

        # ===== 向量库配置 =====
        vector_store_type: str = "chroma",  # 向量库类型：chroma, faiss
        vector_store_config: dict = None,    # 向量库特定配置
    ):
        """
        初始化 FastMe RAG

        Args:
            embedding_model: Embedding 模型名称，默认 "BAAI/bge-m3"
            model_cache_dir: 模型缓存目录，默认 "./models"
            chroma_dir: Chroma 数据目录，默认 "./data/chroma"
            chroma_collection: Chroma 集合名称，默认 "fastme_rag"
            llm_base_url: LLM API 地址，默认 "http://localhost:8000/v1/chat/completions"
            llm_api_key: LLM API Key
            llm_model: LLM 模型名称，默认 "qwen-plus"
            config_dir: 配置文件目录，默认 "./config"
            temperature: LLM 温度，默认 0.2
            language: 语言，默认 "zh"（中文），可选 "en"（英文）

            # ===== Chunk 与批量处理配置 =====
            chunk_max_size: 单个 chunk 最大字符数，默认 1000。
                建议值：日志 500-800，手册 1000-1500，工单 800-1200
            ingest_batch_size: 入库分批大小，默认 32。
                内存受限时减小 (16-24)，高性能环境可增大 (64-128)
            embedding_batch_size: Embedding 批量大小，默认 32。
                GPU 用户可增大到 64-128，内存受限用户减小到 8-16
            show_progress_bar: 是否显示进度条，默认 False。
                ingest 大文件时可设置为 True 查看进度，chat 时建议关闭
                API 服务可设置为 False 关闭进度显示
        """
        # 配置目录
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent / "config"

        # 初始化配置（从环境变量或参数）
        self.embedding_model = embedding_model or os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
        self.model_cache_dir = model_cache_dir or os.getenv("MODEL_CACHE_DIR", "./models")
        self.llm_base_url = llm_base_url or os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
        self.llm_api_key = llm_api_key or os.getenv("LLM_API_KEY", "sk-1234567890abcdef1234567890abcdef")
        self.llm_model = llm_model or os.getenv("LLM_MODEL", "qwen-plus")
        self.temperature = temperature
        self.language = language or os.getenv("FASTME_LANGUAGE", "zh")

        # Chunk 与批量处理配置
        self.chunk_max_size = chunk_max_size
        self.ingest_batch_size = ingest_batch_size
        self.embedding_batch_size = embedding_batch_size
        self.show_progress_bar = show_progress_bar

        # 向量库配置
        self.vector_store_type = vector_store_type
        self.vector_store_config = vector_store_config or {}

        # 向后兼容：如果提供了 chroma_dir/chroma_collection，自动填充到 config
        if chroma_dir:
            self.vector_store_config["persist_directory"] = chroma_dir
        if chroma_collection:
            self.vector_store_config["collection_name"] = chroma_collection

        # 保存向后兼容的属性
        self.chroma_dir = self.vector_store_config.get("persist_directory", "./data/chroma")
        self.chroma_collection = self.vector_store_config.get("collection_name", "fastme_rag")

        # [必须] 框架初始化信息
        logger.info("=" * 60)
        logger.info("FastMe RAG 初始化")
        logger.info(f"  Embedding 模型：{self.embedding_model}")
        logger.info(f"  模型缓存目录：{self.model_cache_dir}")
        logger.info(f"  Chroma 目录：{self.chroma_dir}")
        logger.info(f"  Chroma 集合：{self.chroma_collection}")
        logger.info(f"  LLM 模型：{self.llm_model}")
        logger.info(f"  LLM 地址：{self.llm_base_url}")
        logger.info(f"  语言：{self.language}")
        logger.info("=" * 60)

        # ========== LangChain 原语组件 ==========

        # Embedding
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            cache_folder=self.model_cache_dir,
            model_kwargs={"device": "cpu", "trust_remote_code": True},
            encode_kwargs={
                "normalize_embeddings": True,
                "batch_size": self.embedding_batch_size
            },
            show_progress=self.show_progress_bar
        )

        # Vector Store（使用工厂方法）
        self.vectorstore = VectorStoreFactory.create(
            vector_store_type=self.vector_store_type,
            embeddings=self.embeddings,
            vector_store_config=self.vector_store_config
        )


        # LLM
        self.llm = ChatOpenAI(
            model_name=self.llm_model,
            api_key=self.llm_api_key,
            base_url=self.llm_base_url,
            temperature=self.temperature
        )

        # ========== 制造业专属组件 ==========

        # 拆解器注册表
        self.splitter_registry = SplitterRegistry()
        self.splitter_registry.register("log", LogSplitter(max_chunk_size=self.chunk_max_size))
        self.splitter_registry.register("manual", ManualSplitter(max_chunk_size=self.chunk_max_size))
        self.splitter_registry.register("business", BusinessSplitter(max_chunk_size=self.chunk_max_size))
        self.splitter_registry.register("sop", SopSplitter(max_chunk_size=self.chunk_max_size))

        # 元数据抽取器
        self.metadata_extractor = IndustrialMetadataExtractor(
            config_path=self.config_dir / "metadata_rules.yaml"
        )

        # 场景路由
        self.scene_router = SceneRouter(config_path=self.config_dir / "scenes.yaml")

        # Prompt 适配器（支持多语言）
        self.prompt_adapter = PromptAdapter(
            path=self.config_dir / "prompt_templates.yaml",
            field_labels_path=self.config_dir / "field_labels.yaml",
            language=self.language
        )

        # 字段标签加载（支持多语言）- 用于向后兼容
        with open(self.config_dir / "field_labels.yaml", "r", encoding="utf-8") as f:
            all_labels = yaml.safe_load(f)
            self.field_labels = all_labels.get(self.language, all_labels.get("zh", {}))

        # ========== 创建 Pipeline（核心业务逻辑委托给 pipeline） ==========

        # IngestPipeline - 文档入库流水线
        self.ingest_pipeline = IngestPipeline(
            document_loader=SimpleDocumentLoader(),
            splitter_registry=self.splitter_registry,
            metadata_extractor=self.metadata_extractor,
            vector_store=self.vectorstore,
            ingest_batch_size=self.ingest_batch_size,
            show_progress_bar=self.show_progress_bar,
        )

        # 创建场景化检索器（使用工厂方法）
        self.scene_aware_retriever = RetrieverFactory.create(
            vector_store_type=self.vector_store_type,
            vector_store_adapter=self.vectorstore,
            scene_router=self.scene_router,
        )

        # ChatPipeline - 对话流水线（使用 SceneAwareRetriever）
        self.chat_pipeline = ChatPipeline(
            scene_aware_retriever=self.scene_aware_retriever,
            prompt_adapter=self.prompt_adapter,
            llm=self.llm,
        )

        # ========== 直接绑定 Pipeline 方法（消除委托重复） ==========
        # 文档入库
        self.ingest = self.ingest_pipeline.ingest
        self.batch_ingest = self.ingest_pipeline.batch_ingest
        # 场景化问答
        self.chat = self.chat_pipeline.chat
        self.chat_stream = self.chat_pipeline.chat_stream
        # 记忆管理
        self.create_memory = self.chat_pipeline.create_memory
        self.get_memory = self.chat_pipeline.get_memory
        self.clear_memory = self.chat_pipeline.clear_memory
        self.chat_with_memory = self.chat_pipeline.chat_with_memory

    # ========== 配置工具 ==========

    def add_scene(
        self,
        name: str,
        doc_type: str,
        prompt_template: str,
        top_k: int = 5,
        source_fields: list = None,
        description: str = ""
    ):
        """动态添加场景配置"""
        self.scene_router.scene_config[name] = {
            "doc_type": doc_type,
            "prompt_template": prompt_template,
            "top_k": top_k,
            "source_fields": source_fields or ["chunk_id", "doc_id", "doc_type", "source"],
            "description": description
        }
        # 注意：SceneAwareRetriever 会自动使用最新的 scene_config
        # 无需手动更新检索器

    def add_metadata_rule(self, field: str, patterns: list, description: str = ""):
        """动态添加元数据抽取规则"""
        # 委托给 metadata_extractor
        self.metadata_extractor.add_metadata_rule(field, patterns, description)

    def update_scene_top_k(self, scene: str, top_k: int):
        """更新场景的 top_k 配置"""
        if scene in self.scene_router.scene_config:
            self.scene_router.scene_config[scene]["top_k"] = top_k

    def set_language(self, language: str):
        """
        切换语言

        Args:
            language: 语言代码 ("zh" | "en")

        Raises:
            ValueError: 当不支持该语言时
        """
        # 委托给 PromptAdapter 处理语言切换和字段标签加载
        self.prompt_adapter.set_language(language)
        self.language = language
        # 同步 field_labels 以便向后兼容
        self.field_labels = self.prompt_adapter.field_labels

    # ========== 查询和统计 ==========

    def get_scenes(self) -> list:
        """获取所有可用场景"""
        return list(self.scene_router.scene_config.keys())

    def get_doc_types(self) -> list:
        """获取所有支持的文档类型"""
        return list(self.splitter_registry._splitters.keys())

    def get_vector_count(self) -> int:
        """获取向量库中的向量总数"""
        return self.vectorstore.get_count()

    def delete_collection(self):
        """删除当前集合"""
        try:
            self.vectorstore.delete_collection()
        except Exception:
            pass
