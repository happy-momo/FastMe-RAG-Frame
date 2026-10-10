# FastMe RAG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://img.shields.io/github/actions/workflow/status/happy-momo/FastMe-RAG-Frame/ci.yml?branch=frame-0.2)](https://github.com/happy-momo/FastMe-RAG-Frame/actions)

**FastMe RAG** is a lightweight, pluggable Retrieval-Augmented Generation (RAG) framework purpose-built for manufacturing. It is designed for factory equipment manuals, operation logs, workshop work orders, and process SOPs, providing scene-aware Q&A, automatic industrial metadata extraction, and multi-vector-store support.

> 📖 [中文 README](README.md) | 📖 [Documentation](docs/README.md) | 📖 [Examples](examples/README.md)

---

## ✨ Key Features

- 🏭 **Manufacturing-specific splitters**: four built-in splitters (logs, manuals, work orders, SOPs) that chunk documents based on industrial structure.
- 🔍 **Scene-aware Q&A**: built-in scenes for fault diagnosis, manual query, and work order trace, routing questions to the right knowledge base.
- 🏷️ **Industrial metadata extraction**: auto-extracts device ID, line ID, fault code, work order ID, and other industrial fields to improve retrieval precision.
- 🔌 **Pluggable architecture**: built on LangChain; embeddings, vector stores, and LLM are all config-driven and swappable.
- 🗃️ **Multi vector store**: bundled adapters for Chroma (persistent) and FAISS (high-speed), with metadata filtering.
- ⚙️ **Config-driven**: scenes, prompt templates, and field labels are defined in YAML — extend without touching code.
- 🌐 **Internationalization**: built-in Chinese and English, configurable field labels.
- 💬 **Streaming output**: streaming Q&A for faster first-token and better UX.

---

## 🚀 Chatbot Demo (`chatbot-demo` branch)

This repository also provides a **ready-to-use RAG Chatbot service template** on the `chatbot-demo` branch. Built on the FastMe RAG framework with **Vue 3 + FastAPI + Docker Compose**, it fully demonstrates the framework's core capabilities and is ready for validation and secondary development.

<img width="1907" height="861" alt="image" src="https://github.com/user-attachments/assets/47d53a28-869e-49fb-a69a-2781b6bd6c9f" />

<img width="1891" height="880" alt="image" src="https://github.com/user-attachments/assets/f4c1e929-820f-4148-bae5-8567164e91b2" />

| Feature | Description |
|---------|-------------|
| 💬 Streaming chat | SSE typewriter effect, first token appears immediately |
| 📄 Document upload | Drag-and-drop PDF/DOCX/TXT/LOG/MD, choose type and ingest |
| 🧵 Multi-session memory | Create / switch / delete sessions based on framework `session_id` |
| 🎯 Scene selection | fault_diagnosis / manual_query / work_order_trace / default |
| 🔍 Source tracing | Answers with source snippets and similarity scores |

```bash
git checkout chatbot-demo          # switch to demo branch
cp backend/.env.example .env       # configure your LLM endpoint
docker compose up --build          # one-click start
# Frontend http://localhost:8080 | API docs http://localhost:8000/docs
```

The demo **does not modify framework source at all**: `backend/app/core/rag.py` wraps `FastMeRAG` as an HTTP service via a `RAGManager` singleton with thread-lock serialization.

---

## 🧭 Architecture

```
                    ┌──────────────────────────────────────┐
user question ────▶ │              FastMeRAG               │  factory entry
                    │  ┌──────────────┐  ┌───────────────┐ │
                    │  │ IngestPipeline│  │  ChatPipeline │ │  ingest / chat pipelines
                    │  └──────┬───────┘  └──────┬────────┘ │
                    │         └────────┬────────┘          │
                    │          SceneAwareRetriever         │  scene-aware retrieval
                    │                   │                  │
                    │          VectorStoreFactory          │
                    │             │      │                 │
                    │     ChromaAdapter  FAISSAdapter      │  vector stores
                    └──────────────────────────────────────┘
```

Core modules:

