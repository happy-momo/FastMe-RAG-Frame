# FastMe RAG Developer Guide

This document is intended for developers who need to extend the framework's functionality, introducing how to add new scenes, splitters, and vector stores.

---

## Table of Contents

- [Adding New Scene](#adding-new-scene)
- [Adding New Splitter](#adding-new-splitter)
- [Adding New Vector Store](#adding-new-vector-store)
- [Best Practices](#best-practices)

---

## Adding New Scene

Scene is a core concept in the FastMe RAG framework, used to route user questions to specific knowledge bases and Prompt templates. The framework provides two ways to add new scenes.

### Method 1: Add via Configuration File (Recommended)

**Configuration File Location**: `config/scenes.yaml`

**Configuration Structure**:

```yaml
scenes:
  <scene_name>:
    doc_type: <document_type>      # Supports 3 formats (see below)
    prompt_template: <template_name> # Reference template in prompt_templates.yaml
    top_k: <retrieval_count>        # Number of documents to retrieve
    source_fields:                  # Source tracing fields
      - chunk_id
      - doc_id
      - <other_metadata_fields>
    description: <scene_description>
```

**`doc_type` Field Supports Three Formats (🆕 New Feature):**

| Format | Example | Description |
|--------|---------|-------------|
| **Single String** | `doc_type: log` | Match single document type (backward compatible) |
| **List Format** | `doc_type: ["log", "manual"]` | Match multiple document types, auto-converts to `$in` operator |
| **Null Value** | `doc_type: null` | No document type restriction |

**Examples:**

```yaml
scenes:
  # Single document type scene (backward compatible)
  fault_diagnosis:
    doc_type: log
    prompt_template: fault_diagnosis
    top_k: 5

  # Multi-document type scene (new feature)
  comprehensive_search:
    doc_type:
      - log
      - manual
      - business
    prompt_template: comprehensive
    top_k: 10

  # No document type restriction
  general_query:
    doc_type: null
    prompt_template: default
    top_k: 5
```

**Complete Example: Adding "Quality Check" Scene**

1. Edit `config/scenes.yaml` to add new scene configuration:

```yaml
scenes:
  # ... existing scene configuration ...

  # New: Quality check scene
  quality_check:
    doc_type: business              # Corresponding to work order document type
    prompt_template: quality_check  # Prompt template name
    top_k: 5                        # Retrieve 5 related records
    source_fields:                  # Source tracing fields
      - chunk_id
      - doc_id
      - doc_type
      - work_order_id
      - material_id
      - station
      - quality_result
      - timestamp
    description: "Quality record query - Trace work order quality results"
```

2. Add corresponding Prompt template in `config/prompt_templates.yaml`:

```yaml
quality_check:
  system: |
    You are a professional quality inspection assistant. Please answer user questions based on retrieved quality inspection records.

    Requirements:
    1. Accurately cite key information such as work order numbers and quality results
    2. If there are non-conforming items, explain specific issues and handling recommendations
    3. Keep answers concise and professional, highlighting key data
```

**Using New Scene**:

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("quality_records.xlsx", doc_type="business")

# Use new scene for Q&A
result = rag.chat(
    question="What is the quality result for work order WO001?",
    scene="quality_check"
)
print(result["answer"])
```

### Method 2: Add Dynamically via Code

Use the `add_scene()` method to dynamically add scenes at runtime without modifying configuration files.

**Method Signature**:

```python
rag.add_scene(
    name: str,              # Scene name (unique identifier)
    doc_type: str,          # Corresponding document type
    prompt_template: str,   # Prompt template name
    top_k: int = 5,         # Retrieval count
    source_fields: list = None,  # Source tracing field list
    description: str = ""   # Scene description
)
```

**Complete Example**:

```python
from app_factory import FastMeRAG

# Initialize framework
rag = FastMeRAG()

# Dynamically add "Device Maintenance" scene
rag.add_scene(
    name="device_maintenance",
    doc_type="manual",          # Corresponding to device manual
    prompt_template="default",  # Use default template
    top_k=8,                    # Retrieve 8 records
    source_fields=[
        "chunk_id",
        "doc_id",
        "chapter_num",
        "chapter_title",
        "device_model"
    ],
    description="Device maintenance guide query"
)

# Ingest document
rag.ingest("device_maintenance_manual.pdf", doc_type="manual")

# Use dynamically added scene
result = rag.chat(
    question="What are the daily maintenance steps for EQ-1000 device?",
    scene="device_maintenance"
)
print(result["answer"])
```

**Notes**:

- Dynamically added scenes will not persist after framework restart; use configuration file method for persistence
- `source_fields` defaults to `["chunk_id", "doc_id", "doc_type", "source"]`
- Scene names cannot duplicate existing scene names

---

## Adding New Splitter

Splitter is responsible for splitting documents into semantically complete chunks based on their structural characteristics. Adding a new Splitter requires inheriting `BaseSplitter` and implementing the `split()` method.

### Step Description

| Step | File Location | Description |
|------|---------------|-------------|
| 1. Create new Splitter class | `splitters/<name>_splitter.py` | Inherit `BaseSplitter`, implement `split()` method |
| 2. Register to SplitterRegistry | `app_factory.py` | Register new Splitter during initialization |
| 3. Update exports | `splitters/__init__.py` | Export new class (optional) |

### Base Class Structure

`BaseSplitter` is defined in `splitters/base.py`, key structure:

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
            List of FastMeChunk, each chunk contains unique ID, text, and metadata
        """
        pass
```

**Available Helper Methods (inherited from BaseSplitter)**:

| Method | Purpose |
|--------|---------|
| `_split_by_paragraphs(lines, max_size)` | Split by paragraphs, control size |
| `_split_large_text(content, max_size)` | Large text splitting helper |
| `_generate_chunk_id(doc_id, chunk_index, ...)` | Generate chunk ID |
| `_build_chunk_metadata(document, ...)` | Build standard metadata dictionary |
| `_extract_with_patterns(text, patterns, findall)` | Regex extraction helper |

### Complete Example: Adding "Technical Specification" Splitter

Assume need to process technical specification documents, split by "specification item" structure.

**Step 1: Create New Splitter Class**

Create file `splitters/spec_splitter.py`:

```python
"""
Technical Specification Splitter - SpecSplitter

Split technical specification documents by specification items, each item contains:
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
            List of FastMeChunk, each chunk corresponds to one specification item
        """
        chunks = []
        text = document.text
        doc_id = document.doc_id
        
        # 1. Split by specification item pattern (assume format: "spec_name: spec_value")
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

Modify `app_factory.py` to register new Splitter during initialization:

```python
# Import new class at top of app_factory.py
from splitters.spec_splitter import SpecSplitter

# In FastMeRAG.__init__ method, find Splitter registration section
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

If need to add corresponding scene for new document type, edit `config/scenes.yaml`:

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

**Using New Splitter**:

```python
from app_factory import FastMeRAG

rag = FastMeRAG()

# Use new spec document type for ingestion
result = rag.ingest("product_spec.xlsx", doc_type="spec")
print(f"Ingestion successful: {result['chunks_count']} specification items")

# Query specification
result = rag.chat("What is the input voltage?", scene="spec_query")
print(result["answer"])
```

---

## Adding New Vector Store

FastMe RAG supports multiple vector databases, implementing pluggability through adapter pattern. Adding a new vector store requires:

1. Implement `VectorStoreAdapter` interface
2. Create adapter class
3. Update `VectorStoreFactory`
4. Create corresponding Retriever

### Step Description

| Step | File Location | Description |
|------|---------------|-------------|
| 1. Create adapter class | `vector_stores/<name>.py` | Inherit `VectorStoreAdapter`, implement all abstract methods |
| 2. Create retriever class | `vector_stores/<name>_retriever.py` | Inherit `BaseRetriever`, implement `retrieve()` method |
| 3. Update VectorStoreFactory | `vector_stores/factory.py` | Add creation logic for new vector store type |
| 4. Update RetrieverFactory | `retrievers/factory.py` | Add creation logic for new retriever |

### Interface Definition

**VectorStoreAdapter Abstract Base Class** (`vector_stores/base.py`):

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from langchain_core.documents import Document

class VectorStoreAdapter(ABC):
    """Vector Store Adapter Abstract Base Class"""
    
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
        """Similarity search, return list of (Document, score) tuples"""
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
        pass
```

**BaseRetriever Abstract Base Class** (`core/retriever.py`):

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from core.models import FastMeSearchResult
from core.retriever import FilterCondition

class BaseRetriever(ABC):
    """Retriever Abstract Base Class"""
    
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

### Complete Example: Adding Milvus Vector Store

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
        self.collection_name = collection_name
        self.connection_args = connection_args
        self.embedding_function = embedding_function
        
        # Lazy import
        from langchain_milvus import Milvus
        
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
        sanitized_docs = []
        for doc in documents:
            clean_metadata = self.sanitize_metadata(doc.metadata)
            sanitized_docs.append(Document(
                page_content=doc.page_content,
                metadata=clean_metadata
            ))
        self._milvus.add_documents(sanitized_docs)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        results = self._milvus.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter
        )
        return results
    
    def get_count(self) -> int:
        from pymilvus import connections, Collection
        connections.connect(
            alias="default",
            host=self.connection_args.get("host", "localhost"),
            port=self.connection_args.get("port", "19530")
        )
        collection = Collection(self.collection_name)
        return collection.num_entities
    
    def delete_collection(self) -> None:
        from pymilvus import connections, utility
        connections.connect(
            alias="default",
            host=self.connection_args.get("host", "localhost"),
            port=self.connection_args.get("port", "19530")
        )
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
    
    def get_config(self) -> Dict[str, Any]:
        return {
            "collection_name": self.collection_name,
            "connection_args": self.connection_args,
            "vector_count": self.get_count(),
            "supports_filter": True
        }
    
    def supports_filter(self) -> bool:
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
from core.models import FastMeSearchResult
from core.retriever import BaseRetriever, FilterCondition
from vector_stores.milvus import MilvusAdapter


class MilvusRetriever(BaseRetriever):
    """Milvus Retriever"""
    
    def __init__(self, adapter: MilvusAdapter):
        self.adapter = adapter
    
    def retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[List[FilterCondition]] = None
    ) -> List[FastMeSearchResult]:
        milvus_filter = None
        if filters:
            milvus_filter = self._to_milvus_filter(filters)
        
        results = self.adapter.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=milvus_filter
        )
        
        return self._to_fastme_results(results)
    
    def _to_milvus_filter(
        self,
        conditions: List[FilterCondition]
    ) -> Optional[str]:
        if not conditions:
            return None
        
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
            
            if isinstance(value, str):
                expr_parts.append(f'{field} {op} "{value}"')
            elif isinstance(value, list):
                value_str = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                expr_parts.append(f'{field} {op} [{value_str}]')
            else:
                expr_parts.append(f'{field} {op} {value}')
        
        return " and ".join(expr_parts)
    
    def supports_filter(self) -> bool:
        return True
```

**Step 3: Update VectorStoreFactory**

Modify `vector_stores/factory.py`:

```python
from vector_stores.milvus import MilvusAdapter

class VectorStoreFactory:
    @staticmethod
    def create(
        vector_store_type: str,
        embeddings: Embeddings,
        vector_store_config: Dict[str, Any]
    ) -> VectorStoreAdapter:
        if vector_store_type == "chroma":
            return ChromaAdapter(...)
        elif vector_store_type == "faiss":
            return FAISSAdapter(...)
        elif vector_store_type == "milvus":
            return MilvusAdapter(
                collection_name=vector_store_config.get("collection_name", "fastme_rag"),
                connection_args=vector_store_config.get("connection_args", {"host": "localhost", "port": "19530"}),
                embedding_function=embeddings
            )
        else:
            raise ValueError(f"Unsupported vector store type: {vector_store_type}")
```

**Using New Vector Store**:

```python
from app_factory import FastMeRAG

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

rag.ingest("device_manual.pdf", doc_type="manual")
result = rag.chat("Device operation steps", scene="manual_query")
print(result["answer"])
```

---

## Best Practices

### 1. Metadata Processing

Different vector stores have different support for metadata types, it's recommended to call `sanitize_metadata()` in `add_documents()` for cleaning.

### 2. Filter Condition Conversion

Each vector store has different filter syntax, need to implement conversion logic in Retriever.

### 3. Lazy Import

Use `try/except` or lazy import to handle cases where dependencies are not installed.

### 4. Connection Management

Distributed vector stores need to manage connection pools, recommended to handle within adapter.

### 5. Error Handling

Encapsulate vector store-specific exceptions to provide friendly error messages.

---

## Related Documentation

- [Architecture Design](ARCHITECTURE_EN.md) - Detailed architecture design and module decoupling description
- [API Reference](API_REFERENCE_EN.md) - Detailed description of all public APIs
- [Quick Start](QUICKSTART_EN.md) - Simplified quick start tutorial
