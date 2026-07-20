# FastMe RAG Quick Start Guide

This guide helps you get started with the FastMe RAG framework in 5 minutes.

---

## Prerequisites

- Python 3.10+
- Dependencies installed: `pip install -r requirements.txt`
- Environment variables configured (see below)

---

## 1. Environment Configuration

### 1.1 Copy Environment Template

```bash
cp .env.example .env
```

### 1.2 Edit .env File

```bash
# LLM Configuration
LLM_BASE_URL=http://localhost:8000/v1/chat/completions
LLM_API_KEY=your-api-key
LLM_MODEL=qwen-plus

# Embedding Model
EMBEDDING_MODEL=BAAI/bge-m3
```

---

## 2. Basic Usage

### 2.1 Initialize Framework

```python
from app_factory import FastMeRAG

# Use default configuration
rag = FastMeRAG()
```

### 2.2 Document Ingestion

```python
# Single document ingestion
result = rag.ingest("equipment_manual.pdf", doc_type="manual")
print(f"Successfully ingested: {result['chunks_count']} chunks")

# Batch ingestion
results = rag.batch_ingest("./logs", doc_type="log")
```

### 2.3 Scene-aware Q&A

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

# Streaming output
for chunk in rag.chat_stream("What are the device operation steps?", scene="manual_query"):
    print(chunk, end="", flush=True)
```

---

## 3. Supported Document Types

| Document Type | doc_type | Description |
|---------------|----------|-------------|
| Operation Logs | "log" | Device fault logs, system running logs |
| Equipment Manuals | "manual" | Operation manuals, maintenance manuals |
| Work Orders | "business" | Quality inspection forms, production records |
| Process SOPs | "sop" | Work instructions, BOM documents |

---

## 4. Pre-configured Scenes

| Scene | scene | Description |
|-------|-------|-------------|
| Fault Diagnosis | "fault_diagnosis" | Fault diagnosis based on operation logs |
| Manual Query | "manual_query" | Equipment manual and technical document query |
| Work Order Trace | "work_order_trace" | Work order and production record tracing |
| Default Q&A | "default" | General Q&A scenario |

---

## 5. Complete Examples

### Example 1: Fault Diagnosis

```python
from app_factory import FastMeRAG

# Initialize
rag = FastMeRAG()

# Ingest fault logs
rag.ingest("fault_log.log", doc_type="log")

# Fault diagnosis Q&A
result = rag.chat(
    question="What faults does E001 device have recently?",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}
)

print(f"Answer: {result['answer']}")

# View source tracing
for source in result["sources"]:
    print(f"  - [{source['timestamp']}] {source['fault_code']}")
```

### Example 2: Manual Query

```python
from app_factory import FastMeRAG

# Initialize
rag = FastMeRAG()

# Ingest equipment manual
rag.ingest("equipment_manual.pdf", doc_type="manual")

# Manual query
result = rag.chat(
    question="What are the device startup steps?",
    scene="manual_query"
)

print(f"Answer: {result['answer']}")

# View source chapters
for source in result["sources"]:
    print(f"  - Chapter {source.get('chapter_num', '?')}")
```

### Example 3: Streaming Q&A

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("equipment_manual.pdf", doc_type="manual")

print("AI: ", end="", flush=True)
for chunk in rag.chat_stream(
    question="What is the device maintenance cycle?",
    scene="manual_query"
):
    print(chunk, end="", flush=True)
print()
```

### Example 4: Conversation with Memory

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("fault_log.log", doc_type="log")

# Create session
rag.create_memory(session_id="user_001", max_turns=10)

# First conversation round
result1 = rag.chat_with_memory(
    question="What faults does E001 device have?",
    session_id="user_001",
    scene="fault_diagnosis"
)
print(f"Answer 1: {result1['answer']}")

# Second conversation round (automatically carries context)
result2 = rag.chat_with_memory(
    question="How to handle this fault?",
    session_id="user_001",
    scene="fault_diagnosis"
)
print(f"Answer 2: {result2['answer']}")
```

---

## 6. Vector Store Configuration

### 6.1 Using Chroma (Default)

```python
rag = FastMeRAG(
    vector_store_type="chroma",
    vector_store_config={
        "persist_directory": "./data/chroma",
        "collection_name": "my_collection"
    }
)
```

### 6.2 Using FAISS

```python
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={
        "index_path": "./data/faiss_index"
    }
)
```

---

## 7. Advanced Configuration

### 7.1 Memory-Constrained Environment

```python
rag = FastMeRAG(
    chunk_max_size=800,        # Smaller chunk size
    ingest_batch_size=16,      # Smaller ingestion batch
    embedding_batch_size=16,   # Smaller embedding batch
)
```

### 7.2 High-Performance Configuration (GPU Environment)

```python
rag = FastMeRAG(
    chunk_max_size=1500,       # Larger chunk size
    ingest_batch_size=64,      # Larger ingestion batch
    embedding_batch_size=64,   # Larger embedding batch
    show_progress_bar=True,
)
```

---

## 8. Next Steps

- See [API Reference](API_REFERENCE_EN.md) for detailed API documentation
- See [Developer Guide](DEVELOPER_GUIDE_EN.md) to learn how to extend the framework
- See [Architecture Design](ARCHITECTURE_EN.md) to understand the system architecture

---

## Frequently Asked Questions

### Q1: How to switch language?

```python
rag = FastMeRAG(language="en")  # Use English interface
rag.set_language("zh")          # Switch to Chinese
```

### Q2: How to view vector store statistics?

```python
count = rag.get_vector_count()
scenes = rag.get_scenes()
doc_types = rag.get_doc_types()
```

### Q3: How to clear vector store?

```python
rag.delete_collection()  # Delete all data
```

---

## Related Documentation

- [Architecture Design](ARCHITECTURE_EN.md)
- [Developer Guide](DEVELOPER_GUIDE_EN.md)
- [API Reference](API_REFERENCE_EN.md)
