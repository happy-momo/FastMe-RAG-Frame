# FastMe RAG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-89%20passed-green.svg)]()

**FastMe RAG** is a lightweight, pluggable RAG (Retrieval-Augmented Generation) framework designed for the manufacturing industry. It's built for factory equipment manuals, operation logs, workshop work orders, and process SOPs, providing scenario-based Q&A and automatic industrial metadata extraction.

> 📖 [中文文档](README.md) | 📖 [Configuration Guide](examples/README.md) | 📖 [Documentation](docs/README.md)

---

## Table of Contents

- [Core Features](#-core-features)
- [Quick Start](#-quick-start)
- [Core Concepts](#-core-concepts)
- [API Reference](#-api-reference)
  - [Initialization](#initialization)
  - [Document Ingestion](#document-ingestion)
  - [Scenario-based Q&A](#scenario-based-qa)
  - [Streaming Output](#streaming-output)
  - [Conversation Memory](#conversation-memory)
  - [Vector Store Configuration](#vector-store-configuration)
- [Supported Document Types](#-supported-document-types)
- [Predefined Scenarios](#-predefined-scenarios)
- [Metadata Fields](#-metadata-fields)
- [Advanced Configuration](#-advanced-configuration)
- [Developer Guide](#-developer-guide)
  - [Adding New Scenes](#adding-new-scenes)
  - [Adding New Splitters](#adding-new-splitters)
  - [Adding New Vector Stores](#adding-new-vector-stores)
- [Project Structure](#-project-structure)

---

## 🚀 Core Features

| Feature | Description |
|---------|-------------|
| 🏭 **Manufacturing-specific Splitters** | 4 built-in splitters (log/manual/business/SOP) for intelligent document segmentation |
| 🔍 **Scenario-based Routing** | 4 predefined scenarios (fault diagnosis/manual query/work order trace/default) |
| 🏷️ **Industrial Metadata Extraction** | Automatic extraction of 16 industrial fields (device ID, line ID, fault code, work order ID, etc.) |
| 🌐 **Multi-language Support** | Chinese/English interface switching with configurable field labels |
| 🔌 **Pluggable Architecture** | Based on LangChain, all components (Embedding/Vector Store/LLM) are configurable |
| 💾 **Multi Vector Store Support** | Support for Chroma (persistent), FAISS (in-memory), and more |
| ⚙️ **Configuration-driven** | YAML configuration files for scenarios, prompts, and field labels |
| 📊 **Streaming Output** | Streaming Q&A for faster first token and better user experience |
| 🎛️ **Flexible Configuration** | Configurable chunk size, batch size, progress bar, and more |

---

## 📦 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
LLM_BASE_URL=http://localhost:8000/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=qwen-plus

# Embedding model configuration (supports local path or HuggingFace model name)
# Option 1: Use locally downloaded model (recommended, avoids re-downloading)
EMBEDDING_MODEL=./models/bge-m3

# Option 2: Use HuggingFace model name (will auto-download on first use)
# EMBEDDING_MODEL=BAAI/bge-m3

# Optional: Model cache directory (only used when EMBEDDING_MODEL is a HuggingFace model name)
# MODEL_CACHE_DIR=./models
```

> **💡 Tip**: `FastMeRAG` automatically reads configuration from the `.env` file in the project root directory, no need to pass parameters manually.

### 3. Basic Usage

```python
from app_factory import FastMeRAG

# Initialize with default configuration
rag = FastMeRAG()

# Ingest document
rag.ingest("equipment_manual.pdf", doc_type="manual")

# Scenario-based Q&A
result = rag.chat("How to handle device alarm?", scene="fault_diagnosis")
print(result["answer"])
```

---

## 📖 Core Concepts

### Architecture Overview

```
User Question
    ↓
┌─────────────────────────────────────────────────┐
│           FastMeRAG (Main Entry Point)          │
├─────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────────────┐   │
│  │ Ingestion   │    │  Scenario-based      │   │
│  │ IngestPipe  │    │  ChatPipeline        │   │
│  └──────┬──────┘    └──────────┬───────────┘   │
│         ↓                      ↓                │
│  ┌─────────────────────────────────────────┐   │
│  │      SceneAwareRetriever (Wrapper)       │   │
│  └──────────────────┬──────────────────────┘   │
│                     ↓                           │
│  ┌─────────────────────────────────────────┐   │
│  │  VectorStoreFactory → VectorStoreAdapter │   │
│  │  (ChromaAdapter / FAISSAdapter)          │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Core Components

| Component | File | Responsibility |
|-----------|------|----------------|
| `FastMeRAG` | `app_factory.py` | Main entry point, orchestrates all components |
| `IngestPipeline` | `core/ingest_pipeline.py` | Document ingestion pipeline |
| `ChatPipeline` | `core/chat_pipeline.py` | Conversation pipeline |
| `SceneAwareRetriever` | `retrievers/scene_aware.py` | Scenario-aware retriever |
| `VectorStoreAdapter` | `vector_stores/base.py` | Vector store abstract base class |
| `ChromaAdapter` | `vector_stores/chroma.py` | Chroma vector store adapter |
| `FAISSAdapter` | `vector_stores/faiss.py` | FAISS vector store adapter |

---

## ⚙️ Environment Variable Configuration

### `.env` File Description

The `FastMeRAG` framework automatically reads configuration from the `.env` file in the project root directory, no need to pass parameters manually in code.

**Complete `.env` Configuration Example:**

```bash
# ===== LLM Configuration =====
LLM_BASE_URL=http://localhost:8000/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=qwen-plus

# ===== Embedding Model Configuration =====
# Option 1: Use locally downloaded model (recommended, avoids re-downloading)
EMBEDDING_MODEL=./models/bge-m3

# Option 2: Use HuggingFace model name (will auto-download on first use)
# EMBEDDING_MODEL=BAAI/bge-m3

# Optional: Model cache directory (only used when EMBEDDING_MODEL is a HuggingFace model name)
# MODEL_CACHE_DIR=./models

# ===== Other Configuration =====
# FASTME_LANGUAGE=zh  # UI language, options: zh (Chinese) | en (English)
```

### Environment Variable Priority

Configuration value priority: **Passed parameters > `.env` file > Code defaults**

```python
from app_factory import FastMeRAG

# Scenario 1: No parameters passed, read from .env (recommended)
rag = FastMeRAG()  # Uses configuration from .env

# Scenario 2: Pass parameters to override .env
rag = FastMeRAG(
    embedding_model="./models/bge-m3",  # Overrides EMBEDDING_MODEL in .env
    llm_model="qwen-plus"               # Overrides LLM_MODEL in .env
)
```

### Local Model vs HuggingFace Model

**`EMBEDDING_MODEL` supports two configuration methods:**

| Configuration Method | Example | Description |
|---------------------|---------|-------------|
| **Local Path** | `./models/bge-m3` | Load directly from local path, no network connection required, fast |
| **HuggingFace Model Name** | `BAAI/bge-m3` | Will auto-download to `MODEL_CACHE_DIR` on first use |

**Recommended to use local path** to avoid attempting to connect to HuggingFace and download model on every initialization.

**Steps:**

1. Download model manually on first time:
   ```bash
   # Can use git clone or huggingface-cli to download
   git lfs install
   git clone https://huggingface.co/BAAI/bge-m3 ./models/bge-m3
   ```

2. Configure local path in `.env`:
   ```bash
   EMBEDDING_MODEL=./models/bge-m3
   ```

---

## 🔧 API Reference

### Initialization

#### `FastMeRAG.__init__()`

```python
from app_factory import FastMeRAG

rag = FastMeRAG(
    # ========== Model Configuration ==========
    embedding_model: str = "BAAI/bge-m3",      # Embedding model name
    model_cache_dir: str = "./models",          # Model cache directory
    llm_base_url: str = "http://localhost:8000/v1/chat/completions",  # LLM API URL
    llm_api_key: str = "sk-xxx",                # LLM API Key
    llm_model: str = "qwen-plus",               # LLM model name
    temperature: float = 0.2,                   # LLM temperature
    language: str = "en",                       # Language ("zh" | "en")

    # ========== Chunk & Batch Processing ==========
    chunk_max_size: int = 1000,                 # Max chars per chunk
    ingest_batch_size: int = 32,                # Ingestion batch size
    embedding_batch_size: int = 32,             # Embedding batch size
    show_progress_bar: bool = False,            # Show progress bar

    # ========== Vector Store Configuration ==========
    vector_store_type: str = "chroma",          # Vector store type ("chroma" | "faiss")
    vector_store_config: dict = None,           # Vector store specific config

    # ========== Backward Compatibility ==========
    chroma_dir: str = "./data/chroma",          # Chroma data directory
    chroma_collection: str = "fastme_rag",      # Chroma collection name
)
```

#### Parameter Details

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `embedding_model` | str | `"BAAI/bge-m3"` | HuggingFace Embedding model name, or local model path (e.g., `./models/bge-m3`). **Read from `.env` first** |
| `model_cache_dir` | str | `"./models"` | Model cache directory. When `embedding_model` is a HuggingFace model name, model will be downloaded here. **Read from `.env` first** |
| `llm_base_url` | str | `"http://localhost:8000/v1/chat/completions"` | LLM API URL (OpenAI-compatible format). **Read from `.env` first** |
| `llm_api_key` | str | `"sk-1234567890abcdef..."` | LLM API Key. **Read from `.env` first** |
| `llm_model` | str | `"qwen-plus"` | LLM model name. **Read from `.env` first** |
| `temperature` | float | `0.2` | LLM temperature (lower = more deterministic) |
| `language` | str | `"zh"` | Interface language, supports `"zh"` (Chinese) and `"en"` (English) |
| `chunk_max_size` | int | `1000` | Max chars per chunk. Recommended: log 500-800, manual 1000-1500, business 800-1200 |
| `ingest_batch_size` | int | `32` | Ingestion batch size. Reduce for memory-constrained environments (16-24), increase for high-performance (64-128) |
| `embedding_batch_size` | int | `32` | Embedding batch size. GPU users can increase (64-128), reduce for memory-constrained (8-16) |
| `show_progress_bar` | bool | `False` | Show progress bar. Recommended for large file ingestion |
| `vector_store_type` | str | `"chroma"` | Vector store type, supports `"chroma"` or `"faiss"` |
| `vector_store_config` | dict | `None` | Vector store specific configuration |

> **Environment Variable Priority**: Passed parameters > `.env` file > Code defaults
> - If parameter is passed (e.g., `embedding_model="./models/bge-m3"`), use parameter value
> - If no parameter passed, read from `.env` file
> - If `.env` has no configuration, use code default value

#### Configuration Examples

**Default Configuration (read from .env):**
```python
# Recommended: configure in .env file, code reads automatically
rag = FastMeRAG()
```

**Using FAISS Vector Store:**
```python
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={
        "index_path": "./data/faiss_index"
    }
)
```

**Memory-constrained Environment:**
```python
rag = FastMeRAG(
    chunk_max_size=800,        # Smaller chunks
    ingest_batch_size=16,      # Smaller batches
    embedding_batch_size=16,   # Smaller embedding batches
    show_progress_bar=False,
)
```

**High-performance Configuration (GPU):**
```python
rag = FastMeRAG(
    chunk_max_size=1500,       # Larger chunks
    ingest_batch_size=64,      # Larger batches
    embedding_batch_size=64,   # Larger embedding batches
    show_progress_bar=True,
)
```

**Using English Interface:**
```python
rag = FastMeRAG(language="en")
```

---

### Document Ingestion

#### `ingest()` - Single Document Ingestion

```python
result = rag.ingest(
    file_path: str,                    # File path (required)
    doc_type: str,                     # Document type (required): log/manual/business/sop
    extra_metadata: dict = None,       # Extra metadata (optional)
    require_review: bool = False       # Require review (optional)
)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | str | ✅ | File path, supports PDF, DOCX, TXT, LOG, MD formats |
| `doc_type` | str | ✅ | Document type: `"log"`, `"manual"`, `"business"`, `"sop"` |
| `extra_metadata` | dict | ❌ | Extra metadata to inject into all chunks. Example: `{"device_id": "EQ001", "line_id": "LN01"}` |
| `require_review` | bool | ❌ | Require review. If `True`, returns chunk preview without actual ingestion |

**Return Value:**

```python
# Successful ingestion
{
    "status": "success",
    "doc_id": "doc_20240115_abc123",     # Document unique ID
    "file_name": "equipment_manual.pdf", # File name
    "doc_type": "manual",                # Document type
    "chunks_count": 15,                  # Number of chunks
    "vector_count": 115                  # Total vector count
}

# Review mode
{
    "status": "waiting_review",
    "doc_id": "doc_20240115_abc123",
    "file_name": "equipment_manual.pdf",
    "doc_type": "manual",
    "chunks": [                          # Chunk list (preview)
        {
            "chunk_id": "doc_20240115_abc123_0",
            "text": "Chapter 1 Equipment Overview...",
            "metadata": {"chapter_num": "1", "chapter_title": "Overview"}
        },
        ...
    ]
}
```

**Examples:**

```python
from app_factory import FastMeRAG

rag = FastMeRAG()

# 1. Basic ingestion
result = rag.ingest("equipment_manual.pdf", doc_type="manual")
print(f"Ingestion successful: {result['chunks_count']} chunks")

# 2. Ingestion with extra metadata
result = rag.ingest(
    file_path="fault_log.log",
    doc_type="log",
    extra_metadata={
        "device_id": "EQ001",    # Device ID
        "line_id": "LN01"        # Production line ID
    }
)

# 3. Review mode (preview chunks without ingesting)
result = rag.ingest("work_order.xlsx", doc_type="business", require_review=True)
if result["status"] == "waiting_review":
    print(f"Pending review: {len(result['chunks'])} chunks")
    for chunk in result["chunks"][:3]:  # Preview first 3
        print(f"  - {chunk['chunk_id']}: {chunk['text'][:50]}...")
```

#### `batch_ingest()` - Batch Ingestion

```python
results = rag.batch_ingest(
    folder_path: str,                      # Folder path (required)
    doc_type: str,                         # Document type (required)
    extra_metadata: dict = None,           # Extra metadata (optional)
    file_extensions: list = None,          # File extension filter (optional)
    persist_interval: int = 10             # Memory cleanup interval (optional)
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `folder_path` | str | - | Folder path |
| `doc_type` | str | - | Document type |
| `extra_metadata` | dict | `None` | Extra metadata shared by all files |
| `file_extensions` | list | `[".pdf", ".docx", ".txt", ".log", ".md"]` | File extension filter |
| `persist_interval` | int | `10` | Memory cleanup every N files, set to `0` to disable |

**Return Value:**

```python
[
    {"status": "success", "doc_id": "doc_001", "chunks_count": 10, ...},
    {"status": "success", "doc_id": "doc_002", "chunks_count": 15, ...},
    {"status": "error", "file": "failed.pdf", "error": "Cannot parse file"}
]
```

**Examples:**

```python
# Batch ingest log folder
results = rag.batch_ingest(
    folder_path="./logs",
    doc_type="log",
    extra_metadata={"project": "Production Line A"}
)

# Count results
success = sum(1 for r in results if r["status"] == "success")
print(f"Successfully ingested {success} files")

# Smaller memory cleanup interval for large files
results = rag.batch_ingest(
    folder_path="./manuals",
    doc_type="manual",
    persist_interval=5  # Cleanup every 5 files
)
```

---

### Scenario-based Q&A

#### `chat()` - Synchronous Q&A

```python
result = rag.chat(
    question: str,                    # User question (required)
    scene: str = "default",           # Scenario name (optional)
    filters: dict = None,             # Filter conditions (optional)
    top_k: int = None                 # Number of results (optional)
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `question` | str | - | User question |
| `scene` | str | `"default"` | Scenario name: `"fault_diagnosis"`, `"manual_query"`, `"work_order_trace"`, `"default"` |
| `filters` | dict | `None` | Filter conditions, e.g.: `{"device_id": "EQ001", "line_id": "LN01"}` |
| `top_k` | int | Scene config | Number of results, defaults to scene configuration (usually 5) |

**Return Value:**

```python
{
    "question": "How to handle device alarm?",  # User question
    "scene": "fault_diagnosis",                 # Scenario name
    "filters": {"device_id": "EQ001"},          # Filter conditions
    "answer": "According to the log records...", # LLM-generated answer
    "sources": [                                 # Source information
        {
            "chunk_id": "doc_001_0",
            "doc_id": "doc_001",
            "doc_type": "log",
            "device_id": "EQ001",
            "fault_code": "E001",
            "timestamp": "2024-01-15 10:30:00",
            "score": 0.95,                      # Similarity score
            "preview": "Device alarm record..."  # Text preview
        },
        ...
    ]
}
```

**Examples:**

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("fault_log.log", doc_type="log")

# 1. Basic Q&A
result = rag.chat("How to handle device alarm?", scene="fault_diagnosis")
print(f"Answer: {result['answer']}")

# 2. Q&A with filter conditions
result = rag.chat(
    question="What faults does device E001 have?",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}  # Only retrieve records for device EQ001
)

# 3. View source information
print("\nSources:")
for source in result["sources"]:
    print(f"  - [{source['score']:.2f}] {source['device_id']}: {source['preview'][:50]}...")

# 4. Custom number of results
result = rag.chat("Manual content", scene="manual_query", top_k=10)
```

#### Filter Conditions Detail

**Chroma Vector Store (Native Support):**
```python
# Single condition filter
filters = {"device_id": "EQ001"}

# Multiple condition filter (AND relationship)
filters = {
    "device_id": "EQ001",
    "line_id": "LN01"
}

# Only returns results satisfying device_id=EQ001 AND line_id=LN01
result = rag.chat("Fault records", scene="fault_diagnosis", filters=filters)
```

**FAISS Vector Store (Post-filtering Strategy):**
```python
# FAISS doesn't support native filtering, uses "retrieval + post-filtering" strategy
# First retrieves top_k * post_filter_multiplier results, then filters by conditions

filters = {"device_id": "EQ001"}
result = rag.chat("Fault records", scene="fault_diagnosis", filters=filters)
```

---

### Streaming Output

#### `chat_stream()` - Streaming Q&A

```python
for chunk in rag.chat_stream(
    question: str,                    # User question (required)
    scene: str = "default",           # Scenario name (optional)
    filters: dict = None,             # Filter conditions (optional)
    top_k: int = None                 # Number of results (optional)
):
    print(chunk, end="", flush=True)
```

**Parameters:**

Same as `chat()`.

**Return Value:**

- Generator, each `yield` is a text chunk (`str`)

**Example:**

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("equipment_manual.pdf", doc_type="manual")

# Streaming Q&A (ChatGPT-like typing effect)
print("AI: ", end="", flush=True)
for chunk in rag.chat_stream(
    question="What are the equipment startup steps?",
    scene="manual_query"
):
    print(chunk, end="", flush=True)
print()  # Newline

# Output example:
# AI: According to the equipment manual, the startup steps are:
# 1. Check power connection before starting...
# 2. Press the start button...
# ...
```

---

### Conversation Memory

#### `create_memory()` - Create Session Memory

```python
rag.create_memory(
    session_id: str,              # Session ID (required)
    max_turns: int = 10           # Max turns to retain (optional)
)
```

#### `chat_with_memory()` - Conversational Q&A

```python
result = rag.chat_with_memory(
    question: str,                    # User question (required)
    session_id: str,                  # Session ID (required)
    scene: str = "default",           # Scenario name (optional)
    filters: dict = None,             # Filter conditions (optional)
    top_k: int = None                 # Number of results (optional)
)
```

#### `get_memory()` - Get Session Memory

```python
memory = rag.get_memory(session_id: str)
```

#### `clear_memory()` - Clear Memory

```python
# Clear specific session
rag.clear_memory(session_id: str)

# Clear all sessions
rag.clear_memory()
```

**Complete Example:**

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("fault_log.log", doc_type="log")

# Create session memory
rag.create_memory(session_id="user_001", max_turns=10)

# First conversation
result1 = rag.chat_with_memory(
    question="What faults does device E001 have?",
    session_id="user_001",
    scene="fault_diagnosis"
)
print(f"Answer 1: {result1['answer']}")

# Second conversation (automatically carries context)
result2 = rag.chat_with_memory(
    question="How to handle this fault?",  # Can reference device E001 from previous turn
    session_id="user_001",
    scene="fault_diagnosis"
)
print(f"Answer 2: {result2['answer']}")

# View history
memory = rag.get_memory("user_001")
print(f"Conversation history: {memory}")

# Clear memory
rag.clear_memory(session_id="user_001")
```

---

### Vector Store Configuration

#### Chroma Vector Store (Default)

**Features:**
- ✅ Persistent storage (data saved to disk)
- ✅ Native support for metadata filtering
- ✅ Collection isolation

**Configuration:**

```python
# Method 1: Backward compatible parameters
rag = FastMeRAG(
    chroma_dir="./data/chroma",           # Chroma data directory
    chroma_collection="my_collection"     # Collection name
)

# Method 2: Through vector_store_config
rag = FastMeRAG(
    vector_store_type="chroma",
    vector_store_config={
        "persist_directory": "./data/chroma",
        "collection_name": "my_collection"
    }
)
```

**Configuration Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `persist_directory` | str | `"./data/chroma"` | Chroma data directory |
| `collection_name` | str | `"fastme_rag"` | Collection name (data isolation) |

**Use Cases:**

```python
# Environment isolation
rag_dev = FastMeRAG(chroma_collection="dev_collection")
rag_prod = FastMeRAG(chroma_collection="prod_collection")

# Project isolation
rag_project_a = FastMeRAG(chroma_collection="project_a")
rag_project_b = FastMeRAG(chroma_collection="project_b")

# Document type isolation
rag_manual = FastMeRAG(chroma_collection="manual_collection")
rag_log = FastMeRAG(chroma_collection="log_collection")
```

#### FAISS Vector Store

**Features:**
- ✅ In-memory storage (high performance)
- ✅ Supports persistence to disk
- ⚠️ No native metadata filtering (uses post-filtering strategy)

**Configuration:**

```python
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={
        "index_path": "./data/faiss_index"
    }
)
```

**Configuration Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `index_path` | str | `"./data/faiss_index"` | FAISS index path |

---

## 📚 Supported Document Types

| Document Type | `doc_type` | Splitter | Use Case | Recommended Config |
|---------------|------------|----------|----------|-------------------|
| 📋 Operation Logs | `"log"` | `LogSplitter` | Device fault logs, system operation logs | `chunk_max_size=500-800` |
| 📖 Equipment Manuals | `"manual"` | `ManualSplitter` | Operation manuals, maintenance manuals, technical specs | `chunk_max_size=1000-1500` |
| 📝 Workshop Orders | `"business"` | `BusinessSplitter` | Quality inspection forms, production records, work orders | `chunk_max_size=800-1200` |
| 🔧 Process SOPs | `"sop"` | `SopSplitter` | Work instructions, BOM documents, process flows | `chunk_max_size=1000-1500` |

### Document Type Metadata Fields

**Log Documents (log):**
```python
metadata = {
    "device_id": "EQ001",       # Device ID
    "line_id": "LN01",          # Production line ID
    "fault_code": "E001",       # Fault code
    "timestamp": "2024-01-15",  # Timestamp
    ...
}
```

**Manual Documents (manual):**
```python
metadata = {
    "chapter_num": "1",         # Chapter number
    "chapter_title": "Overview", # Chapter title
    "device_model": "EQ-1000",  # Device model
    ...
}
```

**Business Documents (business):**
```python
metadata = {
    "work_order_id": "WO001",   # Work order ID
    "material_id": "M001",      # Material ID
    "station": "Station_A",     # Station
    "quality_result": "Pass",   # Quality result
    ...
}
```

**SOP Documents (sop):**
```python
metadata = {
    "process_num": "Process 1",  # Process number
    "bom_items": ["PartA", "PartB"],  # BOM items
    "device_model": "EQ-1000",  # Device model
    ...
}
```

---

## 🎯 Predefined Scenarios

| Scenario | `scene` | Description | Document Type |
|----------|---------|-------------|---------------|
| 🛠️ Fault Diagnosis | `"fault_diagnosis"` | Diagnosis based on operation logs and fault records | log |
| 📖 Manual Query | `"manual_query"` | Equipment manual and technical document query | manual |
| 📋 Work Order Trace | `"work_order_trace"` | Work order and production record tracing | business |
| 💬 Default Q&A | `"default"` | General Q&A scenario | All types |

### Scenario Configuration File (config/scenes.yaml)

#### Single Document Type Scenario

```yaml
scenes:
  fault_diagnosis:
    doc_type: log                        # Single document type
    prompt_template: fault_diagnosis     # Prompt template name
    top_k: 5                             # Number of results
    source_fields:                       # Source fields
      - chunk_id
      - doc_id
      - device_id
      - fault_code
      - timestamp
    description: "Device fault diagnosis"
```

#### Multi-Document Type Scenarios (🆕 New Feature)

```yaml
scenes:
  # Comprehensive search - query logs and manuals simultaneously
  comprehensive_search:
    doc_type:                            # List format: match multiple document types
      - log
      - manual
    prompt_template: comprehensive
    top_k: 10
    source_fields:
      - chunk_id
      - doc_id
      - doc_type
      - source
    description: "Comprehensive search - logs + manuals"

  # Knowledge base scenario - exclude log type
  knowledge_base:
    doc_type:
      - manual
      - sop
      - business
    prompt_template: default
    top_k: 5
    description: "Knowledge base query - exclude logs"
```

**Multi-Document Type Notes:**
- `doc_type: ["log", "manual"]` is automatically converted to Chroma's `$in` operator
- Supports single string, list, and null formats
- FAISS vector store implements the same functionality via post-filtering

### Source Field Description

Fields included in `sources` for each scenario:

**Fault Diagnosis Scenario:**
- `chunk_id`: Chunk ID
- `doc_id`: Document ID
- `device_id`: Device ID
- `line_id`: Production line ID
- `fault_code`: Fault code
- `timestamp`: Timestamp
- `score`: Similarity score

**Manual Query Scenario:**
- `chunk_id`: Chunk ID
- `doc_id`: Document ID
- `chapter_num`: Chapter number
- `chapter_title`: Chapter title
- `device_model`: Device model
- `score`: Similarity score

**Work Order Trace Scenario:**
- `chunk_id`: Chunk ID
- `doc_id`: Document ID
- `work_order_id`: Work order ID
- `material_id`: Material ID
- `station`: Station
- `quality_result`: Quality result
- `score`: Similarity score

---

## 🏷️ Metadata Fields

### Automatically Extracted Industrial Fields

| Field | Chinese Label | English Label | Applicable Types | Regex Example |
|-------|---------------|---------------|-----------------|---------------|
| `device_id` | 设备 | Device | log, manual, sop | `设备 ID: EQ001` |
| `line_id` | 产线 | Production Line | log, business | `产线号: LN01` |
| `fault_code` | 故障码 | Fault Code | log | `故障代码: E001` |
| `work_order_id` | 工单号 | Work Order | business | `工单号: WO001` |
| `material_id` | 物料号 | Material | business, sop | `物料号: M001` |
| `station` | 工位 | Station | business | `工位: Station_A` |
| `quality_result` | 质检结果 | Quality Result | business | `质检结果: 合格` |
| `device_model` | 设备型号 | Device Model | manual, sop | `设备型号: EQ-1000` |
| `process_num` | 工序号 | Process | sop | `工序号: 工序 1` |
| `bom_items` | BOM 物料 | BOM Items | sop | `BOM: 零件A, 零件B` |
| `timestamp` | 时间 | Timestamp | log | `时间: 2024-01-15 10:30:00` |
| `chapter_num` | 章节号 | Chapter | manual | `第 1 章` |
| `chapter_title` | 章节标题 | Chapter Title | manual | `设备概述` |

### Configuration File (config/field_labels.yaml)

```yaml
zh:
  chunk_id: "片段 ID"
  doc_id: "文档 ID"
  device_id: "设备"
  fault_code: "故障码"
  ...

en:
  chunk_id: "Chunk ID"
  doc_id: "Document ID"
  device_id: "Device"
  fault_code: "Fault Code"
  ...
```

### Custom Metadata Extraction Rules

```python
# Add device model extraction rule
rag.add_metadata_rule(
    field="device_model",
    patterns=[
        r"设备型号 [::\s]*([A-Za-z0-9\-_]+)",
        r"产品型号 [::\s]*([A-Za-z0-9\-_]+)"
    ],
    description="Device model"
)

# Test extraction
result = rag.ingest("equipment_manual.pdf", doc_type="manual")
# metadata will contain automatically extracted device_model field
```

---

## ⚙️ Advanced Configuration

### Custom Scenario

```python
rag = FastMeRAG()

# Add quality check scenario
rag.add_scene(
    name="quality_check",                    # Scenario name
    doc_type="business",                     # Corresponding document type
    prompt_template="default",               # Prompt template
    top_k=5,                                 # Number of results
    source_fields=["work_order_id", "quality_result", "station"],  # Source fields
    description="Quality check scenario"
)

# Use new scenario
result = rag.chat("Is batch 2024001 qualified?", scene="quality_check")
```

### Update Scenario Configuration

```python
# Update scenario top_k
rag.update_scene_top_k(scene="fault_diagnosis", top_k=10)
```

### Switch Language

```python
# Switch to Chinese interface
rag.set_language("zh")

# Switch to English interface
rag.set_language("en")
```

### Query Statistics

```python
# Get all available scenarios
scenes = rag.get_scenes()
# ['fault_diagnosis', 'manual_query', 'work_order_trace', 'default']

# Get all supported document types
doc_types = rag.get_doc_types()
# ['log', 'manual', 'business', 'sop']

# Get total vector count
count = rag.get_vector_count()
print(f"Total vectors: {count}")
```

### Delete Collection

```python
# Delete current collection (clear all data)
rag.delete_collection()

# Re-ingest
rag.ingest("new_document.pdf", doc_type="manual")
```

---

## 👨‍💻 Developer Guide

This section is for developers who need to extend the framework's functionality, introducing how to add new scenes, splitters, and vector stores.

---

### Adding New Scenes

Scenes are a core concept of the FastMe RAG framework, used to route user questions to specific knowledge bases and Prompt templates. The framework provides two ways to add new scenes.

#### Method 1: Add via Configuration File (Recommended)

**Configuration File Location:** `config/scenes.yaml`

**Configuration Structure:**

```yaml
scenes:
  <scene_name>:
    doc_type: <document_type>          # log/manual/business/sop, or null for no restriction
    prompt_template: <template_name>    # Reference to template in prompt_templates.yaml
    top_k: <recall_count>              # Number of documents to return during retrieval
    source_fields:                     # Source traceability fields list
      - chunk_id
      - doc_id
      - <other_metadata_fields>
    description: <scene_description>
```

**Complete Example: Adding "Quality Check Query" Scene**

Edit `config/scenes.yaml` and add the new scene configuration:

```yaml
scenes:
  # ... existing scene configurations ...

  # New: Quality check query scene
  quality_check:
    doc_type: business              # Corresponds to work order document type
    prompt_template: quality_check  # Prompt template name
    top_k: 5                        # Recall 5 related records
    source_fields:                  # Source traceability fields
      - chunk_id
      - doc_id
      - doc_type
      - work_order_id
      - material_id
      - station
      - quality_result
      - timestamp
    description: "Quality record query - trace work order quality results"
```

Then, add the corresponding Prompt template in `config/prompt_templates.yaml`:

```yaml
quality_check:
  system: |
    You are a professional quality inspection assistant. Please answer user questions based on the retrieved quality inspection records.

    Answer requirements:
    1. Accurately cite key information such as work order IDs and quality results
    2. If there are any non-conforming items, explain specific issues and handling recommendations
    3. Keep answers concise and professional, highlighting key data
```

**Using the New Scene:**

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("quality_records.xlsx", doc_type="business")

# Use the new scene for Q&A
result = rag.chat(
    question="What is the quality result for work order WO001?",
    scene="quality_check"
)
print(result["answer"])
```

#### Method 2: Add Dynamically via Code

You can use the `add_scene()` method to dynamically add scenes at runtime without modifying configuration files.

**Method Signature:**

```python
rag.add_scene(
    name: str,              # Scene name (unique identifier)
    doc_type: str,          # Corresponding document type
    prompt_template: str,   # Prompt template name
    top_k: int = 5,         # Recall count
    source_fields: list = None,  # Source traceability fields list
    description: str = ""   # Scene description
)
```

**Complete Example:**

```python
from app_factory import FastMeRAG

# Initialize framework
rag = FastMeRAG()

# 1. Define Prompt template (needs to be configured in prompt_templates.yaml first)
# Or use an existing template, such as "default"

# 2. Dynamically add "Device Maintenance" scene
rag.add_scene(
    name="device_maintenance",
    doc_type="manual",          # Corresponds to device manuals
    prompt_template="default",  # Use default template
    top_k=8,                    # Recall 8 records
    source_fields=[
        "chunk_id",
        "doc_id",
        "chapter_num",
        "chapter_title",
        "device_model"
    ],
    description="Device maintenance guide query"
)

# 3. Ingest documents
rag.ingest("device_maintenance_manual.pdf", doc_type="manual")

# 4. Use the dynamically added scene
result = rag.chat(
    question="What are the daily maintenance steps for EQ-1000 device?",
    scene="device_maintenance"
)
print(result["answer"])

# 5. View source traceability information
for source in result["sources"]:
    print(f"  - Chapter {source['chapter_num']}: {source['chapter_title']}")
```

**Notes:**

- Dynamically added scenes will not persist after framework restart; use configuration file method for persistence
- `source_fields` defaults to `["chunk_id", "doc_id", "doc_type", "source"]`
- Scene names cannot duplicate existing scenes

---

### Adding New Splitters

Splitters are responsible for splitting documents into semantically complete chunks based on their structural characteristics. Adding a new Splitter requires inheriting from `BaseSplitter` and implementing the `split()` method.

#### Step Instructions

| Step | File Location | Description |
|------|---------------|-------------|
| 1. Create new Splitter class | `splitters/<name>_splitter.py` | Inherit from `BaseSplitter`, implement `split()` method |
| 2. Register to SplitterRegistry | `app_factory.py` | Register the new Splitter during initialization |
| 3. Update exports | `splitters/__init__.py` | Export the new class (optional) |

#### Base Class Structure

`BaseSplitter` is defined in `splitters/base.py`, key structure as follows:

```python
from abc import ABC, abstractmethod
from core.models import FastMeDocument, FastMeChunk

class BaseSplitter(ABC):
    def __init__(self, max_chunk_size: int = 1000):
        """Initialize splitter, set maximum chunk size"""
        self.max_chunk_size = max_chunk_size

    @abstractmethod
    def split(self, document: FastMeDocument) -> list[FastMeChunk]:
        """
        Split document into chunk list

        Args:
            document: FastMeDocument instance containing document content

        Returns:
            FastMeChunk list, each chunk contains unique ID, text, and metadata
        """
        pass
```

**Available Helper Methods (inherited from BaseSplitter):**

| Method | Purpose |
|--------|---------|
| `_split_by_paragraphs(lines, max_size)` | Split by paragraphs, control size |
| `_split_large_text(content, max_size)` | Large text splitting helper |
| `_generate_chunk_id(doc_id, chunk_index, ...)` | Generate chunk ID |
| `_build_chunk_metadata(document, ...)` | Build standard metadata dictionary |
| `_extract_with_patterns(text, patterns, findall)` | Regex extraction helper |

#### Complete Example: Adding "Technical Specification" Splitter

Suppose we need to process technical specification documents, splitting them by "specification item" structure.

**Step 1: Create New Splitter Class**

Create file `splitters/spec_splitter.py`:

```python
"""
Technical Specification Splitter - SpecSplitter

Splits technical specification documents by specification items, each item contains:
- Specification name
- Specification value
- Unit
- Test conditions
"""
import re
from typing import List
from splitters.base import BaseSplitter
from core.models import FastMeDocument, FastMeChunk


class SpecSplitter(BaseSplitter):
    """Technical Specification Splitter"""

    def __init__(self, max_chunk_size: int = 800):
        """
        Initialize

        Args:
            max_chunk_size: Maximum chunk size, default 800 characters
                           Specification items are usually short, recommend 600-1000
        """
        super().__init__(max_chunk_size)

    def split(self, document: FastMeDocument) -> List[FastMeChunk]:
        """
        Split document by specification items

        Args:
            document: FastMeDocument instance

        Returns:
            FastMeChunk list, each chunk corresponds to a specification item
        """
        chunks = []
        text = document.text
        doc_id = document.doc_id

        # 1. Split by specification item pattern (assumes format: "Spec Name: Spec Value")
        # Example text:
        # Input Voltage: 220V AC
        # Power: 500W
        # Operating Temperature: -20°C ~ 60°C

        spec_pattern = re.compile(
            r'^([^:\n]+):\s*([^\n]+)$',
            re.MULTILINE
        )

        # 2. Extract all specification items
        matches = list(spec_pattern.finditer(text))

        if not matches:
            # If no specification format matched, split by paragraphs
            return self._fallback_split(document)

        # 3. Create chunk for each specification item
        for i, match in enumerate(matches):
            spec_name = match.group(1).strip()
            spec_value = match.group(2).strip()

            # Build chunk text
            chunk_text = f"{spec_name}: {spec_value}"

            # Handle oversized specification values
            if len(chunk_text) > self.max_chunk_size:
                chunk_text = chunk_text[:self.max_chunk_size]

            # Generate chunk ID
            chunk_id = self._generate_chunk_id(doc_id, i, len(matches))

            # Build metadata
            metadata = {
                "spec_name": spec_name,        # Specification name
                "spec_value": spec_value,      # Specification value
                "doc_type": "spec",            # Document type
                **document.metadata           # Inherit document-level metadata
            }

            # Create chunk
            chunk = FastMeChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                doc_type="spec",
                text=chunk_text,
                metadata=metadata
            )
            chunks.append(chunk)

        return chunks

    def _fallback_split(self, document: FastMeDocument) -> List[FastMeChunk]:
        """Fallback splitting strategy: split by paragraphs"""
        lines = document.text.split('\n')
        return self._split_by_paragraphs(lines, self.max_chunk_size)
```

**Step 2: Register to SplitterRegistry**

Modify `app_factory.py`, register the new Splitter in the initialization method:

```python
# Add import at the top of app_factory.py
from splitters.spec_splitter import SpecSplitter

# In FastMeRAG.__init__ method, find the Splitter registration section (around lines 221-225)
# Add new registration:

def __init__(self, ...):
    # ... other initialization code ...

    # Register splitters
    self.splitter_registry = SplitterRegistry()
    self.splitter_registry.register("log", LogSplitter(max_chunk_size=self.chunk_max_size))
    self.splitter_registry.register("manual", ManualSplitter(max_chunk_size=self.chunk_max_size))
    self.splitter_registry.register("business", BusinessSplitter(max_chunk_size=self.chunk_max_size))
    self.splitter_registry.register("sop", SopSplitter(max_chunk_size=self.chunk_max_size))

    # Add: Register new specification splitter
    self.splitter_registry.register("spec", SpecSplitter(max_chunk_size=self.chunk_max_size))
```

**Step 3: Update Configuration (Optional)**

If you need to add a corresponding scene for the new document type, edit `config/scenes.yaml`:

```yaml
scenes:
  spec_query:
    doc_type: spec
    prompt_template: default
    top_k: 10
    source_fields:
      - chunk_id
      - doc_id
      - spec_name
      - spec_value
    description: "Technical specification query"
```

**Using the New Splitter:**

```python
from app_factory import FastMeRAG

rag = FastMeRAG()

# Ingest using the new spec document type
result = rag.ingest("product_specification.xlsx", doc_type="spec")
print(f"Ingestion successful: {result['chunks_count']} specification items")

# Query specifications
result = rag.chat("What is the input voltage?", scene="spec_query")
print(result["answer"])
```

---

### Adding New Vector Stores

FastMe RAG supports multiple vector databases, implementing pluggability through the adapter pattern. Adding a new vector store requires:

1. Implement the `VectorStoreAdapter` interface
2. Create an adapter class
3. Update `VectorStoreFactory`
4. Create the corresponding Retriever

#### Step Instructions

| Step | File Location | Description |
|------|---------------|-------------|
| 1. Create adapter class | `vector_stores/<name>.py` | Inherit from `VectorStoreAdapter`, implement all abstract methods |
| 2. Create retriever class | `vector_stores/<name>_retriever.py` | Inherit from `BaseRetriever`, implement `retrieve()` method |
| 3. Update VectorStoreFactory | `vector_stores/factory.py` | Add creation logic for new vector store type |
| 4. Update RetrieverFactory | `retrievers/factory.py` | Add creation logic for new retriever |

#### Interface Definitions

**VectorStoreAdapter Abstract Base Class** (`vector_stores/base.py`):

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from langchain_core.documents import Document

class VectorStoreAdapter(ABC):
    """Vector store adapter abstract base class"""

    @abstractmethod
    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> None:
        """Add documents to vector store"""
        pass

    @abstractmethod
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """Similarity search, returns list of (Document, score) tuples"""
        pass

    @abstractmethod
    def get_count(self) -> int:
        """Return total vector count in vector store"""
        pass

    @abstractmethod
    def delete_collection(self) -> None:
        """Delete entire collection"""
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Return configuration info dictionary"""
        pass

    # Optional methods (with default implementation)
    def persist(self) -> None:
        """Persist data"""
        pass

    def supports_filter(self) -> bool:
        """Whether native metadata filtering is supported"""
        return True

    def sanitize_metadata(self, metadata: Dict) -> Dict:
        """Clean metadata, keep only basic types"""
        # Default implementation provided
        pass
```

**BaseRetriever Abstract Base Class** (`core/retriever.py`):

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from core.models import FastMeSearchResult
from core.retriever import FilterCondition

class BaseRetriever(ABC):
    """Retriever abstract base class"""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[List[FilterCondition]] = None
    ) -> List[FastMeSearchResult]:
        """Execute retrieval"""
        pass

    @abstractmethod
    def supports_filter(self) -> bool:
        """Whether filtering is supported"""
        pass
```

#### Complete Example: Adding Milvus Vector Store

Using Milvus as an example, demonstrating how to add new vector store support.

**Step 1: Create Adapter Class**

Create file `vector_stores/milvus.py`:

```python
"""
Milvus Vector Store Adapter

Supports Milvus distributed vector database, suitable for large-scale production environments.
"""
from typing import List, Optional, Dict, Any, Tuple
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from vector_stores.base import VectorStoreAdapter


class MilvusAdapter(VectorStoreAdapter):
    """Milvus Vector Store Adapter"""

    def __init__(
        self,
        collection_name: str,
        connection_args: Dict[str, Any],
        embedding_function: Embeddings
    ):
        """
        Initialize Milvus adapter

        Args:
            collection_name: Collection name
            connection_args: Connection parameters, e.g. {"host": "localhost", "port": "19530"}
            embedding_function: Embedding function
        """
        self.collection_name = collection_name
        self.connection_args = connection_args
        self.embedding_function = embedding_function

        # Lazy import to avoid errors if not installed
        from langchain_milvus import Milvus

        # Create Milvus vector store instance
        self._milvus = Milvus(
            embedding_function=embedding_function,
            collection_name=collection_name,
            connection_args=connection_args
        )

    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to Milvus

        Args:
            documents: LangChain Document list
            ids: Optional document ID list
        """
        # Clean metadata (Milvus only supports basic types)
        sanitized_docs = []
        for doc in documents:
            clean_metadata = self.sanitize_metadata(doc.metadata)
            sanitized_docs.append(Document(
                page_content=doc.page_content,
                metadata=clean_metadata
            ))

        # Milvus auto-generates IDs, passed ids parameter not currently supported
        self._milvus.add_documents(sanitized_docs)

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        Similarity search

        Args:
            query: Query text
            k: Return count
            filter: Metadata filter conditions

        Returns:
            List of (Document, score) tuples
        """
        # Milvus supports native metadata filtering
        # Filter condition format example: {"device_id": "EQ001"}
        results = self._milvus.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter  # Milvus uses expr parameter, LangChain auto-converts
        )
        return results

    def get_count(self) -> int:
        """Return total vector count"""
        # Milvus statistics require querying collection
        from pymilvus import connections, Collection

        # Get collection statistics
        connections.connect(
            alias="default",
            host=self.connection_args.get("host", "localhost"),
            port=self.connection_args.get("port", "19530")
        )
        collection = Collection(self.collection_name)
        count = collection.num_entities
        return count

    def delete_collection(self) -> None:
        """Delete collection"""
        from pymilvus import connections, utility

        connections.connect(
            alias="default",
            host=self.connection_args.get("host", "localhost"),
            port=self.connection_args.get("port", "19530")
        )

        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)

        # Recreate empty collection
        self._milvus = Milvus(
            embedding_function=self.embedding_function,
            collection_name=self.collection_name,
            connection_args=self.connection_args
        )

    def get_config(self) -> Dict[str, Any]:
        """Return configuration info"""
        return {
            "collection_name": self.collection_name,
            "connection_args": self.connection_args,
            "vector_count": self.get_count(),
            "supports_filter": True
        }

    def supports_filter(self) -> bool:
        """Milvus supports native metadata filtering"""
        return True
```

**Step 2: Create Retriever Class**

Create file `vector_stores/milvus_retriever.py`:

```python
"""
Milvus Retriever

Responsible for converting filter conditions to Milvus query expressions and executing retrieval.
"""
from typing import List, Optional
from langchain_core.documents import Document
from core.models import FastMeSearchResult
from core.retriever import BaseRetriever, ResultConverterMixin, FilterCondition
from vector_stores.milvus import MilvusAdapter


class MilvusRetriever(BaseRetriever, ResultConverterMixin):
    """Milvus Retriever"""

    def __init__(self, adapter: MilvusAdapter):
        """
        Initialize retriever

        Args:
            adapter: Milvus adapter instance
        """
        self.adapter = adapter

    def retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[List[FilterCondition]] = None
    ) -> List[FastMeSearchResult]:
        """
        Execute retrieval

        Args:
            query: Query text
            top_k: Return count
            filters: Filter conditions list

        Returns:
            FastMeSearchResult list
        """
        # Convert FilterCondition list to Milvus filter expression
        milvus_filter = None
        if filters:
            milvus_filter = self._to_milvus_filter(filters)

        # Execute similarity search
        results = self.adapter.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=milvus_filter
        )

        # Convert to FastMeSearchResult
        return self._to_fastme_results(results)

    def _to_milvus_filter(
        self,
        conditions: List[FilterCondition]
    ) -> Optional[str]:
        """
        Convert FilterCondition list to Milvus filter expression

        Milvus uses SQL-like expressions, such as:
        - Single condition: device_id == "EQ001"
        - Multiple conditions: device_id == "EQ001" and line_id == "LN01"

        Args:
            conditions: FilterCondition list

        Returns:
            Milvus filter expression string
        """
        if not conditions:
            return None

        # Operator mapping
        op_map = {
            "$eq": "==",
            "$ne": "!=",
            "$gt": ">",
            "$gte": ">=",
            "$lt": "<",
            "$lte": "<=",
            "$in": "in",
            "$nin": "not in"
        }

        expr_parts = []
        for cond in conditions:
            op = op_map.get(cond.operator, "==")
            field = cond.field
            value = cond.value

            # Handle string values
            if isinstance(value, str):
                expr_parts.append(f'{field} {op} "{value}"')
            # Handle list values ($in, $nin)
            elif isinstance(value, list):
                value_str = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                expr_parts.append(f'{field} {op} [{value_str}]')
            # Handle numeric values
            else:
                expr_parts.append(f'{field} {op} {value}')

        # Multiple conditions use AND connection
        return " and ".join(expr_parts)

    def supports_filter(self) -> bool:
        """Supports filtering"""
        return True
```

**Step 3: Update VectorStoreFactory**

Modify `vector_stores/factory.py`, add Milvus type:

```python
# Add import at top of file
from vector_stores.milvus import MilvusAdapter

class VectorStoreFactory:
    @staticmethod
    def create(
        vector_store_type: str,
        embeddings: Embeddings,
        vector_store_config: Dict[str, Any]
    ) -> VectorStoreAdapter:
        """
        Create vector store adapter

        Args:
            vector_store_type: Vector store type ("chroma" | "faiss" | "milvus")
            embeddings: Embedding function
            vector_store_config: Configuration dictionary

        Returns:
            VectorStoreAdapter instance
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
                index_path=vector_store_config.get("index_path", "./data/faiss_index"),
                load_existing=True
            )

        # New: Milvus vector store
        elif vector_store_type == "milvus":
            return MilvusAdapter(
                collection_name=vector_store_config.get("collection_name", "fastme_rag"),
                connection_args=vector_store_config.get("connection_args", {"host": "localhost", "port": "19530"}),
                embedding_function=embeddings
            )

        else:
            raise ValueError(f"Unsupported vector store type: {vector_store_type}")
```

**Step 4: Update RetrieverFactory**

Modify `retrievers/factory.py`, add Milvus retriever:

```python
# Add import at top of file
from vector_stores.milvus_retriever import MilvusRetriever

class RetrieverFactory:
    @staticmethod
    def create(
        vector_store_type: str,
        vector_store_adapter: VectorStoreAdapter,
        scene_router: SceneRouter,
        retriever_config: Optional[Dict[str, Any]] = None
    ) -> BaseRetriever:
        """
        Create retriever

        Args:
            vector_store_type: Vector store type
            vector_store_adapter: Vector store adapter
            scene_router: Scene router
            retriever_config: Retriever configuration

        Returns:
            BaseRetriever instance (wrapped by SceneAwareRetriever)
        """
        retriever_config = retriever_config or {}

        # Create corresponding retriever based on vector store type
        if vector_store_type == "chroma":
            from vector_stores.chroma_retriever import ChromaRetriever
            base_retriever = ChromaRetriever(adapter=vector_store_adapter)

        elif vector_store_type == "faiss":
            from vector_stores.faiss_retriever import FAISSRetriever
            post_filter_multiplier = retriever_config.get("post_filter_multiplier", 5)
            base_retriever = FAISSRetriever(
                adapter=vector_store_adapter,
                post_filter_multiplier=post_filter_multiplier
            )

        # New: Milvus retriever
        elif vector_store_type == "milvus":
            base_retriever = MilvusRetriever(adapter=vector_store_adapter)

        else:
            raise ValueError(f"Unsupported vector store type: {vector_store_type}")

        # Wrap as scene-aware retriever
        from retrievers.scene_aware import SceneAwareRetriever
        return SceneAwareRetriever(base_retriever, scene_router)
```

**Using the New Vector Store:**

```python
from app_factory import FastMeRAG

# Use Milvus vector store
rag = FastMeRAG(
    vector_store_type="milvus",
    vector_store_config={
        "collection_name": "manufacturing_rag",
        "connection_args": {
            "host": "localhost",
            "port": "19530"
        }
    }
)

# Ingest documents
rag.ingest("device_manual.pdf", doc_type="manual")

# Q&A
result = rag.chat("Device operation steps", scene="manual_query")
print(result["answer"])
```

#### Best Practices for Adding Vector Stores

1. **Metadata Handling**: Different vector stores have different support for metadata types, recommend calling `sanitize_metadata()` in `add_documents()` to clean data

2. **Filter Condition Conversion**: Each vector store has different filter syntax, need to implement conversion logic in Retriever

3. **Lazy Import**: Use `try/except` or lazy import to handle cases where dependencies are not installed

4. **Connection Management**: Distributed vector stores need connection pool management, recommend handling within adapter

5. **Error Handling**: Encapsulate vector store-specific exceptions, provide user-friendly error messages

---

## 📁 Project Structure

```
FASTME-RAG/
├── app_factory.py              # Main framework entry (FastMeRAG class)
├── app.py                      # Usage examples
├── requirements.txt            # Python dependencies
├── README.md                   # Chinese documentation
├── README_EN.md                # English documentation
│
├── core/                       # Core modules
│   ├── models.py              # Data models (FastMeDocument, FastMeChunk, FastMeSearchResult)
│   ├── ingest_pipeline.py     # Document ingestion pipeline
│   ├── chat_pipeline.py       # Conversation pipeline
│   └── retriever.py           # Retriever abstract base class
│
├── vector_stores/              # Vector store modules
│   ├── __init__.py            # Exports VectorStoreFactory, ChromaAdapter, FAISSAdapter
│   ├── base.py                # VectorStoreAdapter abstract base class
│   ├── factory.py             # VectorStoreFactory (vector store factory)
│   ├── chroma.py              # ChromaAdapter (Chroma adapter)
│   ├── faiss.py               # FAISSAdapter (FAISS adapter)
│   ├── chroma_retriever.py    # ChromaRetriever (Chroma retriever)
│   └── faiss_retriever.py     # FAISSRetriever (FAISS retriever)
│
├── retrievers/                 # Retriever modules
│   ├── __init__.py            # Exports RetrieverFactory, SceneAwareRetriever
│   ├── factory.py             # RetrieverFactory (retriever factory)
│   └── scene_aware.py         # SceneAwareRetriever (scenario-aware retriever)
│
├── splitters/                  # Document splitters
│   ├── base.py                # BaseSplitter (splitter base class)
│   ├── log_splitter.py        # LogSplitter (log splitter)
│   ├── manual_splitter.py     # ManualSplitter (manual splitter)
│   ├── business_splitter.py   # BusinessSplitter (work order splitter)
│   └── sop_splitter.py        # SopSplitter (SOP splitter)
│
├── manufacturing/              # Manufacturing-specific components
│   └── metadata_extractor.py  # IndustrialMetadataExtractor (metadata extractor)
│
├── routers/                    # Routers
│   └── scene_router.py        # SceneRouter (scenario router)
│
├── adapters/                   # Adapters
│   ├── __init__.py            # Exports PromptAdapter, SimpleDocumentLoader
│   ├── prompt_adapter.py      # PromptAdapter (prompt adapter)
│   └── document_loader.py     # SimpleDocumentLoader (document loader)
│
├── config/                     # Configuration files
│   ├── scenes.yaml            # Scenario configuration
│   ├── metadata_rules.yaml    # Metadata extraction rules
│   ├── prompt_templates.yaml  # Prompt templates
│   └── field_labels.yaml      # Field labels (multi-language)
│
├── examples/                   # Usage examples
│   ├── README.md              # Example documentation
│   ├── quickstart.py          # Quick start
│   ├── scene_chat.py          # Scenario Q&A example
│   ├── custom_config.py       # Custom configuration example
│   └── chat_stream_example.py # Streaming output example
│
└── tests/                      # Unit tests
    ├── test_app_factory.py    # Main framework tests
    ├── test_splitters.py      # Splitter tests
    ├── test_retrievers.py     # Retriever tests
    └── test_vector_stores.py  # Vector store tests
```

---

## 🧪 Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific tests
python -m pytest tests/test_splitters.py -v
python -m pytest tests/test_retrievers.py -v

# Run tests with coverage
python -m pytest tests/ -v --cov=. --cov-report=html
```

---

## 📝 Complete Examples

### Example 1: Fault Diagnosis Scenario

```python
from app_factory import FastMeRAG

# Initialize
rag = FastMeRAG(
    chroma_collection="fault_diagnosis_collection"
)

# Ingest fault logs
rag.ingest(
    file_path="./logs/fault_log_20240115.log",
    doc_type="log",
    extra_metadata={
        "project": "Production Line A",
        "date": "2024-01-15"
    }
)

# Fault diagnosis Q&A
result = rag.chat(
    question="What faults does device E001 have recently?",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}
)

print(f"Answer: {result['answer']}")
print("\nSources:")
for source in result["sources"]:
    print(f"  - [{source['timestamp']}] {source['fault_code']}: {source['preview'][:50]}...")
```

### Example 2: Manual Query Scenario

```python
from app_factory import FastMeRAG

# Initialize
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={"index_path": "./data/manuals_faiss"}
)

# Batch ingest manuals
rag.batch_ingest(
    folder_path="./manuals",
    doc_type="manual"
)

# Manual query Q&A
result = rag.chat(
    question="What are the equipment startup steps?",
    scene="manual_query"
)

print(f"Answer: {result['answer']}")
print("\nSource chapters:")
for source in result["sources"]:
    print(f"  - Chapter {source['chapter_num']} {source['chapter_title']}")
```

### Example 3: Work Order Trace Scenario

```python
from app_factory import FastMeRAG

# Initialize
rag = FastMeRAG()

# Ingest work orders
rag.ingest("./work_orders/wo_20240115.xlsx", doc_type="business")

# Work order trace Q&A
result = rag.chat(
    question="What is the quality result for work order WO001?",
    scene="work_order_trace",
    filters={"work_order_id": "WO001"}
)

print(f"Answer: {result['answer']}")
for source in result["sources"]:
    print(f"  - Work Order: {source['work_order_id']}")
    print(f"  - Quality Result: {source['quality_result']}")
    print(f"  - Station: {source['station']}")
```

### Example 4: Streaming Q&A

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("equipment_manual.pdf", doc_type="manual")

print("AI: ", end="", flush=True)
for chunk in rag.chat_stream(
    question="What is the maintenance interval for the equipment?",
    scene="manual_query"
):
    print(chunk, end="", flush=True)
print()
```

### Example 5: Multi-language Support

```python
from app_factory import FastMeRAG

# Using Chinese interface
rag_zh = FastMeRAG(language="zh")
result_zh = rag_zh.chat("设备故障如何处理？", scene="fault_diagnosis")

# Switch to English interface
rag_en = FastMeRAG(language="en")
result_en = rag_en.chat("How to handle device faults?", scene="fault_diagnosis")

# Dynamic language switching
rag = FastMeRAG(language="zh")
rag.set_language("en")  # Switch to English
result = rag.chat("Device maintenance steps?", scene="manual_query")
```

---

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - RAG framework foundation
- [ChromaDB](https://github.com/chroma-core/chroma) - Vector database
- [FAISS](https://github.com/facebookresearch/faiss) - Vector retrieval library
- [HuggingFace](https://huggingface.co/) - Embedding model

---

## 📬 Contact

- 🐛 Issues: [GitHub Issues](https://github.com/happy-momo/FASTME-RAG/issues)

---

<div align="center">

**Made with ❤️ for Manufacturing Industry**

[⭐ Star this repo](https://github.com/happy-momo/FASTME-RAG) if you find it useful!

</div>