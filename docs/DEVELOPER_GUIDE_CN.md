# FastMe RAG 开发者指南

本文档面向需要扩展框架功能的开发者，介绍如何添加新的场景、拆解器和向量库。

---

## 目录

- [添加新场景](#添加新场景)
- [添加新 Splitter](#添加新-splitter)
- [添加新向量库](#添加新向量库)
- [最佳实践](#最佳实践)

---

## 添加新场景

场景（Scene）是 FastMe RAG 框架的核心概念，用于将用户问题路由到特定的知识库和 Prompt 模板。框架提供了两种添加新场景的方式。

### 方式一：通过配置文件添加（推荐）

**配置文件位置**: `config/scenes.yaml`

**配置结构**:

```yaml
scenes:
  <场景名称>:
    doc_type: <文档类型>          # 支持 3 种格式（见下方说明）
    prompt_template: <模板名称>    # 引用 prompt_templates.yaml 中的模板
    top_k: <召回数量>              # 检索时返回的文档数量
    source_fields:                 # 溯源字段列表
      - chunk_id
      - doc_id
      - <其他元数据字段>
    description: <场景描述>
```

**`doc_type` 字段支持三种格式（🆕 新增功能）：**

| 格式 | 示例 | 说明 |
|------|------|------|
| **单值字符串** | `doc_type: log` | 匹配单个文档类型（向后兼容） |
| **列表格式** | `doc_type: ["log", "manual"]` | 匹配多个文档类型，自动转换为 `$in` 操作符 |
| **null 值** | `doc_type: null` | 不限制文档类型 |

**示例：**

```yaml
scenes:
  # 单文档类型场景（向后兼容）
  fault_diagnosis:
    doc_type: log
    prompt_template: fault_diagnosis
    top_k: 5

  # 多文档类型场景（新功能）
  comprehensive_search:
    doc_type:
      - log
      - manual
      - business
    prompt_template: comprehensive
    top_k: 10

  # 不限制文档类型
  general_query:
    doc_type: null
    prompt_template: default
    top_k: 5
```

**完整示例：添加"质检查询"场景**

1. 编辑 `config/scenes.yaml`，添加新场景配置：

```yaml
scenes:
  # ... 已有场景配置 ...

  # 新增：质检查询场景
  quality_check:
    doc_type: business              # 对应工单文档类型
    prompt_template: quality_check  # Prompt 模板名称
    top_k: 5                        # 召回 5 条相关记录
    source_fields:                  # 溯源字段
      - chunk_id
      - doc_id
      - doc_type
      - work_order_id
      - material_id
      - station
      - quality_result
      - timestamp
    description: "质检记录查询 - 追溯工单质检结果"
```

2. 在 `config/prompt_templates.yaml` 中添加对应的 Prompt 模板：

```yaml
quality_check:
  system: |
    你是一个专业的质量检测助手。请根据检索到的质检记录回答用户问题。

    回答要求：
    1. 准确引用工单号、质检结果等关键信息
    2. 如有不合格项，说明具体问题和处理建议
    3. 回答简洁专业，突出关键数据
```

**使用新场景**:

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("质检记录.xlsx", doc_type="business")

# 使用新场景进行问答
result = rag.chat(
    question="工单 WO001 的质检结果如何？",
    scene="quality_check"
)
print(result["answer"])
```

### 方式二：通过代码动态添加

使用 `add_scene()` 方法可以在运行时动态添加场景，无需修改配置文件。

**方法签名**:

```python
rag.add_scene(
    name: str,              # 场景名称（唯一标识）
    doc_type: str,          # 对应文档类型
    prompt_template: str,   # Prompt 模板名称
    top_k: int = 5,         # 召回数量
    source_fields: list = None,  # 溯源字段列表
    description: str = ""   # 场景描述
)
```

**完整示例**:

```python
from app_factory import FastMeRAG

# 初始化框架
rag = FastMeRAG()

# 动态添加"设备维护"场景
rag.add_scene(
    name="device_maintenance",
    doc_type="manual",          # 对应设备手册
    prompt_template="default",  # 使用默认模板
    top_k=8,                    # 召回 8 条记录
    source_fields=[
        "chunk_id",
        "doc_id",
        "chapter_num",
        "chapter_title",
        "device_model"
    ],
    description="设备维护指南查询"
)

# 入库文档
rag.ingest("设备维护手册.pdf", doc_type="manual")

# 使用动态添加的场景
result = rag.chat(
    question="EQ-1000 设备的日常维护步骤是什么？",
    scene="device_maintenance"
)
print(result["answer"])
```

**注意事项**:

- 动态添加的场景在框架重启后不会保留，如需持久化请使用配置文件方式
- `source_fields` 默认为 `["chunk_id", "doc_id", "doc_type", "source"]`
- 场景名称不能与已有场景重复

---

## 添加新 Splitter

Splitter（拆解器）负责将文档按其结构特点拆分成语义完整的切片。添加新 Splitter 需要继承 `BaseSplitter` 并实现 `split()` 方法。

### 步骤说明

| 步骤 | 文件位置 | 说明 |
|------|----------|------|
| 1. 创建新 Splitter 类 | `splitters/<name>_splitter.py` | 继承 `BaseSplitter`，实现 `split()` 方法 |
| 2. 注册到 SplitterRegistry | `app_factory.py` | 在初始化时注册新的 Splitter |
| 3. 更新导出 | `splitters/__init__.py` | 导出新类（可选） |

### 基类结构

`BaseSplitter` 定义在 `splitters/base.py`，关键结构如下：

```python
from abc import ABC, abstractmethod
from core.models import FastMeDocument, FastMeChunk

class BaseSplitter(ABC):
    def __init__(self, max_chunk_size: int = 1000):
        """初始化拆解器，设置最大切片大小"""
        self.max_chunk_size = max_chunk_size

    @abstractmethod
    def split(self, document: FastMeDocument) -> list[FastMeChunk]:
        """
        拆分文档为切片列表
        
        Args:
            document: FastMeDocument 实例，包含文档内容
        
        Returns:
            FastMeChunk 列表，每个切片包含唯一 ID、文本和元数据
        """
        pass
```

**可用的辅助方法（继承自 BaseSplitter）**:

| 方法 | 用途 |
|------|------|
| `_split_by_paragraphs(lines, max_size)` | 按段落切分，控制大小 |
| `_split_large_text(content, max_size)` | 大文本切分助手 |
| `_generate_chunk_id(doc_id, chunk_index, ...)` | 生成切片 ID |
| `_build_chunk_metadata(document, ...)` | 构建标准元数据字典 |
| `_extract_with_patterns(text, patterns, findall)` | 正则提取助手 |

### 完整示例：添加"技术规格书"拆解器

假设需要处理技术规格书文档，按"规格项"结构拆分。

**步骤 1：创建新 Splitter 类**

创建文件 `splitters/spec_splitter.py`：

```python
"""
技术规格书拆解器 - SpecSplitter

按规格项拆分技术规格书文档，每个规格项包含：
- 规格名称
- 规格值
- 单位
- 测试条件
"""
import re
from typing import List
from splitters.base import BaseSplitter
from core.models import FastMeDocument, FastMeChunk


class SpecSplitter(BaseSplitter):
    """技术规格书拆解器"""
    
    def __init__(self, max_chunk_size: int = 800):
        """
        初始化
        
        Args:
            max_chunk_size: 最大切片大小，默认 800 字符
                           规格书单个规格项通常较短，建议 600-1000
        """
        super().__init__(max_chunk_size)
    
    def split(self, document: FastMeDocument) -> List[FastMeChunk]:
        """
        按规格项拆分文档
        
        Args:
            document: FastMeDocument 实例
        
        Returns:
            FastMeChunk 列表，每个切片对应一个规格项
        """
        chunks = []
        text = document.text
        doc_id = document.doc_id
        
        # 1. 按规格项模式切分（假设格式："规格名称: 规格值"）
        spec_pattern = re.compile(
            r'^([^:\n]+):\s*([^\n]+)$',
            re.MULTILINE
        )
        
        # 2. 提取所有规格项
        matches = list(spec_pattern.finditer(text))
        
        if not matches:
            # 如果没有匹配到规格格式，按段落拆分
            return self._fallback_split(document)
        
        # 3. 为每个规格项创建切片
        for i, match in enumerate(matches):
            spec_name = match.group(1).strip()
            spec_value = match.group(2).strip()
            
            # 构建切片文本
            chunk_text = f"{spec_name}: {spec_value}"
            
            # 处理超长规格值
            if len(chunk_text) > self.max_chunk_size:
                chunk_text = chunk_text[:self.max_chunk_size]
            
            # 生成切片 ID
            chunk_id = self._generate_chunk_id(doc_id, i, len(matches))
            
            # 构建元数据
            metadata = {
                "spec_name": spec_name,        # 规格名称
                "spec_value": spec_value,      # 规格值
                "doc_type": "spec",            # 文档类型
                **document.metadata           # 继承文档级元数据
            }
            
            # 创建切片
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
        """后备拆分策略：按段落拆分"""
        lines = document.text.split('\n')
        return self._split_by_paragraphs(lines, self.max_chunk_size)
```

**步骤 2：注册到 SplitterRegistry**

修改 `app_factory.py`，在初始化方法中注册新的 Splitter：

```python
# 在 app_factory.py 顶部导入新类
from splitters.spec_splitter import SpecSplitter

# 在 FastMeRAG.__init__ 方法中，找到 Splitter 注册部分
def __init__(self, ...):
    # ... 其他初始化代码 ...
    
    # 注册拆解器
    self.splitter_registry = SplitterRegistry()
    self.splitter_registry.register("log", LogSplitter(max_chunk_size=self.chunk_max_size))
    self.splitter_registry.register("manual", ManualSplitter(max_chunk_size=self.chunk_max_size))
    self.splitter_registry.register("business", BusinessSplitter(max_chunk_size=self.chunk_max_size))
    self.splitter_registry.register("sop", SopSplitter(max_chunk_size=self.chunk_max_size))
    
    # 添加：注册新的规格书拆解器
    self.splitter_registry.register("spec", SpecSplitter(max_chunk_size=self.chunk_max_size))
```

**步骤 3：更新配置（可选）**

如果需要为新文档类型添加对应的场景，编辑 `config/scenes.yaml`：

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
    description: "技术规格查询"
```

**使用新 Splitter**:

```python
from app_factory import FastMeRAG

rag = FastMeRAG()

# 使用新的 spec 文档类型入库
result = rag.ingest("产品规格书.xlsx", doc_type="spec")
print(f"入库成功：{result['chunks_count']} 个规格项")

# 查询规格
result = rag.chat("输入电压是多少？", scene="spec_query")
print(result["answer"])
```

---

## 添加新向量库

FastMe RAG 支持多种向量数据库，通过适配器模式实现可插拔。添加新向量库需要：

1. 实现 `VectorStoreAdapter` 接口
2. 创建适配器类
3. 更新 `VectorStoreFactory`
4. 创建对应的 Retriever

### 步骤说明

| 步骤 | 文件位置 | 说明 |
|------|----------|------|
| 1. 创建适配器类 | `vector_stores/<name>.py` | 继承 `VectorStoreAdapter`，实现所有抽象方法 |
| 2. 创建检索器类 | `vector_stores/<name>_retriever.py` | 继承 `BaseRetriever`，实现 `retrieve()` 方法 |
| 3. 更新 VectorStoreFactory | `vector_stores/factory.py` | 添加新向量库类型的创建逻辑 |
| 4. 更新 RetrieverFactory | `retrievers/factory.py` | 添加新检索器的创建逻辑 |

### 接口定义

**VectorStoreAdapter 抽象基类**（`vector_stores/base.py`）：

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from langchain_core.documents import Document

class VectorStoreAdapter(ABC):
    """向量库适配器抽象基类"""
    
    @abstractmethod
    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> None:
        """添加文档到向量库"""
        pass
    
    @abstractmethod
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """相似度搜索，返回 (Document, score) 元组列表"""
        pass
    
    @abstractmethod
    def get_count(self) -> int:
        """返回向量库中的向量总数"""
        pass
    
    @abstractmethod
    def delete_collection(self) -> None:
        """删除整个集合"""
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """返回配置信息字典"""
        pass
    
    # 可选方法（有默认实现）
    def persist(self) -> None:
        """持久化数据"""
        pass
    
    def supports_filter(self) -> bool:
        """是否支持原生元数据过滤"""
        return True
    
    def sanitize_metadata(self, metadata: Dict) -> Dict:
        """清理元数据，只保留基本类型"""
        pass
```

**BaseRetriever 抽象基类**（`core/retriever.py`）：

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from core.models import FastMeSearchResult
from core.retriever import FilterCondition

class BaseRetriever(ABC):
    """检索器抽象基类"""
    
    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[List[FilterCondition]] = None
    ) -> List[FastMeSearchResult]:
        """执行检索"""
        pass
    
    @abstractmethod
    def supports_filter(self) -> bool:
        """是否支持过滤"""
        pass
```

### 完整示例：添加 Milvus 向量库

**步骤 1：创建适配器类**

创建文件 `vector_stores/milvus.py`：

```python
"""
Milvus 向量库适配器

支持 Milvus 分布式向量数据库，适用于大规模生产环境。
"""
from typing import List, Optional, Dict, Any, Tuple
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from vector_stores.base import VectorStoreAdapter


class MilvusAdapter(VectorStoreAdapter):
    """Milvus 向量库适配器"""
    
    def __init__(
        self,
        collection_name: str,
        connection_args: Dict[str, Any],
        embedding_function: Embeddings
    ):
        self.collection_name = collection_name
        self.connection_args = connection_args
        self.embedding_function = embedding_function
        
        # 延迟导入
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

**步骤 2：创建检索器类**

创建文件 `vector_stores/milvus_retriever.py`：

```python
"""
Milvus 检索器

负责将过滤条件转换为 Milvus 查询表达式，并执行检索。
"""
from typing import List, Optional
from core.models import FastMeSearchResult
from core.retriever import BaseRetriever, FilterCondition
from vector_stores.milvus import MilvusAdapter


class MilvusRetriever(BaseRetriever):
    """Milvus 检索器"""
    
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

**步骤 3：更新 VectorStoreFactory**

修改 `vector_stores/factory.py`：

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

**使用新向量库**:

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

rag.ingest("设备手册.pdf", doc_type="manual")
result = rag.chat("设备操作步骤", scene="manual_query")
print(result["answer"])
```

---

## 最佳实践

### 1. 元数据处理

不同向量库对元数据类型支持不同，建议在 `add_documents()` 中调用 `sanitize_metadata()` 清理。

### 2. 过滤条件转换

每个向量库的过滤语法不同，需要在 Retriever 中实现转换逻辑。

### 3. 延迟导入

使用 `try/except` 或延迟导入处理依赖未安装的情况。

### 4. 连接管理

分布式向量库需要管理连接池，建议在适配器内部处理。

### 5. 错误处理

封装向量库特定异常，提供友好的错误信息。

---

## 相关文档

- [架构设计](ARCHITECTURE_CN.md) - 详细的架构设计和模块解耦说明
- [API 参考](API_REFERENCE_CN.md) - 所有公开 API 的详细说明
- [快速开始](QUICKSTART_CN.md) - 简化的快速入门教程