| Component | File | Responsibility |
|-----------|------|----------------|
| `FastMeRAG` | `app_factory.py` | Factory entry: loads config and assembles all components |
| `IngestPipeline` | `core/ingest_pipeline.py` | Ingest pipeline: load → split → embed → store |
| `ChatPipeline` | `core/chat_pipeline.py` | Chat pipeline: scene routing → retrieval → prompt → LLM → sources |
| `SceneAwareRetriever` | `retrievers/scene_aware.py` | Scene-aware retriever binding scene config to vector store |
| `IndustrialMetadataExtractor` | `manufacturing/metadata_extractor.py` | Industrial metadata extractor |

---

## 📦 Installation

```bash
pip install git+https://github.com/happy-momo/FastMe-RAG-Frame.git
```

Or install locally in editable mode (includes dev dependencies):

```bash
git clone https://github.com/happy-momo/FastMe-RAG-Frame.git
cd FastMe-RAG-Frame
pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### 1. Configure

Copy the environment template and edit it:

```bash
cp .env.example .env
```

Core configuration:

```bash
# LLM (OpenAI-compatible endpoint)
FASTME_LLM_BASE_URL=http://localhost:8000/v1
FASTME_LLM_API_KEY=your-api-key
FASTME_LLM_MODEL=qwen-plus

# Embedding model (local path or HuggingFace model name)
FASTME_EMBEDDING_MODEL=BAAI/bge-m3

# Vector store: chroma | faiss
FASTME_VECTOR_STORE_TYPE=chroma
```

### 2. Use

```python
from app_factory import FastMeRAG

rag = FastMeRAG()  # reads .env automatically
rag.ingest("equipment_manual.pdf", doc_type="manual")      # ingest
result = rag.chat("How do I handle an equipment alarm?", scene="fault_diagnosis")
print(result["answer"])
```

---

## 📖 Framework Usage Guide

### Ingest documents `ingest()`

```python
result = rag.ingest(
    file_path: str,              # required; PDF/DOCX/TXT/LOG/MD
    doc_type: str,               # required; log/manual/business/sop
    extra_metadata: dict = None, # extra metadata injected into all chunks
    require_review: bool = False # if True, preview chunks without storing
)
# result = {"status": "success", "doc_id": ..., "chunks_count": N}
```

Batch-ingest an entire folder:

```python
results = rag.batch_ingest(
    folder_path="./logs",
    doc_type="log",
    extra_metadata={"project": "Line A"},     # shared metadata for all files
    file_extensions=[".log"]                   # extension filter
)
# [{"status": "success", ...}, {"status": "error", "file": "...", "error": "..."}]
```

### Scene-aware Q&A `chat()`

```python
result = rag.chat(
    question="What faults does device E001 have?",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"},   # filter conditions, retrieve only this device
    top_k=5                           # retrieval count; defaults to scene config
)
# result = {"answer": str, "sources": [{"score": 0.95, "preview": "...", ...}], "scene": str}
```

`filters` supports single and multiple conditions (AND); FAISS implements the same filtering as "retrieve + post-filter", retrieving `top_k × post_filter_multiplier` results first.

### Streaming Q&A `chat_stream()`

```python
for chunk in rag.chat_stream("How do I handle an alarm?", scene="fault_diagnosis"):
    print(chunk, end="", flush=True)
```

### Conversation memory

```python
rag.create_memory("user_001", max_turns=10)          # create session memory
result = rag.chat_with_memory("What fault does E001 have?", session_id="user_001", scene="fault_diagnosis")
memory = rag.get_memory("user_001")                  # view history
rag.clear_memory("user_001")                         # clear a session
```

### Configuration loading

```python
# Load from a YAML config file
rag = FastMeRAG.from_config("./config/fastme_chroma.yaml")

