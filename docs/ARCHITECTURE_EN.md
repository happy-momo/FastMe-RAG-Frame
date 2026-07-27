# FastMe RAG Architecture Design Document

## Overview

FastMe RAG is a lightweight, pluggable RAG (Retrieval-Augmented Generation) framework designed for the manufacturing industry. This document details the system's architecture design, module decoupling strategy, and core call chains.

## Architecture Overview

### System Architecture Diagram

```
User Request
    |
    v
+------------------------------------------+
|           FastMeRAG (Main Entry)          |
|  app_factory.py                          |
+------------------------------------------+
    |                    |
    | Document Ingest    | Scene-aware Q&A
    v                    v
+---------------+  +-------------------+
| IngestPipeline|  |   ChatPipeline    |
| Ingestion     |  |   Conversation    |
| Pipeline      |  |   Pipeline        |
+---------------+  +-------------------+
    |                    |
    v                    v
+------------------------------------------+
|      SceneAwareRetriever                 |
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
|           Vector Embeddings               |
+------------------------------------------+
```

### Core Design Principles

1. **Pluggable Architecture**: Embedding, vector store, LLM, and Splitter are all configurable and replaceable
2. **Configuration-Driven**: Scenes, Prompts, and field labels are defined via YAML configuration without code changes
3. **Separation of Concerns**: Pipeline layer focuses on business orchestration, Adapter layer handles technical details
4. **Scene-Based Routing**: Automatically selects corresponding doc_type, Prompt template, and source fields based on scene

---

## Module Details

### 1. Main Entry (app_factory.py)

The `FastMeRAG` class is the main entry point for the entire framework, responsible for orchestrating all components.

**Core Responsibilities**:
- Initialize all components (Embedding, LLM, vector store, splitter, router)
- Provide unified API interfaces (ingest, chat, chat_stream)
- Manage configuration and language switching

**Key Attributes**:
```python
class FastMeRAG:
    # LangChain primitive components
    embeddings: HuggingFaceEmbeddings  # Embedding model
    vectorstore: VectorStoreAdapter     # Vector store adapter
    llm: ChatOpenAI                     # LLM instance

    # Manufacturing-specific components
    splitter_registry: SplitterRegistry      # Splitter registry
    metadata_extractor: IndustrialMetadataExtractor  # Metadata extractor
    scene_router: SceneRouter               # Scene router
    prompt_adapter: PromptAdapter           # Prompt adapter

    # Pipeline components
    ingest_pipeline: IngestPipeline         # Document ingestion pipeline
    chat_pipeline: ChatPipeline             # Conversation pipeline
```

### 2. Document Ingestion Pipeline (core/ingest_pipeline.py)

`IngestPipeline` orchestrates the complete document ingestion process.

**Processing Flow**:
```
File -> Load -> Split -> Metadata Extraction -> Batch Vectorization -> Store
```

**Core Methods**:
- `ingest()`: Single document ingestion
- `batch_ingest()`: Batch folder ingestion

**Design Points**:
- Batch processing to avoid memory peaks
- Support review mode for chunk preview
- Periodic memory cleanup optimization
- Auto-persist after ingestion (FAISS data is written to disk; failure only logs a warning without interrupting; Chroma keeps auto-persistent behavior unchanged)

### 3. Conversation Pipeline (core/chat_pipeline.py)

`ChatPipeline` orchestrates the complete scene-aware Q&A process.

**Processing Flow**:
```
Question -> Scene Routing -> Retrieval -> Prompt Assembly -> LLM Call -> Source Building
```

**Core Methods**:
- `chat()`: Synchronous Q&A
- `chat_stream()`: Streaming Q&A
- `chat_with_memory()`: Conversation with memory

**Memory Management**:
- Based on `ConversationBufferMemory` for session memory
- Support max_turns to control history rounds

### 4. Scene-Aware Retriever (retrievers/scene_aware.py)

`SceneAwareRetriever` wraps BaseRetriever and adds scene-aware capabilities.

**Core Functions**:
- Automatically apply scene configuration (top_k, source_fields)
- Automatically build scene filter conditions
- Unified return format

**Call Flow**:
```python
# 1. Get scene configuration
scene_config = scene_router.route(scene)
top_k = scene_config.get("top_k", 5)
source_fields = scene_config.get("source_fields", [])

# 2. Build filter conditions
where_filter = scene_router.build_filter(scene, user_filter)

# 3. Execute retrieval
results = retriever.retrieve(query, top_k, filters)
```

### 5. Vector Store Adapter (vector_stores/)

Using adapter pattern to unify interfaces for different vector stores.

**Base Class Definition** (`vector_stores/base.py`):
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

**Implemented Adapters**:
- `ChromaAdapter`: Chroma vector store, supports persistence and native metadata filtering
- `FAISSAdapter`: FAISS vector store, in-memory storage with post-filtering strategy

### 6. Document Splitters (splitters/)

Specialized splitters designed for manufacturing document characteristics.

**Base Class** (`splitters/base.py`):
- `BaseSplitter`: Provides common text splitting logic
- `SplitterRegistry`: Manages splitters for different document types

**Implemented Splitters**:
| Splitter | Document Type | Features |
|----------|---------------|----------|
| `LogSplitter` | log | Split by log entries, extract timestamps, fault codes |
| `ManualSplitter` | manual | Split by chapter hierarchy, preserve chapter structure |
| `BusinessSplitter` | business | Split by work orders/records, extract order numbers, material IDs |
| `SopSplitter` | sop | Split by process steps, preserve process flow |

