# FastMe RAG 架构设计文档

## 概述

FastMe RAG 是一个面向制造业的轻量化、可插拔 RAG（检索增强生成）框架。本文档详细介绍系统的架构设计、模块解耦策略和核心调用链路。

## 架构总览

### 系统架构图

```
用户请求
    |
    v
+------------------------------------------+
|           FastMeRAG (主框架入口)          |
|  app_factory.py                          |
+------------------------------------------+
    |                    |
    | 文档入库           | 场景化问答
    v                    v
+---------------+  +-------------------+
| IngestPipeline|  |   ChatPipeline    |
| 文档入库流水线 |  |   对话流水线       |
+---------------+  +-------------------+
    |                    |
    v                    v
+------------------------------------------+
|      SceneAwareRetriever (场景感知)       |
|      retrievers/scene_aware.py           |
+------------------------------------------+
    |
    v
+------------------------------------------+
|  VectorStoreFactory -> VectorStoreAdapter|
|  (ChromaAdapter / FAISSAdapter)          |
|  vector_stores/                          |
+------------------------------------------+
    |
    v
+------------------------------------------+
|           HuggingFace Embeddings          |
|           向量化嵌入                       |
+------------------------------------------+
```

### 核心设计理念

1. **可插拔架构**: Embedding、向量库、LLM、Splitter 全部可配置替换
2. **配置化驱动**: 场景、Prompt、字段标签通过 YAML 配置，无需改代码
3. **职责分离**: Pipeline 层专注业务编排，Adapter 层处理技术细节
4. **场景化路由**: 根据场景自动选择对应的 doc_type、Prompt 模板和溯源字段

---

## 模块详解

### 1. 主框架入口 (app_factory.py)

`FastMeRAG` 类是整个框架的主入口，负责编排所有组件。

**核心职责**:
- 初始化所有组件（Embedding、LLM、向量库、拆解器、路由器）
- 提供统一的 API 接口（ingest、chat、chat_stream）
- 管理配置和语言切换

**关键属性**:
```python
class FastMeRAG:
    # LangChain 原语组件
    embeddings: HuggingFaceEmbeddings  # Embedding 模型
    vectorstore: VectorStoreAdapter     # 向量库适配器
    llm: ChatOpenAI                     # LLM 实例

    # 制造业专属组件
    splitter_registry: SplitterRegistry      # 拆解器注册表
    metadata_extractor: IndustrialMetadataExtractor  # 元数据抽取器
    scene_router: SceneRouter               # 场景路由器
    prompt_adapter: PromptAdapter           # Prompt 适配器

    # Pipeline 组件
    ingest_pipeline: IngestPipeline         # 文档入库流水线
    chat_pipeline: ChatPipeline             # 对话流水线
```

### 2. 文档入库流水线 (core/ingest_pipeline.py)

`IngestPipeline` 编排文档入库的完整流程。

**处理流程**:
```
文件 -> 加载 -> 拆解 -> 元数据抽取 -> 分批向量化 -> 入库
```

**核心方法**:
- `ingest()`: 单文档入库
- `batch_ingest()`: 批量文件夹入库

**设计要点**:
- 分批处理避免内存峰值
- 支持审核模式预览切片
- 定期内存清理优化
- 入库完成后自动 persist（FAISS 数据落盘，失败仅告警不中断，Chroma 保持自动持久化行为不变）

### 3. 对话流水线 (core/chat_pipeline.py)

`ChatPipeline` 编排场景化问答的完整流程。

**处理流程**:
```
问题 -> 场景路由 -> 检索 -> Prompt组装 -> LLM调用 -> 溯源构建
```

**核心方法**:
- `chat()`: 同步问答
- `chat_stream()`: 流式问答
- `chat_with_memory()`: 带记忆的对话

**记忆管理**:
- 基于 `ConversationBufferMemory` 实现会话记忆
- 支持 max_turns 控制历史轮次

### 4. 场景感知检索器 (retrievers/scene_aware.py)

`SceneAwareRetriever` 包装 BaseRetriever，添加场景化能力。

