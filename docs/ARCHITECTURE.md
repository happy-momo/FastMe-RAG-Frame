# FastMe RAG 架构设计文档

## 📋 目录

- [整体架构概览](#整体架构概览)
- [核心设计理念](#核心设计理念)
- [模块详细设计](#模块详细设计)
- [场景路由机制](#场景路由机制)
- [Splitter 拆解器架构](#splitter-拆解器架构)
- [向量库适配器架构](#向量库适配器架构)
- [完整的调用链路](#完整的调用链路)
- [模块解耦设计](#模块解耦设计)

---

## 整体架构概览

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户层 (User Layer)                     │
│                                                               │
│  rag = FastMeRAG()                                           │
│  rag.ingest("manual.pdf", doc_type="manual")                 │
│  rag.chat("设备报警?", scene="fault_diagnosis")              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│               应用层 (Application Layer)                      │
│                                                               │
│  ┌─────────────────┐          ┌─────────────────┐           │
│  │  FastMeRAG      │          │                 │           │
│  │  (app_factory)  │──────────┤   配置管理      │           │
│  │                 │          │   (config/)     │           │
│  └────────┬────────┘          └─────────────────┘           │
│           │                                                   │
│           ├──────────┬─────────────┬──────────────┐         │
│           ↓          ↓             ↓              ↓         │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│    │ Ingest   │ │   Chat   │ │  Scene   │ │Metadata  │    │
│    │ Pipeline │ │ Pipeline │ │  Router  │ │Extractor │    │
│    └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                业务层 (Business Layer)                        │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Splitters  │  │  Retrievers │  │   Adapters  │         │
│  │  (拆解器)   │  │  (检索器)   │  │  (适配器)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│               基础设施层 (Infrastructure Layer)               │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ ChromaDB    │  │   FAISS     │  │  Qdrant     │  ...    │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐                           │
│  │ HuggingFace │  │   OpenAI    │                           │
│  │ Embeddings  │  │    LLM      │                           │
│  └─────────────┘  └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心设计理念

### 1. 分层架构

| 层级 | 职责 | 关键组件 |
|------|------|---------|
| **用户层** | 提供简单易用的 API | `FastMeRAG` |
| **应用层** | 编排业务流程 | `IngestPipeline`, `ChatPipeline` |
| **业务层** | 实现具体业务逻辑 | `Splitters`, `Retrievers`, `Adapters` |
| **基础设施层** | 提供底层服务 | `ChromaDB`, `FAISS`, `LLM` |

---

### 2. 设计模式

#### 2.1 工厂模式 (Factory Pattern)

**用途：** 根据配置创建不同类型的对象

```python
# 文件：vector_stores/factory.py
class VectorStoreFactory:
    @staticmethod
    def create(vector_store_type, embeddings, config):
        if vector_store_type == "chroma":
            return ChromaAdapter(...)
        elif vector_store_type == "faiss":
            return FAISSAdapter(...)
```

**优点：**
- 解耦对象创建和使用
- 支持运行时切换实现

---

#### 2.2 适配器模式 (Adapter Pattern)

**用途：** 统一不同向量库的接口

```python
# 文件：vector_stores/base.py
class VectorStoreAdapter(ABC):
    @abstractmethod
    def add_documents(self, documents, ids=None):
        pass
    
    @abstractmethod
    def similarity_search_with_score(self, query, k=5, filter=None):
        pass

# 文件：vector_stores/chroma.py
class ChromaAdapter(VectorStoreAdapter):
    def add_documents(self, documents, ids=None):
        # Chroma 特定实现
        
# 文件：vector_stores/faiss.py
class FAISSAdapter(VectorStoreAdapter):
    def add_documents(self, documents, ids=None):
        # FAISS 特定实现
```

**优点：**
- 上层代码只依赖抽象接口
- 切换向量库无需修改业务代码

---

#### 2.3 策略模式 (Strategy Pattern)

**用途：** 不同文档类型使用不同的拆解策略

```python
# 文件：splitters/base.py
class BaseSplitter(ABC):
    @abstractmethod
    def split(self, document):
        pass

# 文件：splitters/log_splitter.py
class LogSplitter(BaseSplitter):
    def split(self, document):
        # 日志特定拆解逻辑

# 文件：splitters/manual_splitter.py
class ManualSplitter(BaseSplitter):
    def split(self, document):
        # 手册特定拆解逻辑
```

**优点：**
- 新增文档类型只需添加新的 Splitter
- 运行时动态选择策略

---

#### 2.4 注册表模式 (Registry Pattern)

**用途：** 管理 Splitter 的注册和获取

```python
# 文件：splitters/base.py
class SplitterRegistry:
    def __init__(self):
        self._splitters = {}
    
    def register(self, doc_type, splitter):
        self._splitters[doc_type] = splitter
    
    def get(self, doc_type):
        return self._splitters.get(doc_type)
```

**优点：**
- 解耦注册和使用
- 支持动态注册新的 Splitter

---

## 模块详细设计

### 模块 1：FastMeRAG（主入口）

**文件位置：** `app_factory.py`

**职责：**
- 初始化所有组件
- 编排 IngestPipeline 和 ChatPipeline
- 提供统一的用户接口

**核心代码：**

```python
# 文件：app_factory.py (line 95-284)
class FastMeRAG:
    def __init__(
        self,
        vector_store_type: str = "chroma",
        vector_store_config: dict = None,
        ...
    ):
        # 1. 创建 Embedding 模型
        self.embeddings = HuggingFaceEmbeddings(...)
        
        # 2. 使用工厂创建向量库（支持切换）
        self.vectorstore = VectorStoreFactory.create(
            vector_store_type=vector_store_type,
            embeddings=self.embeddings,
            vector_store_config=vector_store_config
        )
        
        # 3. 创建 LLM
        self.llm = ChatOpenAI(...)
        
        # 4. 注册 Splitter
        self.splitter_registry = SplitterRegistry()
        self.splitter_registry.register("log", LogSplitter(...))
        self.splitter_registry.register("manual", ManualSplitter(...))
        self.splitter_registry.register("business", BusinessSplitter(...))
        self.splitter_registry.register("sop", SopSplitter(...))
        
        # 5. 创建元数据提取器
        self.metadata_extractor = IndustrialMetadataExtractor(...)
        
        # 6. 创建场景路由器
        self.scene_router = SceneRouter(...)
        
        # 7. 创建 IngestPipeline
        self.ingest_pipeline = IngestPipeline(
            document_loader=SimpleDocumentLoader(),
            splitter_registry=self.splitter_registry,
            metadata_extractor=self.metadata_extractor,
            vector_store=self.vectorstore,
            ...
        )
        
        # 8. 创建检索器（使用工厂）
        self.scene_aware_retriever = RetrieverFactory.create(
            vector_store_type=vector_store_type,
            vector_store_adapter=self.vectorstore,
            scene_router=self.scene_router,
        )
        
        # 9. 创建 ChatPipeline
        self.chat_pipeline = ChatPipeline(
            scene_aware_retriever=self.scene_aware_retriever,
            prompt_adapter=self.prompt_adapter,
            llm=self.llm,
        )
        
        # 10. 方法绑定（消除委托）
        self.ingest = self.ingest_pipeline.ingest
        self.chat = self.chat_pipeline.chat
```

**设计亮点：**
- ✅ 所有组件通过参数注入，支持替换
- ✅ 使用工厂方法创建向量库和检索器
- ✅ 方法绑定避免委托方法重复

---

## 场景路由机制

### 架构图

```
用户问题: "E001 设备报警怎么处理？"
         ↓
┌────────────────────────────────────────┐
│     ChatPipeline.chat()                │
│     (core/chat_pipeline.py)             │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│   SceneAwareRetriever.retrieve()       │
│   (retrievers/scene_aware.py)           │
│                                          │
│   scene = "fault_diagnosis"             │
│   question = "E001 设备报警怎么处理？"   │
│   filters = {"device_id": "EQ001"}      │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│   SceneRouter.route(scene)              │
│   (routers/scene_router.py)              │
│                                          │
│   返回场景配置：                          │
│   {                                      │
│     "doc_type": "log",                  │
│     "prompt_template": "fault_diagnosis",│
│     "top_k": 5,                         │
│     "source_fields": [...]              │
│   }                                      │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│   SceneRouter.build_filter()            │
│                                          │
│   根据场景配置构建过滤条件：               │
│   {"doc_type": "log"}                   │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│   BaseRetriever.retrieve()              │
│   (ChromaRetriever / FAISSRetriever)    │
│                                          │
│   执行检索：                              │
│   - query = "E001 设备报警"              │
│   - top_k = 5                           │
│   - filter = {"doc_type": "log"}        │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│   VectorStoreAdapter                     │
│   .similarity_search_with_score()       │
│                                          │
│   ChromaAdapter: 原生过滤                 │
│   FAISSAdapter: 后过滤                   │
└────────────────────────────────────────┘
```

---

### 详细代码实现

#### 1. SceneRouter（场景路由器）

**文件位置：** `routers/scene_router.py`

```python
# 文件：routers/scene_router.py (line 20-120)
class SceneRouter:
    """
    场景路由器
    
    职责：
    1. 加载场景配置（从 YAML）
    2. 根据场景名称返回配置
    3. 构建元数据过滤条件
    """
    
    def __init__(self, config_path: str):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        self.scene_config = config.get("scenes", {})
    
    def route(self, scene: str) -> dict:
        """
        路由到具体场景配置
        
        Args:
            scene: 场景名称（如 "fault_diagnosis"）
        
        Returns:
            场景配置字典：
            {
                "doc_type": "log",
                "prompt_template": "fault_diagnosis",
                "top_k": 5,
                "source_fields": ["chunk_id", "device_id", ...]
            }
        """
        if scene not in self.scene_config:
            logger.warning(f"场景 {scene} 不存在，使用默认场景")
            scene = "default"
        
        return self.scene_config[scene]
    
    def build_filter(
        self,
        scene: str,
        user_filter: dict = None
    ) -> dict:
        """
        构建过滤条件
        
        流程：
        1. 从场景配置获取 doc_type
        2. 合并用户提供的过滤条件
        
        Args:
            scene: 场景名称
            user_filter: 用户额外过滤条件（如 {"device_id": "EQ001"}）
        
        Returns:
            合并后的过滤条件：
            {
                "doc_type": "log",      # 来自场景配置
                "device_id": "EQ001"    # 来自用户
            }
        """
        scene_config = self.route(scene)
        
        filter_dict = {}
        
        # 1. 添加场景默认过滤（doc_type）
        if scene_config.get("doc_type"):
            filter_dict["doc_type"] = scene_config["doc_type"]
        
        # 2. 合并用户过滤条件
        if user_filter:
            filter_dict.update(user_filter)
        
        return filter_dict
    
    def get_source_fields(self, scene: str) -> list:
        """
        获取场景的溯源字段列表
        
        Args:
            scene: 场景名称
        
        Returns:
            字段列表：["chunk_id", "device_id", "fault_code", ...]
        """
        scene_config = self.route(scene)
        return scene_config.get("source_fields", [])
```

**配置文件示例：** `config/scenes.yaml`

```yaml
scenes:
  fault_diagnosis:
    doc_type: log                        # 对应的文档类型
    prompt_template: fault_diagnosis     # Prompt 模板
    top_k: 5                             # 召回数量
    source_fields:                       # 溯源字段
      - chunk_id
      - doc_id
      - device_id
      - fault_code
      - timestamp
    description: "设备故障诊断"
```

---

#### 2. SceneAwareRetriever（场景感知检索器）

**文件位置：** `retrievers/scene_aware.py`

```python
# 文件：retrievers/scene_aware.py (line 20-100)
class SceneAwareRetriever:
    """
    场景感知检索器（装饰器模式）
    
    职责：
    1. 包装 BaseRetriever
    2. 集成 SceneRouter
    3. 自动构建过滤条件
    """
    
    def __init__(
        self,
        base_retriever: BaseRetriever,
        scene_router: SceneRouter
    ):
        self.base_retriever = base_retriever
        self.scene_router = scene_router
    
    def retrieve(
        self,
        question: str,
        scene: str,
        filters: dict = None,
        top_k: int = None
    ) -> Tuple[List[FastMeSearchResult], List[str]]:
        """
        执行场景化检索
        
        流程：
        1. 从 SceneRouter 获取场景配置
        2. 构建过滤条件
        3. 调用 BaseRetriever 执行检索
        4. 返回结果和溯源字段
        
        Args:
            question: 用户问题
            scene: 场景名称
            filters: 额外过滤条件
            top_k: 召回数量（None 时使用场景配置）
        
        Returns:
            (检索结果列表, 溯源字段列表)
        """
        # 1. 获取场景配置
        scene_config = self.scene_router.route(scene)
        
        # 2. 获取 top_k（优先使用参数，否则使用场景配置）
        if top_k is None:
            top_k = scene_config.get("top_k", 5)
        
        # 3. 构建过滤条件
        filter_dict = self.scene_router.build_filter(scene, filters)
        
        # 4. 调用 BaseRetriever 执行检索
        results = self.base_retriever.retrieve(
            query=question,
            top_k=top_k,
            filters=self._convert_to_filter_conditions(filter_dict)
        )
        
        # 5. 获取溯源字段
        source_fields = self.scene_router.get_source_fields(scene)
        
        return results, source_fields
    
    def supports_filter(self) -> bool:
        """代理到 BaseRetriever"""
        return self.base_retriever.supports_filter()
```

---

## Splitter 拆解器架构

### 架构图

```
文档入库流程
         ↓
┌────────────────────────────────────────┐
│   IngestPipeline.ingest()              │
│   (core/ingest_pipeline.py)             │
│                                          │
│   file_path = "manual.pdf"              │
│   doc_type = "manual"                   │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│   SplitterRegistry.get(doc_type)        │
│   (splitters/base.py)                    │
│                                          │
│   返回：ManualSplitter 实例              │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│   ManualSplitter.split(document)        │
│   (splitters/manual_splitter.py)         │
│                                          │
│   流程：                                  │
│   1. 识别章节结构                         │
│   2. 拆分超大段落                         │
│   3. 生成 chunk_id                       │
│   4. 构建 metadata                       │
│   5. 返回 FastMeChunk 列表               │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│   返回：List[FastMeChunk]                │
│   [                                      │
│     FastMeChunk(                         │
│       chunk_id="doc_001_0",             │
│       text="第一章...",                  │
│       metadata={"chapter_num": "1"}     │
│     ),                                   │
│     ...                                  │
│   ]                                      │
└────────────────────────────────────────┘
```

---

### 详细代码实现

#### 1. BaseSplitter（抽象基类）

**文件位置：** `splitters/base.py`

```python
# 文件：splitters/base.py (line 45-320)
class BaseSplitter(ABC):
    """
    拆解器抽象基类
    
    职责：
    1. 定义统一接口（split 方法）
    2. 提供通用工具方法
    """
    
    def __init__(self, max_chunk_size: int = 1000):
        self.max_chunk_size = max_chunk_size
    
    @abstractmethod
    def split(self, document: FastMeDocument) -> List[FastMeChunk]:
        """
        拆分文档为多个 chunk（子类实现）
        
        Args:
            document: FastMeDocument 实例
        
        Returns:
            FastMeChunk 列表
        """
        pass
    
    # ========== 通用工具方法 ==========
    
    def _generate_chunk_id(
        self,
        doc_id: str,
        chunk_index: int,
        total_sub_chunks: int = 1,
        sub_chunk_index: int = 0
    ) -> str:
        """
        生成 chunk ID
        
        格式：
        - 普通情况：{doc_id}_{chunk_index}
        - 子 chunk：{doc_id}_{chunk_index}_part{sub_idx}of{total}
        """
        if total_sub_chunks == 1:
            return f"{doc_id}_{chunk_index}"
        else:
            return f"{doc_id}_{chunk_index}_part{sub_chunk_index + 1}of{total_sub_chunks}"
    
    def _build_chunk_metadata(
        self,
        document: FastMeDocument,
        chunk_id: str,
        sub_chunks: list,
        sub_idx: int,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        构建 chunk 元数据（通用逻辑）
        
        所有 splitter 子类可以复用此方法。
        """
        metadata = {
            **document.metadata,
            "doc_id": document.doc_id,
            "doc_type": document.doc_type,
            "chunk_id": chunk_id,
            "splitter": self.__class__.__name__.lower().replace("splitter", "_splitter"),
            "is_sub_chunk": len(sub_chunks) > 1,
            "sub_chunk_index": sub_idx if len(sub_chunks) > 1 else None,
            "sub_chunk_total": len(sub_chunks) if len(sub_chunks) > 1 else None
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        return metadata
```

---

#### 2. LogSplitter（日志拆解器）

**文件位置：** `splitters/log_splitter.py`

```python
# 文件：splitters/log_splitter.py (line 15-148)
class LogSplitter(BaseSplitter):
    """
    日志拆解器
    
    特点：
    1. 按时间戳识别日志条目
    2. 提取故障码、设备 ID 等元数据
    """
    
    def __init__(self, max_chunk_size: int = 1000):
        super().__init__(max_chunk_size)
        # 时间戳识别模式
        self.timestamp_pattern = re.compile(
            r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
        )
    
    def split(self, document: FastMeDocument) -> List[FastMeChunk]:
        """
        拆分日志文档
        
        流程：
        1. 按时间戳分割日志条目
        2. 拆分超大条目（超过 max_chunk_size）
        3. 提取时间戳元数据
        4. 生成 FastMeChunk
        """
        lines = document.text.splitlines()
        
        # 1. 按时间戳识别条目
        entries = []
        current = []
        
        for line in lines:
            if self.timestamp_pattern.match(line.strip()):
                if current:
                    entries.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
        
        if current:
            entries.append("\n".join(current))
        
        # 2. 拆分超大条目并生成 chunks
        chunks = []
        chunk_index = 0
        
        for entry in entries:
            # 拆分超大条目
            sub_chunks = self._split_large_entry(entry)
            
            for sub_idx, sub_text in enumerate(sub_chunks):
                # 使用基类方法生成 chunk_id
                sub_chunk_id = self._generate_chunk_id(
                    document.doc_id, chunk_index, len(sub_chunks), sub_idx
                )
                
                # 使用基类方法构建 metadata
                metadata = self._build_chunk_metadata(
                    document, sub_chunk_id, sub_chunks, sub_idx,
                    extra_metadata={}
                )
                
                # 提取时间戳
                timestamp_match = self.timestamp_pattern.match(sub_text)
                if timestamp_match:
                    metadata["timestamp"] = timestamp_match.group(1)
                
                # 创建 FastMeChunk
                chunks.append(FastMeChunk(
                    chunk_id=metadata["chunk_id"],
                    doc_id=metadata["doc_id"],
                    doc_type=metadata["doc_type"],
                    text=sub_text,
                    metadata=metadata
                ))
                
                chunk_index += 1
        
        return chunks
```

---

#### 3. SplitterRegistry（注册表）

**文件位置：** `splitters/base.py`

```python
# 文件：splitters/base.py (line 18-43)
class SplitterRegistry:
    """
    拆解器注册表
    
    职责：
    1. 管理不同文档类型的 Splitter
    2. 支持动态注册
    """
    
    def __init__(self):
        self._splitters = {}
    
    def register(self, doc_type: str, splitter: BaseSplitter):
        """注册拆解器"""
        self._splitters[doc_type] = splitter
    
    def get(self, doc_type: str) -> BaseSplitter:
        """获取指定文档类型的拆解器"""
        splitter = self._splitters.get(doc_type)
        if not splitter:
            raise ValueError(f"Splitter not registered for doc type: {doc_type}")
        return splitter
```

**使用方式：**

```python
# 文件：app_factory.py (line 220-225)
# 注册 Splitter
self.splitter_registry = SplitterRegistry()
self.splitter_registry.register("log", LogSplitter(max_chunk_size=self.chunk_max_size))
self.splitter_registry.register("manual", ManualSplitter(max_chunk_size=self.chunk_max_size))
self.splitter_registry.register("business", BusinessSplitter(max_chunk_size=self.chunk_max_size))
self.splitter_registry.register("sop", SopSplitter(max_chunk_size=self.chunk_max_size))
```

---

## 向量库适配器架构

### 架构图

```
用户调用
         ↓
┌────────────────────────────────────────┐
│   FastMeRAG.__init__()                  │
│   (app_factory.py)                       │
│                                          │
│   vector_store_type = "chroma"          │
│   vector_store_config = {...}           │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│   VectorStoreFactory.create()           │
│   (vector_stores/factory.py)             │
│                                          │
│   根据 vector_store_type 创建实例：       │
│   - "chroma" → ChromaAdapter             │
│   - "faiss" → FAISSAdapter               │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│   VectorStoreAdapter (抽象基类)          │
│   (vector_stores/base.py)                │
│                                          │
│   定义统一接口：                           │
│   - add_documents(documents, ids)       │
│   - similarity_search_with_score(...)   │
│   - get_count()                         │
│   - delete_collection()                 │
└────────────────┬───────────────────────┘
                 ↓
       ┌─────────┴─────────┐
       ↓                   ↓
┌─────────────┐     ┌─────────────┐
│ChromaAdapter│     │FAISSAdapter │
│(chroma.py)  │     │(faiss.py)   │
└─────────────┘     └─────────────┘
       ↓                   ↓
┌─────────────┐     ┌─────────────┐
│ ChromaDB    │     │   FAISS     │
│ (原生库)    │     │ (原生库)    │
└─────────────┘     └─────────────┘
```

---

### 详细代码实现

#### 1. VectorStoreAdapter（抽象基类）

**文件位置：** `vector_stores/base.py`

```python
# 文件：vector_stores/base.py (line 20-150)
class VectorStoreAdapter(ABC):
    """
    向量库适配器抽象基类
    
    职责：
    1. 定义统一的接口
    2. 提供元数据清洗等通用方法
    """
    
    @abstractmethod
    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        添加文档到向量库
        
        Args:
            documents: 文档列表
            ids: 可选的文档 ID 列表
        """
        pass
    
    @abstractmethod
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        带分数的相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter: 元数据过滤条件
        
        Returns:
            (文档, 分数) 元组列表
        """
        pass
    
    @abstractmethod
    def get_count(self) -> int:
        """获取向量总数"""
        pass
    
    @abstractmethod
    def delete_collection(self) -> None:
        """删除整个集合"""
        pass
    
    @staticmethod
    def sanitize_metadata(metadata: dict) -> dict:
        """
        清洗元数据（只保留简单类型）
        
        ChromaDB 只接受 str/int/float/bool 类型
        """
        clean = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                clean[key] = value
            elif value is not None:
                clean[key] = str(value)
        return clean
```

---

#### 2. ChromaAdapter（Chroma 适配器）

**文件位置：** `vector_stores/chroma.py`

```python
# 文件：vector_stores/chroma.py (line 47-265)
class ChromaAdapter(VectorStoreAdapter):
    """
    Chroma 向量库适配器
    
    特点：
    1. 支持持久化到磁盘
    2. 原生支持元数据过滤
    3. 支持 Collection 隔离
    """
    
    def __init__(
        self,
        collection_name: str,
        persist_directory: str,
        embedding_function
    ):
        self._collection_name = collection_name
        self._persist_directory = persist_directory
        self._embedding_function = embedding_function
        
        # 创建 Chroma 实例
        self._chroma = Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=embedding_function
        )
    
    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        添加文档到 Chroma
        
        流程：
        1. 清洗元数据
        2. 调用 LangChain Chroma 的 add_documents
        """
        # 清洗元数据
        clean_docs = []
        for doc in documents:
            clean_metadata = self.sanitize_metadata(doc.metadata)
            clean_docs.append(Document(
                page_content=doc.page_content,
                metadata=clean_metadata
            ))
        
        # 添加到 Chroma
        if ids:
            self._chroma.add_documents(documents=clean_docs, ids=ids)
        else:
            self._chroma.add_documents(documents=clean_docs)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        带分数的相似度搜索（原生支持过滤）
        """
        results = self._chroma.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter  # Chroma 原生支持
        )
        return results
    
    def get_count(self) -> int:
        """获取向量总数"""
        return len(self._chroma.get()["ids"])
    
    def supports_filter(self) -> bool:
        """Chroma 支持元数据过滤"""
        return True
```

---

#### 3. FAISSAdapter（FAISS 适配器）

**文件位置：** `vector_stores/faiss.py`

```python
# 文件：vector_stores/faiss.py (line 40-290)
class FAISSAdapter(VectorStoreAdapter):
    """
    FAISS 向量库适配器
    
    特点：
    1. 内存存储（高性能）
    2. 支持持久化到磁盘
    3. 不支持原生元数据过滤（使用后过滤策略）
    """
    
    def __init__(
        self,
        embedding_function,
        index_path: str = None
    ):
        self._embedding_function = embedding_function
        self._index_path = index_path
        
        # 创建或加载 FAISS 索引
        if index_path and os.path.exists(index_path):
            self._faiss = FAISS.load_local(
                index_path,
                embedding_function,
                allow_dangerous_deserialization=True
            )
        else:
            self._faiss = None  # 空索引
    
    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> None:
        """添加文档"""
        if self._faiss is None:
            # 第一次添加
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            self._faiss = FAISS.from_texts(
                texts,
                self._embedding_function,
                metadatas=metadatas
            )
        else:
            # 追加
            texts = [doc.page_content for doc in documents]
            metadatas = [self.sanitize_metadata(doc.metadata) for doc in documents]
            self._faiss.add_texts(texts, metadatas=metadatas)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        带分数的相似度搜索（后过滤策略）
        
        流程：
        1. 先检索 top_k * multiplier 个结果
        2. 按 filter 条件过滤
        3. 返回 top_k 个结果
        """
        # 如果没有过滤条件，直接检索
        if filter is None:
            return self._faiss.similarity_search_with_score(query, k=k)
        
        # 有过滤条件，使用后过滤策略
        multiplier = 5  # 扩大检索数量
        results = self._faiss.similarity_search_with_score(
            query,
            k=k * multiplier
        )
        
        # 后过滤
        filtered = []
        for doc, score in results:
            if self._match_filter(doc.metadata, filter):
                filtered.append((doc, score))
                if len(filtered) >= k:
                    break
        
        return filtered
    
    def supports_filter(self) -> bool:
        """FAISS 支持元数据过滤（后过滤）"""
        return True
```

---

#### 4. VectorStoreFactory（向量库工厂）

**文件位置：** `vector_stores/factory.py`

```python
# 文件：vector_stores/factory.py (line 37-104)
class VectorStoreFactory:
    """
    向量库工厂
    
    职责：
    根据配置创建对应的向量库适配器实例
    """
    
    @staticmethod
    def create(
        vector_store_type: str,
        embeddings,
        vector_store_config: Dict[str, Any]
    ) -> VectorStoreAdapter:
        """
        创建向量库适配器
        
        Args:
            vector_store_type: 向量库类型（"chroma" | "faiss"）
            embeddings: Embedding 函数
            vector_store_config: 向量库特定配置
        
        Returns:
            VectorStoreAdapter 实例
        """
        if vector_store_type == "chroma":
            return ChromaAdapter(
                collection_name=vector_store_config.get("collection_name", "fastme_rag"),
                persist_directory=vector_store_config.get("persist_directory", "./data/chroma"),
                embedding_function=embeddings
            )
        
        elif vector_store_type == "faiss":
            return FAISSAdapter(
                embedding_function=embeddings,
                index_path=vector_store_config.get("index_path", "./data/faiss_index")
            )
        
        else:
            raise ValueError(
                f"Unsupported vector store type: {vector_store_type}. "
                f"Supported types: chroma, faiss"
            )
```

---

#### 5. RetrieverFactory（检索器工厂）

**文件位置：** `retrievers/factory.py`

```python
# 文件：retrievers/factory.py (line 17-92)
class RetrieverFactory:
    """
    检索器工厂
    
    职责：
    1. 创建 BaseRetriever 实例
    2. 包装为 SceneAwareRetriever
    """
    
    @staticmethod
    def create(
        vector_store_type: str,
        vector_store_adapter: VectorStoreAdapter,
        scene_router: SceneRouter,
        retriever_config: Optional[Dict[str, Any]] = None
    ) -> BaseRetriever:
        """
        创建检索器
        
        流程：
        1. 根据 vector_store_type 创建对应的 Retriever
        2. 包装为 SceneAwareRetriever
        
        Args:
            vector_store_type: 向量库类型
            vector_store_adapter: VectorStoreAdapter 实例
            scene_router: SceneRouter 实例
            retriever_config: 检索器额外配置
        
        Returns:
            SceneAwareRetriever 实例
        """
        retriever_config = retriever_config or {}
        
        # 1. 创建基础检索器
        if vector_store_type == "chroma":
            from vector_stores.chroma_retriever import ChromaRetriever
            base_retriever = ChromaRetriever(vector_store_adapter)
        
        elif vector_store_type == "faiss":
            from vector_stores.faiss_retriever import FAISSRetriever
            post_filter_multiplier = retriever_config.get("post_filter_multiplier", 5)
            base_retriever = FAISSRetriever(
                vector_store_adapter,
                post_filter_multiplier=post_filter_multiplier
            )
        
        else:
            raise ValueError(f"Unsupported vector store type: {vector_store_type}")
        
        # 2. 包装为场景感知检索器
        from retrievers.scene_aware import SceneAwareRetriever
        scene_aware_retriever = SceneAwareRetriever(base_retriever, scene_router)
        
        return scene_aware_retriever
```

---

## 完整的调用链路

### 链路 1：文档入库流程

```
┌────────────────────────────────────────────────────────────┐
│ 用户调用                                                     │
│ rag.ingest("manual.pdf", doc_type="manual")                │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ FastMeRAG.ingest()                                          │
│ 文件：app_factory.py (line 275)                             │
│                                                             │
│ self.ingest = self.ingest_pipeline.ingest  # 方法绑定       │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ IngestPipeline.ingest()                                     │
│ 文件：core/ingest_pipeline.py (line 93-228)                │
│                                                             │
│ 流程：                                                       │
│ 1. 加载文档 → FastMeDocument                                │
│ 2. 拆分文档 → List[FastMeChunk]                             │
│ 3. 提取元数据                                                │
│ 4. 分批入库                                                  │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 步骤 1：加载文档                                             │
│ SimpleDocumentLoader.load()                                 │
│ 文件：adapters/document_loader.py                           │
│                                                             │
│ 输入：file_path, doc_type, extra_metadata                   │
│ 输出：FastMeDocument(                                       │
│     doc_id="doc_20240115_abc123",                          │
│     doc_type="manual",                                      │
│     text="文档全文...",                                      │
│     metadata={...}                                          │
│ )                                                           │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 步骤 2：拆分文档                                             │
│ SplitterRegistry.get("manual")                              │
│ 文件：splitters/base.py (line 37-42)                       │
│                                                             │
│ 返回：ManualSplitter 实例                                    │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ ManualSplitter.split(document)                              │
│ 文件：splitters/manual_splitter.py (line 88-219)           │
│                                                             │
│ 流程：                                                       │
│ 1. 识别章节结构                                              │
│ 2. 拆分超大段落                                              │
│ 3. 生成 chunk_id（使用基类方法）                             │
│ 4. 构建 metadata（使用基类方法）                             │
│                                                             │
│ 输出：List[FastMeChunk]                                     │
│ [                                                           │
│   FastMeChunk(                                              │
│     chunk_id="doc_001_0",                                   │
│     text="第一章...",                                        │
│     metadata={"chapter_num": "1", ...}                     │
│   ),                                                        │
│   ...                                                       │
│ ]                                                           │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 步骤 3：提取元数据                                           │
│ IndustrialMetadataExtractor.enrich_chunk(chunks)           │
│ 文件：manufacturing/metadata_extractor.py                   │
│                                                             │
│ 流程：                                                       │
│ 1. 遍历每个 chunk                                           │
│ 2. 应用元数据抽取规则（正则匹配）                            │
│ 3. 更新 chunk.metadata                                      │
│                                                             │
│ 提取字段：                                                   │
│ - device_id: "EQ001"                                        │
│ - device_model: "EQ-1000"                                   │
│ - ...                                                       │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 步骤 4：分批入库                                             │
│ for batch_chunks in chunks:                                 │
│     # 构建 Document 列表                                     │
│     docs = [Document(                                       │
│         page_content=chunk.text,                            │
│         metadata={                                          │
│             "chunk_id": chunk.chunk_id,                     │
│             "doc_id": chunk.doc_id,                         │
│             **chunk.metadata                                │
│         }                                                   │
│     )]                                                      │
│                                                             │
│     # 提取 ID 列表                                           │
│     batch_ids = [chunk.chunk_id for chunk in batch_chunks] │
│                                                             │
│     # 调用向量库                                             │
│     self.vector_store.add_documents(docs, ids=batch_ids)   │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ ChromaAdapter.add_documents(docs, ids)                      │
│ 文件：vector_stores/chroma.py (line 120-150)               │
│                                                             │
│ 流程：                                                       │
│ 1. 清洗元数据（只保留 str/int/float/bool）                  │
│ 2. if ids: 传入 ids 参数                                    │
│    else: 不传 ids，自动生成 UUID                            │
│ 3. 调用 LangChain Chroma 的 add_documents                   │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ LangChain Chroma.add_documents()                            │
│ 文件：langchain_chroma (第三方库)                           │
│                                                             │
│ 流程：                                                       │
│ 1. 提取 texts 和 metadatas                                  │
│ 2. 生成 embeddings                                          │
│ 3. 调用 ChromaDB upsert                                     │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ ChromaDB 存储                                                │
│ 向量库中的数据：                                             │
│ {                                                           │
│   id: "doc_001_0",                                          │
│   embedding: [0.1, 0.2, ...],                              │
│   document: "第一章...",                                     │
│   metadata: {                                               │
│     "chunk_id": "doc_001_0",                               │
│     "doc_id": "doc_001",                                   │
│     "chapter_num": "1",                                     │
│     ...                                                     │
│   }                                                         │
│ }                                                           │
└────────────────────────────────────────────────────────────┘
```

---

### 链路 2：场景化问答流程

```
┌────────────────────────────────────────────────────────────┐
│ 用户调用                                                     │
│ result = rag.chat(                                          │
│     "E001 设备报警怎么处理？",                               │
│     scene="fault_diagnosis",                                │
│     filters={"device_id": "EQ001"}                         │
│ )                                                           │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ FastMeRAG.chat()                                            │
│ 文件：app_factory.py (line 278)                             │
│                                                             │
│ self.chat = self.chat_pipeline.chat  # 方法绑定             │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ ChatPipeline.chat()                                         │
│ 文件：core/chat_pipeline.py (line 81-162)                  │
│                                                             │
│ 流程：                                                       │
│ 1. 场景化检索                                                │
│ 2. 格式化上下文                                              │
│ 3. 获取 Prompt 模板                                         │
│ 4. 调用 LLM                                                  │
│ 5. 构建溯源信息                                              │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 步骤 1：场景化检索                                           │
│ self.scene_aware_retriever.retrieve(                       │
│     question="E001 设备报警怎么处理？",                      │
│     scene="fault_diagnosis",                                │
│     filters={"device_id": "EQ001"}                         │
│ )                                                           │
│ 文件：retrievers/scene_aware.py (line 35-70)               │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ SceneAwareRetriever.retrieve()                              │
│ 文件：retrievers/scene_aware.py                             │
│                                                             │
│ 步骤 1：获取场景配置                                         │
│ scene_config = self.scene_router.route("fault_diagnosis")  │
│ 返回：{                                                     │
│   "doc_type": "log",                                        │
│   "prompt_template": "fault_diagnosis",                    │
│   "top_k": 5,                                               │
│   "source_fields": ["device_id", "fault_code", ...]       │
│ }                                                           │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 步骤 2：构建过滤条件                                         │
│ filter_dict = self.scene_router.build_filter(              │
│     scene="fault_diagnosis",                                │
│     user_filter={"device_id": "EQ001"}                     │
│ )                                                           │
│                                                             │
│ 返回：{                                                     │
│   "doc_type": "log",        # 来自场景配置                  │
│   "device_id": "EQ001"      # 来自用户                      │
│ }                                                           │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 步骤 3：调用基础检索器                                       │
│ results = self.base_retriever.retrieve(                    │
│     query="E001 设备报警",                                  │
│     top_k=5,                                                │
│     filters=[FilterCondition(...)]                         │
│ )                                                           │
│ 文件：vector_stores/chroma_retriever.py                     │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ ChromaRetriever.retrieve()                                  │
│ 文件：vector_stores/chroma_retriever.py (line 20-60)       │
│                                                             │
│ 流程：                                                       │
│ 1. 转换过滤条件为 Chroma 格式                                │
│ 2. 调用 ChromaAdapter.similarity_search_with_score          │
│ 3. 转换结果为 FastMeSearchResult                            │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ ChromaAdapter.similarity_search_with_score()               │
│ 文件：vector_stores/chroma.py (line 152-174)               │
│                                                             │
│ 调用：                                                       │
│ self._chroma.similarity_search_with_score(                 │
│     query="E001 设备报警",                                  │
│     k=5,                                                    │
│     filter={"doc_type": "log", "device_id": "EQ001"}      │
│ )                                                           │
│                                                             │
│ Chroma 原生支持元数据过滤，直接传入 filter                   │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ LangChain Chroma.similarity_search_with_score()            │
│ 文件：langchain_chroma (第三方库)                           │
│                                                             │
│ 流程：                                                       │
│ 1. 生成查询向量                                             │
│ 2. 执行向量相似度搜索                                        │
│ 3. 应用元数据过滤                                           │
│ 4. 返回结果                                                 │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 步骤 4：返回检索结果                                         │
│ results = [                                                 │
│   FastMeSearchResult(                                       │
│     chunk_id="doc_001_0",                                   │
│     score=0.95,                                             │
│     text="2024-01-15 10:30 E001 设备报警...",               │
│     metadata={                                              │
│       "device_id": "EQ001",                                 │
│       "fault_code": "E001",                                 │
│       "timestamp": "2024-01-15 10:30:00"                   │
│     }                                                       │
│   ),                                                        │
│   ...                                                       │
│ ]                                                           │
│                                                             │
│ source_fields = ["device_id", "fault_code", "timestamp"]   │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ ChatPipeline.chat() 继续执行                                │
│ 文件：core/chat_pipeline.py                                 │
│                                                             │
│ 步骤 2：格式化上下文                                         │
│ context_text = self.prompt_adapter._format_context(        │
│     contexts=results,                                       │
│     source_fields=source_fields                             │
│ )                                                           │
│                                                             │
│ 输出格式：                                                   │
│ 【检索结果 1】                                               │
│ 设备：EQ001                                                 │
│ 故障码：E001                                                │
│ 时间：2024-01-15 10:30:00                                   │
│ 内容：2024-01-15 10:30 E001 设备报警...                     │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 步骤 3：获取 Prompt 模板                                     │
│ system_prompt = self.prompt_adapter.get_system_prompt(     │
│     "fault_diagnosis"                                       │
│ )                                                           │
│                                                             │
│ 返回：                                                       │
│ "你是一个设备故障诊断专家，根据以下日志信息..."              │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 步骤 4：调用 LLM                                             │
│ messages = [                                                 │
│     SystemMessage(content=system_prompt),                   │
│     HumanMessage(content=f"用户问题：{question}             │
│                              检索到的上下文：{context_text} │
│                              基于以上内容回答")              │
│ ]                                                           │
│                                                             │
│ answer = self.llm.invoke(messages).content                  │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 步骤 5：构建溯源信息                                         │
│ sources = self._build_sources(results, source_fields)      │
│                                                             │
│ 返回：[                                                     │
│   {                                                         │
│     "chunk_id": "doc_001_0",                                │
│     "device_id": "EQ001",                                   │
│     "fault_code": "E001",                                   │
│     "timestamp": "2024-01-15 10:30:00",                    │
│     "score": 0.95,                                          │
│     "preview": "2024-01-15 10:30 E001 设备报警..."          │
│   },                                                        │
│   ...                                                       │
│ ]                                                           │
└────────────────────────┬───────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 返回最终结果                                                 │
│ return {                                                     │
│     "question": "E001 设备报警怎么处理？",                   │
│     "scene": "fault_diagnosis",                              │
│     "filters": {"device_id": "EQ001"},                      │
│     "answer": "根据日志记录，E001 设备在...",                │
│     "sources": [...]                                         │
│ }                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 模块解耦设计

### 解耦原则

#### 1. 依赖倒置原则（DIP）

**原则：** 高层模块不应依赖低层模块，两者都应依赖抽象。

**实现：**

```python
# ❌ 错误：高层依赖具体实现
class ChatPipeline:
    def __init__(self):
        self.retriever = ChromaRetriever(...)  # 直接依赖 Chroma

# ✅ 正确：高层依赖抽象
class ChatPipeline:
    def __init__(
        self,
        scene_aware_retriever: BaseRetriever  # 依赖抽象
    ):
        self.retriever = scene_aware_retriever
```

---

#### 2. 开闭原则（OCP）

**原则：** 对扩展开放，对修改关闭。

**实现：**

```python
# 添加新的向量库，无需修改现有代码
# 文件：vector_stores/qdrant.py（新建）
class QdrantAdapter(VectorStoreAdapter):
    def add_documents(self, documents, ids=None):
        # Qdrant 特定实现
        pass

# 文件：vector_stores/factory.py（只修改工厂）
class VectorStoreFactory:
    @staticmethod
    def create(...):
        ...
        elif vector_store_type == "qdrant":  # 新增分支
            return QdrantAdapter(...)
```

---

#### 3. 单一职责原则（SRP）

**原则：** 每个类只负责一项职责。

**实现：**

```python
# ✅ 职责清晰分离

# IngestPipeline - 只负责文档入库流程编排
class IngestPipeline:
    def ingest(self, file_path, doc_type):
        # 编排：加载 → 拆分 → 元数据提取 → 入库

# ManualSplitter - 只负责手册拆分逻辑
class ManualSplitter:
    def split(self, document):
        # 拆分逻辑

# ChromaAdapter - 只负责 Chroma 向量库操作
class ChromaAdapter:
    def add_documents(self, documents, ids):
        # Chroma 特定操作
```

---

### 无感切换的实现

#### 示例：从 Chroma 切换到 FAISS

**用户代码：**

```python
# 使用 Chroma
rag = FastMeRAG(
    vector_store_type="chroma",
    vector_store_config={
        "persist_directory": "./data/chroma",
        "collection_name": "fastme_rag"
    }
)

# 切换到 FAISS（只需修改配置，无需修改业务代码）
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={
        "index_path": "./data/faiss_index"
    }
)

# 业务代码完全相同
rag.ingest("manual.pdf", doc_type="manual")
result = rag.chat("设备报警?", scene="fault_diagnosis")
```

**内部实现：**

```python
# app_factory.py
class FastMeRAG:
    def __init__(self, vector_store_type, vector_store_config):
        # 工厂根据类型创建适配器
        self.vectorstore = VectorStoreFactory.create(
            vector_store_type,  # "chroma" 或 "faiss"
            self.embeddings,
            vector_store_config
        )
        
        # 检索器工厂自动适配
        self.scene_aware_retriever = RetrieverFactory.create(
            vector_store_type,  # 自动选择对应的 Retriever
            self.vectorstore,
            self.scene_router
        )
        
        # ChatPipeline 无需修改
        self.chat_pipeline = ChatPipeline(
            scene_aware_retriever=self.scene_aware_retriever,
            ...
        )
```

---

### 配置驱动的解耦

**配置文件：** `config/scenes.yaml`

```yaml
scenes:
  fault_diagnosis:
    doc_type: log
    prompt_template: fault_diagnosis
    top_k: 5
    source_fields:
      - device_id
      - fault_code
      - timestamp
```

**代码加载配置：**

```python
# routers/scene_router.py
class SceneRouter:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        self.scene_config = config.get("scenes", {})
```

**优点：**
- ✅ 新增场景无需修改代码，只需修改 YAML
- ✅ 配置与代码分离，便于维护

---

## 总结

### 核心设计模式

| 模式 | 应用场景 | 实现文件 |
|------|---------|---------|
| **工厂模式** | 创建向量库、检索器 | `vector_stores/factory.py`, `retrievers/factory.py` |
| **适配器模式** | 统一向量库接口 | `vector_stores/base.py`, `chroma.py`, `faiss.py` |
| **策略模式** | 不同文档拆解策略 | `splitters/base.py`, `log_splitter.py` 等 |
| **注册表模式** | 管理 Splitter | `splitters/base.py` |
| **装饰器模式** | 场景感知检索器 | `retrievers/scene_aware.py` |

---

### 模块解耦的关键

1. **抽象接口**：定义统一的抽象基类（`VectorStoreAdapter`, `BaseSplitter`, `BaseRetriever`）
2. **工厂方法**：通过工厂创建具体实例
3. **依赖注入**：高层模块通过参数接收依赖
4. **配置驱动**：使用 YAML 配置文件管理场景、Prompt 等

---

### 无感切换的实现

| 切换场景 | 实现方式 | 修改点 |
|---------|---------|--------|
| **向量库切换** | 修改 `vector_store_type` 参数 | 仅配置 |
| **文档类型切换** | 修改 `doc_type` 参数 | 仅参数 |
| **场景切换** | 修改 `scene` 参数 | 仅参数 |
| **添加新向量库** | 实现 `VectorStoreAdapter`，更新工厂 | 新增文件 |

---

**这就是 FastMe RAG 的完整架构设计！** 🎉