# Load from config dict, or override partial values
rag = FastMeRAG.from_config(
    "./config/fastme_chroma.yaml",
    overrides={"vector_store": {"config": {"collection_name": "new_coll"}}}
)
```

Configuration priority: **config file > environment variable > code default**.

---

## 📚 Supported Document Types

| Document type | `doc_type` | Splitter | Typical use |
|---------------|------------|----------|-------------|
| Operation log | `"log"` | `LogSplitter` | Equipment fault logs, system logs |
| Equipment manual | `"manual"` | `ManualSplitter` | Operator manual, repair manual, spec sheet |
| Work order | `"business"` | `BusinessSplitter` | QC forms, production records, work orders |
| Process SOP | `"sop"` | `SopSplitter` | Work instructions, BOM docs, process flow |

---

## 🎯 Built-in Scenes

| Scene | `scene` | Description | Document type |
|-------|---------|-------------|---------------|
| Fault diagnosis | `"fault_diagnosis"` | Diagnose based on operation logs | log |
| Manual query | `"manual_query"` | Query equipment manuals / tech docs | manual |
| Work order trace | `"work_order_trace"` | Trace work orders / production records | business |
| Default Q&A | `"default"` | General Q&A | all |

Scenes are configured in `config/scenes.yaml` and support both single and multiple document types (`doc_type` lists auto-convert to the `$in` operator).

---

## 🚢 Deployment

### Option 1: Integrate as a Python library (recommended)

Install and call it from your own service:

```python
# in your service code
from app_factory import FastMeRAG

app_state = {"rag": None}

def get_rag():
    if app_state["rag"] is None:
        app_state["rag"] = FastMeRAG(config={...})   # or .env / YAML
    return app_state["rag"]
```

Suitable as the RAG engine behind FastAPI / Flask / Django services.

### Option 2: Docker one-click Chatbot (`chatbot-demo` branch)

```bash
git checkout chatbot-demo
cp backend/.env.example .env        # configure LLM endpoint & embedding strategy
docker compose up --build           # one-click start
# Frontend http://localhost:8080 | Backend http://localhost:8000/docs
```

| Config | Description |
|--------|-------------|
| `FASTME_LLM_BASE_URL` | OpenAI-compatible endpoint; use `host.docker.internal` to reach the host from a container |
| `FASTME_LLM_API_KEY` | must be non-empty; fill `not-needed` for auth-free services |
| `FASTME_LLM_MODEL` | model name, e.g. `qwen-plus` / `llama3.2` |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` (auto-download) or local path `/app/models/bge-m3` |

> After changing the embedding model, run `docker compose down -v` to clear volumes and rebuild.

---

## 🔧 Secondary Development

### Add a scene (dynamic API)

No framework changes needed — add it at runtime:

```python
rag.add_scene(
    name="custom_scene",
    doc_type="log",
    prompt_template="fault_diagnosis",   # reuse an existing prompt template
    top_k=10,
    description="custom scene"
)
# then use it
result = rag.chat("...", scene="custom_scene")
```

### Add a scene (YAML config)

Append to `config/scenes.yaml`:

```yaml
scenes:
  comprehensive_search:
    doc_type:            # multiple doc types: match multiple knowledge bases
      - log
      - manual
    prompt_template: comprehensive
    top_k: 10
    description: "comprehensive search - logs + manuals"
```

### Add a custom metadata extraction rule

```python
rag.add_metadata_rule(
    field="device_model",
    patterns=[r"model[:\s]*([A-Z0-9\-]+)"],
    description="extract device model"
)
```

### Add a custom Splitter

Extend `BaseSplitter` and register it:

```python
from splitters.base import BaseSplitter, SplitterRegistry

class MySplitter(BaseSplitter):
    def __init__(self, max_chunk_size: int = 1000):
        super().__init__(max_chunk_size)
    def split(self, document):
        # implement your splitting logic, return chunk list
        return [...]
```

> For the full guide see [DEVELOPER_GUIDE_EN.md](docs/DEVELOPER_GUIDE_EN.md).

---

## 📁 Project Structure

```
FastMe-RAG-Frame/
├── app_factory.py          # Main framework entry (FastMeRAG class)
├── core/                   # Data models, ingest/chat pipelines
├── vector_stores/          # Vector stores (Chroma / FAISS)
├── retrievers/             # Scene-aware retriever
├── splitters/              # Document splitters
├── manufacturing/          # Industrial metadata extraction
├── routers/                # Scene router
├── adapters/               # Prompt adapter, document loader
├── config/                 # YAML configs (scenes, prompts, field labels)
├── examples/               # Usage examples
└── tests/                  # Unit tests
```

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v                # run all tests
python -m pytest tests/test_splitters.py  # specific module
```

---

## 🤝 Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [developer guide](docs/DEVELOPER_GUIDE_EN.md).

---

## 📄 License

[MIT](LICENSE) © gail peng
