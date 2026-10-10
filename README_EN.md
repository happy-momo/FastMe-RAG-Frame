# FastMe RAG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://img.shields.io/github/actions/workflow/status/happy-momo/FastMe-RAG-Frame/ci.yml?branch=frame-0.2)](https://github.com/happy-momo/FastMe-RAG-Frame/actions)

**FastMe RAG** is a lightweight, pluggable Retrieval-Augmented Generation (RAG) framework purpose-built for manufacturing. It is designed for factory equipment manuals, operation logs, workshop work orders, and process SOPs, providing scene-aware Q&A and automatic industrial metadata extraction.

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

# Ingest a document
rag.ingest("equipment_manual.pdf", doc_type="manual")

# Scene-aware Q&A
result = rag.chat("How do I handle an equipment alarm?", scene="fault_diagnosis")
print(result["answer"])
```

---

## 📖 Core API

### `ingest()` — ingest a single document

```python
result = rag.ingest(
    file_path: str,              # required; PDF/DOCX/TXT/LOG/MD
    doc_type: str,               # required; log/manual/business/sop
    extra_metadata: dict = None, # extra metadata injected into all chunks
    require_review: bool = False # if True, preview chunks without storing
)
```

### `batch_ingest()` — ingest a folder

```python
results = rag.batch_ingest(
    folder_path: str,            # required
    doc_type: str,               # required
    file_extensions: list = None # extension filter
)
```

### `chat()` — scene-aware Q&A

```python
result = rag.chat(
    question: str,                # required
    scene: str = "default",       # fault_diagnosis / manual_query / work_order_trace / default
    filters: dict = None,         # e.g. {"device_id": "EQ001"}
    top_k: int = None             # retrieval count; defaults to scene config
)
# result = {"answer": str, "sources": [...], "scene": str}
```

### `chat_stream()` — streaming Q&A

```python
for chunk in rag.chat_stream("How do I handle an alarm?", scene="fault_diagnosis"):
    print(chunk, end="", flush=True)
```

### Conversation memory

```python
rag.create_memory("user_001", max_turns=10)
result = rag.chat_with_memory("What fault does device E001 have?", session_id="user_001", scene="fault_diagnosis")
memory = rag.get_memory("user_001")
rag.clear_memory("user_001")
```

### Configuration loading

```python
# Load from a YAML config file
rag = FastMeRAG.from_config("./config/fastme_chroma.yaml")

# Load and override some values
rag = FastMeRAG.from_config(
    "./config/fastme_chroma.yaml",
    overrides={"vector_store": {"config": {"collection_name": "new_coll"}}}
)
```

---

## 📚 Supported Document Types

| Document type | `doc_type` | Splitter | Typical use |
|---------------|------------|----------|-------------|
| Operation log | `"log"` | `LogSplitter` | Equipment fault logs, system logs |
| Equipment manual | `"manual"` | `ManualSplitter` | Operator/manual, repair manual, spec sheet |
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

Scenes are configured in `config/scenes.yaml` and support both single and multiple document types.

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
python -m pytest tests/ -v
```

---

## 🤝 Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [developer guide](docs/DEVELOPER_GUIDE_EN.md).

---

## 📄 License

[MIT](LICENSE) © gail peng
