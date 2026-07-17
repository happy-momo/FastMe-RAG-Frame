# FastMe RAG API Reference

This document provides detailed description of all public APIs in the FastMe RAG framework.

---

## Table of Contents

- [FastMeRAG Class](#fasemerag-class)
  - [Initialization Method](#initialization-method)
  - [Document Ingestion Methods](#document-ingestion-methods)
  - [Scene-aware Q&A Methods](#scene-aware-qa-methods)
  - [Configuration Management Methods](#configuration-management-methods)
  - [Query and Statistics Methods](#query-and-statistics-methods)
- [Data Models](#data-models)
- [Exception Classes](#exception-classes)

---

## FastMeRAG Class

Main framework entry class providing unified API interfaces.

### Initialization Method

#### `FastMeRAG.__init__()`

Initialize the FastMe RAG framework.

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `embedding_model` | str | `"BAAI/bge-m3"` | HuggingFace Embedding model name |
| `model_cache_dir` | str | `"./models"` | Model cache directory |
| `llm_base_url` | str | `"http://localhost:8000/v1/chat/completions"` | LLM API address |
| `llm_api_key` | str | `"sk-1234567890abcdef..."` | LLM API Key |
| `llm_model` | str | `"qwen-plus"` | LLM model name |
| `temperature` | float | `0.2` | LLM temperature parameter |
| `language` | str | `"zh"` | Interface language ("zh" or "en") |
| `chunk_max_size` | int | `1000` | Maximum characters per chunk |
| `ingest_batch_size` | int | `32` | Ingestion batch size |
| `embedding_batch_size` | int | `32` | Embedding batch size |
| `show_progress_bar` | bool | `False` | Whether to show progress bar |
| `vector_store_type` | str | `"chroma"` | Vector store type ("chroma" or "faiss") |
| `vector_store_config` | dict | `None` | Vector store specific configuration |
| `chroma_dir` | str | `"./data/chroma"` | Chroma data directory (backward compatible) |
| `chroma_collection` | str | `"fastme_rag"` | Chroma collection name (backward compatible) |

**Example**:

```python
from app_factory import FastMeRAG

# Default configuration
rag = FastMeRAG()

# Custom configuration
rag = FastMeRAG(
    embedding_model="BAAI/bge-m3",
    llm_base_url="http://localhost:8000/v1/chat/completions",
    llm_model="qwen-plus",
    chunk_max_size=1000,
    vector_store_type="chroma"
)

# Using FAISS vector store
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={"index_path": "./data/faiss_index"}
)
```

---

### Document Ingestion Methods

#### `ingest()`

Execute single document ingestion.

**Method Signature**:

```python
def ingest(
    self,
    file_path: str,
    doc_type: str,
    extra_metadata: Optional[dict] = None,
    require_review: bool = False
) -> dict
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | str | Yes | File path, supports PDF, DOCX, TXT, LOG, MD formats |
| `doc_type` | str | Yes | Document type: `"log"`, `"manual"`, `"business"`, `"sop"` |
| `extra_metadata` | dict | No | Extra metadata injected into all chunks |
| `require_review` | bool | No | Review mode. If True, returns chunk preview without ingestion |

**Return Value**:

On success:
```python
{
    "status": "success",
    "doc_id": "doc_20240115_abc123",
    "file_name": "equipment_manual.pdf",
    "doc_type": "manual",
    "chunks_count": 15,
    "vector_count": 115
}
```

In review mode:
```python
{
    "status": "waiting_review",
    "doc_id": "doc_20240115_abc123",
    "file_name": "equipment_manual.pdf",
    "doc_type": "manual",
    "chunks": [...]
}
```

**Example**:

```python
# Basic ingestion
result = rag.ingest("equipment_manual.pdf", doc_type="manual")
print(f"Successfully ingested: {result['chunks_count']} chunks")

# With extra metadata
result = rag.ingest(
    file_path="fault_log.log",
    doc_type="log",
    extra_metadata={"device_id": "EQ001", "line_id": "LN01"}
)

# Review mode
result = rag.ingest("work_order.xlsx", doc_type="business", require_review=True)
if result["status"] == "waiting_review":
    print(f"Pending review: {len(result['chunks'])} chunks")
```

---

#### `batch_ingest()`

Execute batch folder ingestion.

**Method Signature**:

```python
def batch_ingest(
    self,
    folder_path: str,
    doc_type: str,
    extra_metadata: Optional[dict] = None,
    file_extensions: Optional[List[str]] = None,
    persist_interval: int = 10
) -> list
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `folder_path` | str | - | Folder path |
| `doc_type` | str | - | Document type |
| `extra_metadata` | dict | `None` | Extra metadata shared by all files |
| `file_extensions` | list | `[".pdf", ".docx", ".txt", ".log", ".md"]` | File extension filter |
| `persist_interval` | int | `10` | Memory cleanup interval (every N files) |

**Return Value**:

```python
[
    {"status": "success", "doc_id": "doc_001", "chunks_count": 10, ...},
    {"status": "success", "doc_id": "doc_002", "chunks_count": 15, ...},
    {"status": "error", "file": "failed.pdf", "error": "Cannot parse file"}
]
```

**Example**:

```python
# Batch ingestion
results = rag.batch_ingest(
    folder_path="./logs",
    doc_type="log",
    extra_metadata={"project": "ProductionLineA"}
)

# Count results
success = sum(1 for r in results if r["status"] == "success")
print(f"Successfully ingested {success} files")
```

---

### Scene-aware Q&A Methods

#### `chat()`

Execute synchronous scene-aware Q&A.

**Method Signature**:

```python
def chat(
    self,
    question: str,
    scene: str = "default",
    filters: Optional[dict] = None,
    top_k: Optional[int] = None
) -> dict
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `question` | str | - | User question |
| `scene` | str | `"default"` | Scene name |
| `filters` | dict | `None` | Filter conditions |
| `top_k` | int | Scene config | Retrieval count |

**Return Value**:

```python
{
    "question": "How to handle device alarm?",
    "scene": "fault_diagnosis",
    "filters": {"device_id": "EQ001"},
    "answer": "According to log records, E001 device...",
    "sources": [...]
}
```

**Example**:

```python
# Basic Q&A
result = rag.chat("How to handle device alarm?", scene="fault_diagnosis")
print(result["answer"])

# With filter conditions
result = rag.chat(
    question="What faults does E001 device have?",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}
)

# View source tracing
for source in result["sources"]:
    print(f"  - [{source['score']:.2f}] {source['preview'][:50]}...")
```

---

#### `chat_stream()`

Execute streaming scene-aware Q&A.

**Method Signature**:

```python
def chat_stream(
    self,
    question: str,
    scene: str = "default",
    filters: Optional[dict] = None,
    top_k: Optional[int] = None
) -> Generator[str, None, None]
```

**Return Value**:

Generator yielding text chunks.

**Example**:

```python
print("AI: ", end="", flush=True)
for chunk in rag.chat_stream(
    question="What are the device operation steps?",
    scene="manual_query"
):
    print(chunk, end="", flush=True)
print()
```

---

#### `chat_with_memory()`

Execute Q&A with conversation memory.

**Method Signature**:

```python
def chat_with_memory(
    self,
    question: str,
    session_id: str,
    scene: str = "default",
    filters: Optional[dict] = None,
    top_k: Optional[int] = None
) -> dict
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `question` | str | - | User question |
| `session_id` | str | - | Session ID |
| `scene` | str | `"default"` | Scene name |
| `filters` | dict | `None` | Filter conditions |
| `top_k` | int | Scene config | Retrieval count |

**Example**:

```python
# Create session memory
rag.create_memory(session_id="user_001", max_turns=10)

# First conversation round
result1 = rag.chat_with_memory(
    question="What faults does E001 device have?",
    session_id="user_001",
    scene="fault_diagnosis"
)

# Second conversation round (automatically carries context)
result2 = rag.chat_with_memory(
    question="How to handle this fault?",
    session_id="user_001",
    scene="fault_diagnosis"
)
```

---

### Memory Management Methods

#### `create_memory()`

Create session memory.

**Method Signature**:

```python
def create_memory(
    self,
    session_id: str,
    max_turns: int = 10
) -> None
```

---

#### `get_memory()`

Get session memory.

**Method Signature**:

```python
def get_memory(
    self,
    session_id: str
) -> Optional[ConversationBufferMemory]
```

---

#### `clear_memory()`

Clear memory.

**Method Signature**:

```python
def clear_memory(
    self,
    session_id: Optional[str] = None
) -> None
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | str | `None` | Session ID, None clears all |

---

### Configuration Management Methods

#### `add_scene()`

Dynamically add scene configuration.

**Method Signature**:

```python
def add_scene(
    self,
    name: str,
    doc_type: str,
    prompt_template: str,
    top_k: int = 5,
    source_fields: Optional[list] = None,
    description: str = ""
) -> None
```

---

#### `add_metadata_rule()`

Dynamically add metadata extraction rule.

**Method Signature**:

```python
def add_metadata_rule(
    self,
    field: str,
    patterns: list,
    description: str = ""
) -> None
```

---

#### `update_scene_top_k()`

Update scene top_k configuration.

**Method Signature**:

```python
def update_scene_top_k(
    self,
    scene: str,
    top_k: int
) -> None
```

---

#### `set_language()`

Switch language.

**Method Signature**:

```python
def set_language(
    self,
    language: str
) -> None
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `language` | str | Language code, supports `"zh"` or `"en"` |

---

### Query and Statistics Methods

#### `get_scenes()`

Get all available scenes.

**Return Value**: `list[str]` - List of scene names

---

#### `get_doc_types()`

Get all supported document types.

**Return Value**: `list[str]` - List of document types

---

#### `get_vector_count()`

Get total vector count in vector store.

**Return Value**: `int` - Vector count

---

#### `delete_collection()`

Delete current collection.

**Warning**: This operation is irreversible and deletes all data.

---

## Data Models

### FastMeDocument

Document-level data model.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `doc_id` | str | Unique document identifier |
| `doc_type` | str | Document type (log/manual/business/sop) |
| `file_name` | str | File name |
| `file_path` | str | Full file path |
| `text` | str | Full document text content |
| `metadata` | dict | Document metadata |

---

### FastMeChunk

Chunk-level data model.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `chunk_id` | str | Unique chunk identifier |
| `doc_id` | str | Parent document ID |
| `doc_type` | str | Document type |
| `text` | str | Chunk text content |
| `metadata` | dict | Chunk metadata |

---

### FastMeSearchResult

Search result model.

**Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `chunk_id` | str | Chunk ID |
| `doc_id` | str | Document ID |
| `doc_type` | str | Document type |
| `text` | str | Chunk text content |
| `score` | float | Similarity score, range [0, 1] |
| `metadata` | dict | Chunk metadata |

---

## Exception Classes

### ValueError

Thrown when parameters are invalid.

**Common scenarios**:
- `doc_type` has no registered splitter
- `scene` does not exist
- `language` is not supported

---

### FileNotFoundError

Thrown when file or folder does not exist.

---

## Related Documentation

- [Architecture Design](ARCHITECTURE_EN.md) - Detailed architecture design and module decoupling
- [Developer Guide](DEVELOPER_GUIDE_EN.md) - Detailed steps for adding scenes, splitters, and vector stores
- [Quick Start](QUICKSTART_EN.md) - Simplified quick start tutorial