**核心功能**:
- 自动应用场景配置（top_k、source_fields）
- 自动构建场景过滤条件
- 统一返回格式

**调用流程**:
```python
# 1. 获取场景配置
scene_config = scene_router.route(scene)
top_k = scene_config.get("top_k", 5)
source_fields = scene_config.get("source_fields", [])

# 2. 构建过滤条件
where_filter = scene_router.build_filter(scene, user_filter)

# 3. 执行检索
results = retriever.retrieve(query, top_k, filters)
```

### 5. 向量库适配器 (vector_stores/)

采用适配器模式，统一不同向量库的接口。

**基类定义** (`vector_stores/base.py`):
```python
class VectorStoreAdapter(ABC):
    @abstractmethod
    def add_documents(self, documents, ids=None) -> None

    @abstractmethod
    def similarity_search_with_score(self, query, k=5, filter=None) -> List[Tuple[Document, float]]

    @abstractmethod
    def get_count(self) -> int

    @abstractmethod
    def delete_collection(self) -> None

    @abstractmethod
    def get_config(self) -> Dict[str, Any]
```

**已实现适配器**:
- `ChromaAdapter`: Chroma 向量库，支持持久化、原生元数据过滤
- `FAISSAdapter`: FAISS 向量库，内存存储、后过滤策略

### 6. 文档拆解器 (splitters/)

针对制造业文档特点设计的专用拆解器。

**基类** (`splitters/base.py`):
- `BaseSplitter`: 提供通用的文本拆分逻辑
- `SplitterRegistry`: 管理不同文档类型的拆解器

**已实现拆解器**:
| 拆解器 | 文档类型 | 特点 |
|--------|----------|------|
| `LogSplitter` | log | 按日志条目拆分，提取时间戳、故障码 |
| `ManualSplitter` | manual | 按章节层级拆分，保留章节结构 |
| `BusinessSplitter` | business | 按工单/记录拆分，提取工单号、物料号 |
| `SopSplitter` | sop | 按工序步骤拆分，保留工艺流程 |

### 7. 辅助模块

**文档加载器** (`adapters/document_loader.py`):
- 支持 PDF、DOCX、TXT、LOG、MD 格式
- 内存优化：大文件分块读取、PDF 逐页提取

**Prompt 适配器** (`adapters/prompt_adapter.py`):
- 管理 Prompt 模板
- 支持多语言切换
- 格式化上下文输出

**元数据抽取器** (`manufacturing/metadata_extractor.py`):
- 基于正则规则提取工业字段
- 支持 16 个预置工业字段
- 支持自定义规则扩展

---

## 调用链路详解

### 文档入库链路

```
用户调用: rag.ingest("manual.pdf", doc_type="manual")
    |
    v
FastMeRAG.ingest() -> IngestPipeline.ingest()
    |
    v
+-- 1. 加载文档
|   SimpleDocumentLoader.load()
|   - 读取文件内容
|   - 构建 FastMeDocument 对象
    |
    v
+-- 2. 拆分文档
|   SplitterRegistry.get("manual") -> ManualSplitter
|   ManualSplitter.split(document) -> List[FastMeChunk]
    |
    v
+-- 3. 提取元数据
|   IndustrialMetadataExtractor.enrich_chunk(chunks)
|   - 正则匹配提取设备ID、故障码等
    |
    v
+-- 4. 向量化入库
|   for batch in chunks:
|       VectorStoreAdapter.add_documents(batch_docs, batch_ids)
    |
    v
返回: {"status": "success", "chunks_count": N, ...}
```

### 场景化问答链路