### 7. Auxiliary Modules

**Document Loader** (`adapters/document_loader.py`):
- Supports PDF, DOCX, TXT, LOG, MD formats
- Memory optimization: chunked reading for large files, page-by-page PDF extraction

**Prompt Adapter** (`adapters/prompt_adapter.py`):
- Manages Prompt templates
- Supports multi-language switching
- Formats context output

**Metadata Extractor** (`manufacturing/metadata_extractor.py`):
- Extracts industrial fields based on regex rules
- Supports 16 pre-configured industrial fields
- Supports custom rule extension

---

## Call Chain Details

### Document Ingestion Chain

```
User call: rag.ingest("manual.pdf", doc_type="manual")
    |
    v
FastMeRAG.ingest() -> IngestPipeline.ingest()
    |
    v
+-- 1. Load document
|   SimpleDocumentLoader.load()
|   - Read file content
|   - Build FastMeDocument object
    |
    v
+-- 2. Split document
|   SplitterRegistry.get("manual") -> ManualSplitter
|   ManualSplitter.split(document) -> List[FastMeChunk]
    |
    v
+-- 3. Extract metadata
|   IndustrialMetadataExtractor.enrich_chunk(chunks)
|   - Regex matching to extract device ID, fault codes, etc.
    |
    v
+-- 4. Vectorize and store
|   for batch in chunks:
|       VectorStoreAdapter.add_documents(batch_docs, batch_ids)
    |
    v
Return: {"status": "success", "chunks_count": N, ...}
```

### Scene-aware Q&A Chain

```
User call: rag.chat("How to handle device alarm?", scene="fault_diagnosis")
    |
    v
FastMeRAG.chat() -> ChatPipeline.chat()
    |
    v
+-- 1. Scene routing
|   SceneRouter.route("fault_diagnosis")
|   - Return: {doc_type: "log", top_k: 5, source_fields: [...]}
    |
    v
+-- 2. Retrieve context
|   SceneAwareRetriever.retrieve(question, scene, filters)
|   - Build filter conditions
|   - Call BaseRetriever.retrieve()
|   - Return: List[FastMeSearchResult]
    |
    v
+-- 3. Assemble Prompt
|   PromptAdapter.get_system_prompt("fault_diagnosis")
|   PromptAdapter._format_context(contexts, source_fields)
|   - Build: [System Prompt] + [User Question] + [Context]
    |
    v
+-- 4. Call LLM
|   ChatOpenAI.invoke(messages)
|   - Return: LLM-generated answer
    |
    v
+-- 5. Build source tracing
|   ChatPipeline._build_sources(contexts, source_fields)
|   - Extract configured fields, build source info
    |
    v
Return: {"question": "...", "answer": "...", "sources": [...]}
```

**Architecture Optimization Notes:**
- ✅ SceneRouter directly outputs FilterCondition (framework internal standard format)
- ✅ Eliminated redundant dict → FilterCondition → dict conversion
- ✅ Simpler data flow: YAML → FilterCondition → vector store adapter

---

## Configuration System

### Configuration File Structure

```
config/
├── scenes.yaml           # Scene configuration
├── metadata_rules.yaml   # Metadata extraction rules
├── prompt_templates.yaml # Prompt templates
└── field_labels.yaml     # Field labels (multi-language)
```

### Scene Configuration Example

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
    description: "Device fault diagnosis"
```

### Configuration Loading Process

```
Framework initialization
    |
    v
SceneRouter(config_path="config/scenes.yaml")
    |
    v
yaml.safe_load() -> scene_config (dict)
    |
    v
Store to instance attribute for subsequent routing use
```

**Configuration Isolation**: Config merging uses deep copy strategy, ensuring multiple `FastMeRAG` instances do not affect each other's configuration, preventing `DEFAULT_CONFIG` from being polluted.

---

## Extension Mechanism

### Adding New Vector Store

1. Create adapter class inheriting `VectorStoreAdapter`
2. Implement all abstract methods
3. Update `VectorStoreFactory`
4. Create corresponding retriever

### Adding New Splitter

1. Create splitter class inheriting `BaseSplitter`
2. Implement `split()` method
3. Register to `SplitterRegistry`
4. Update configuration file

### Adding New Scene

1. Edit `config/scenes.yaml` to add scene configuration
2. Edit `config/prompt_templates.yaml` to add Prompt template
3. No code modification required

---

## Performance Optimization

### Memory Optimization Strategies

1. **Batch Ingestion**: Avoid loading large amounts of vectors at once
2. **Streaming Read**: Chunked reading for large files to reduce memory peaks
3. **Periodic Cleanup**: Execute `gc.collect()` periodically during batch ingestion

### Retrieval Optimization Strategies

1. **Metadata Filtering**: Chroma native support, FAISS post-filtering
2. **Batch Embedding**: Configure `embedding_batch_size` to improve throughput
3. **Caching Mechanism**: Model cached locally to avoid repeated downloads

---

## Related Documentation

- [Developer Guide](DEVELOPER_GUIDE_EN.md) - Detailed steps for adding scenes, splitters, and vector stores
- [API Reference](API_REFERENCE_EN.md) - Detailed description of all public APIs
- [Quick Start](QUICKSTART_EN.md) - Simplified quick start tutorial