```
用户调用: rag.chat("设备报警怎么处理？", scene="fault_diagnosis")
    |
    v
FastMeRAG.chat() -> ChatPipeline.chat()
    |
    v
+-- 1. 场景路由与过滤构建
|   SceneRouter.route("fault_diagnosis")
|   - 返回: {doc_type: "log", top_k: 5, source_fields: [...]}
|   SceneRouter.build_filter(scene, user_filter)
|   - 直接返回: List[FilterCondition]  ← 优化后，无需中转
    |
    v
+-- 2. 检索上下文
|   SceneAwareRetriever.retrieve(question, scene, filters)
|   - 获取 FilterCondition 列表
|   - 调用 BaseRetriever.retrieve()
|   - 返回: List[FastMeSearchResult]
    |
    v
+-- 3. 向量库适配器处理
|   ChromaRetriever.retrieve(filters=FilterCondition)
|   - _to_chroma_filter(): 转换为 Chroma 语法
|   - similarity_search_with_score(query, k, filter)
|   或
|   FAISSRetriever.retrieve(filters=FilterCondition)
|   - 后过滤：遍历结果，检查 FilterCondition
    |
    v
+-- 4. 组装 Prompt
|   PromptAdapter.get_system_prompt("fault_diagnosis")
|   PromptAdapter._format_context(contexts, source_fields)
|   - 构建: [系统Prompt] + [用户问题] + [上下文]
    |
    v
+-- 5. 调用 LLM
|   ChatOpenAI.invoke(messages)
|   - 返回: LLM 生成的回答
    |
    v
+-- 6. 构建溯源
|   ChatPipeline._build_sources(contexts, source_fields)
|   - 提取配置的字段，构建溯源信息
    |
    v
返回: {"question": "...", "answer": "...", "sources": [...]}
```

**架构优化说明：**
- ✅ SceneRouter 直接输出 FilterCondition（框架内部标准格式）
- ✅ 消除了 dict → FilterCondition → dict 的冗余转换
- ✅ 数据流更简洁：YAML → FilterCondition → 向量库适配器

---

## 配置系统

### 配置文件结构

```
config/
├── scenes.yaml           # 场景配置
├── metadata_rules.yaml   # 元数据抽取规则
├── prompt_templates.yaml # Prompt 模板
└── field_labels.yaml     # 字段标签（多语言）
```

### 场景配置示例

```yaml
# config/scenes.yaml
scenes:
  fault_diagnosis:
    doc_type: log
    prompt_template: fault_diagnosis
    top_k: 5
    source_fields:
      - chunk_id
      - doc_id
      - device_id
      - fault_code
      - timestamp
    description: "设备故障诊断"
```

### 配置加载流程

```
框架初始化
    |
    v
SceneRouter(config_path="config/scenes.yaml")
    |
    v
yaml.safe_load() -> scene_config (dict)
    |
    v
存储到实例属性，供后续路由使用
```

**配置隔离**: 配置合并采用深拷贝策略，多 `FastMeRAG` 实例的配置互不影响，避免 `DEFAULT_CONFIG` 被污染。

---

## 扩展机制

### 添加新向量库

1. 创建适配器类，继承 `VectorStoreAdapter`
2. 实现所有抽象方法
3. 更新 `VectorStoreFactory`
4. 创建对应检索器

### 添加新 Splitter

1. 创建拆解器类，继承 `BaseSplitter`
2. 实现 `split()` 方法
3. 注册到 `SplitterRegistry`
4. 更新配置文件

### 添加新场景

1. 编辑 `config/scenes.yaml`，添加场景配置
2. 编辑 `config/prompt_templates.yaml`，添加 Prompt 模板
3. 无需修改代码

---

## 性能优化

### 内存优化策略

1. **分批入库**: 避免一次性加载大量向量
2. **流式读取**: 大文件分块读取，减少内存峰值
3. **定期清理**: 批量入库时定期执行 `gc.collect()`

### 检索优化策略

1. **元数据过滤**: Chroma 原生支持，FAISS 后过滤
2. **批量 Embedding**: 配置 `embedding_batch_size` 提升吞吐
3. **缓存机制**: 模型缓存到本地，避免重复下载

---

## 相关文档

- [开发者指南](DEVELOPER_GUIDE_CN.md) - 添加场景、Splitter、向量库的详细步骤
- [API 参考](API_REFERENCE_CN.md) - 所有公开 API 的详细说明
- [快速开始](QUICKSTART_CN.md) - 简化的快速入门教程