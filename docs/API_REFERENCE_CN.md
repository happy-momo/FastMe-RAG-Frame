# FastMe RAG API 参考文档

本文档提供 FastMe RAG 框架所有公开 API 的详细说明。

---

## 目录

- [FastMeRAG 类](#fasemerag-类)
  - [初始化方法](#初始化方法)
  - [文档入库方法](#文档入库方法)
  - [场景化问答方法](#场景化问答方法)
  - [配置管理方法](#配置管理方法)
  - [查询统计方法](#查询统计方法)
- [数据模型](#数据模型)
- [异常类](#异常类)

---

## FastMeRAG 类

主框架入口类，提供统一的 API 接口。

### 初始化方法

#### `FastMeRAG.__init__()`

初始化 FastMe RAG 框架。

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `embedding_model` | str | `"BAAI/bge-m3"` | HuggingFace Embedding 模型名称 |
| `model_cache_dir` | str | `"./models"` | 模型缓存目录，首次下载后可离线使用 |
| `llm_base_url` | str | `"http://localhost:8000/v1/chat/completions"` | LLM API 地址（兼容 OpenAI 格式） |
| `llm_api_key` | str | `"sk-1234567890abcdef..."` | LLM API Key |
| `llm_model` | str | `"qwen-plus"` | LLM 模型名称 |
| `temperature` | float | `0.2` | LLM 温度参数，值越小回答越确定 |
| `language` | str | `"zh"` | 界面语言，支持 `"zh"`（中文）和 `"en"`（英文） |
| `chunk_max_size` | int | `1000` | 单个 chunk 最大字符数 |
| `ingest_batch_size` | int | `32` | 入库分批大小 |
| `embedding_batch_size` | int | `32` | Embedding 批量大小 |
| `show_progress_bar` | bool | `False` | 是否显示进度条 |
| `vector_store_type` | str | `"chroma"` | 向量库类型，支持 `"chroma"` 或 `"faiss"` |
| `vector_store_config` | dict | `None` | 向量库特定配置 |
| `chroma_dir` | str | `"./data/chroma"` | Chroma 数据目录（向后兼容） |
| `chroma_collection` | str | `"fastme_rag"` | Chroma 集合名称（向后兼容） |

**示例**:

```python
from app_factory import FastMeRAG

# 默认配置
rag = FastMeRAG()

# 自定义配置
rag = FastMeRAG(
    embedding_model="BAAI/bge-m3",
    llm_base_url="http://localhost:8000/v1/chat/completions",
    llm_model="qwen-plus",
    chunk_max_size=1000,
    vector_store_type="chroma"
)

# 使用 FAISS 向量库
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={"index_path": "./data/faiss_index"}
)
```

---

### 文档入库方法

#### `ingest()`

执行单文档入库。

**方法签名**:

```python
def ingest(
    self,
    file_path: str,
    doc_type: str,
    extra_metadata: Optional[dict] = None,
    require_review: bool = False
) -> dict
```

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_path` | str | 是 | 文件路径，支持 PDF、DOCX、TXT、LOG、MD 格式 |
| `doc_type` | str | 是 | 文档类型：`"log"`、`"manual"`、`"business"`、`"sop"` |
| `extra_metadata` | dict | 否 | 额外元数据，会注入到所有切片中 |
| `require_review` | bool | 否 | 是否需要审核。`True` 时返回切片预览，不实际入库 |

**返回值**:

成功时返回：
```python
{
    "status": "success",
    "doc_id": "doc_20240115_abc123",     # 文档唯一 ID
    "file_name": "设备手册.pdf",          # 文件名
    "doc_type": "manual",                # 文档类型
    "chunks_count": 15,                  # 切片数量
    "vector_count": 115                  # 向量库总量
}
```

审核模式时返回：
```python
{
    "status": "waiting_review",
    "doc_id": "doc_20240115_abc123",
    "file_name": "设备手册.pdf",
    "doc_type": "manual",
    "chunks": [                          # 切片列表
        {
            "chunk_id": "doc_20240115_abc123_0",
            "text": "第一章 设备概述...",
            "metadata": {"chapter_num": "1", "chapter_title": "设备概述"}
        }
    ]
}
```

**示例**:

```python
# 基本入库
result = rag.ingest("设备手册.pdf", doc_type="manual")
print(f"入库成功：{result['chunks_count']} 个切片")

# 带额外元数据
result = rag.ingest(
    file_path="故障日志.log",
    doc_type="log",
    extra_metadata={"device_id": "EQ001", "line_id": "LN01"}
)

# 审核模式
result = rag.ingest("工单.xlsx", doc_type="business", require_review=True)
if result["status"] == "waiting_review":
    print(f"待审核：{len(result['chunks'])} 个切片")
```

---

#### `batch_ingest()`

执行批量文件夹入库。

**方法签名**:

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

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `folder_path` | str | - | 文件夹路径 |
| `doc_type` | str | - | 文档类型 |
| `extra_metadata` | dict | `None` | 所有文件共享的额外元数据 |
| `file_extensions` | list | `[".pdf", ".docx", ".txt", ".log", ".md"]` | 文件扩展名过滤 |
| `persist_interval` | int | `10` | 每处理 N 个文件后执行内存清理 |

**返回值**:

```python
[
    {"status": "success", "doc_id": "doc_001", "chunks_count": 10, ...},
    {"status": "success", "doc_id": "doc_002", "chunks_count": 15, ...},
    {"status": "error", "file": "failed.pdf", "error": "无法解析文件"}
]
```

**示例**:

```python
# 批量入库
results = rag.batch_ingest(
    folder_path="./logs",
    doc_type="log",
    extra_metadata={"project": "生产线A"}
)

# 统计结果
success = sum(1 for r in results if r["status"] == "success")
print(f"成功入库 {success} 个文件")
```

---

### 场景化问答方法

#### `chat()`

执行同步场景化问答。

**方法签名**:

```python
def chat(
    self,
    question: str,
    scene: str = "default",
    filters: Optional[dict] = None,
    top_k: Optional[int] = None
) -> dict
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `question` | str | - | 用户问题 |
| `scene` | str | `"default"` | 场景名称 |
| `filters` | dict | `None` | 过滤条件 |
| `top_k` | int | 场景配置 | 召回数量 |

**返回值**:

```python
{
    "question": "设备报警怎么处理？",      # 用户问题
    "scene": "fault_diagnosis",          # 场景名称
    "filters": {"device_id": "EQ001"},   # 过滤条件
    "answer": "根据日志记录，E001 设备...", # LLM 生成的回答
    "sources": [                         # 溯源信息
        {
            "chunk_id": "doc_001_0",
            "doc_id": "doc_001",
            "device_id": "EQ001",
            "fault_code": "E001",
            "score": 0.95,
            "preview": "设备报警记录..."
        }
    ]
}
```

**示例**:

```python
# 基本问答
result = rag.chat("设备报警怎么处理？", scene="fault_diagnosis")
print(result["answer"])

# 带过滤条件
result = rag.chat(
    question="E001 设备有哪些故障？",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}
)

# 查看溯源
for source in result["sources"]:
    print(f"  - [{source['score']:.2f}] {source['preview'][:50]}...")
```

---

#### `chat_stream()`

执行流式场景化问答。

**方法签名**:

```python
def chat_stream(
    self,
    question: str,
    scene: str = "default",
    filters: Optional[dict] = None,
    top_k: Optional[int] = None
) -> Generator[str, None, None]
```

**返回值**:

生成器，每次 `yield` 一个文本片段。

**示例**:

```python
print("AI: ", end="", flush=True)
for chunk in rag.chat_stream(
    question="设备操作步骤是什么？",
    scene="manual_query"
):
    print(chunk, end="", flush=True)
print()
```

---

#### `chat_with_memory()`

执行带记忆的对话。

**方法签名**:

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

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `question` | str | - | 用户问题 |
| `session_id` | str | - | 会话 ID |
| `scene` | str | `"default"` | 场景名称 |
| `filters` | dict | `None` | 过滤条件 |
| `top_k` | int | 场景配置 | 召回数量 |

**示例**:

```python
# 创建会话记忆
rag.create_memory(session_id="user_001", max_turns=10)

# 第一轮对话
result1 = rag.chat_with_memory(
    question="E001 设备有什么故障？",
    session_id="user_001",
    scene="fault_diagnosis"
)

# 第二轮对话（自动携带上下文）
result2 = rag.chat_with_memory(
    question="那怎么处理这个故障？",
    session_id="user_001",
    scene="fault_diagnosis"
)
```

---

### 记忆管理方法

#### `create_memory()`

创建会话记忆。

**方法签名**:

```python
def create_memory(
    self,
    session_id: str,
    max_turns: int = 10
) -> None
```

---

#### `get_memory()`

获取会话记忆。

**方法签名**:

```python
def get_memory(
    self,
    session_id: str
) -> Optional[ConversationBufferMemory]
```

---

#### `clear_memory()`

清除记忆。

**方法签名**:

```python
def clear_memory(
    self,
    session_id: Optional[str] = None
) -> None
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `session_id` | str | `None` | 会话 ID，`None` 则清除所有 |

---

### 配置管理方法

#### `add_scene()`

动态添加场景配置。

**方法签名**:

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

动态添加元数据抽取规则。

**方法签名**:

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

更新场景的 top_k 配置。

**方法签名**:

```python
def update_scene_top_k(
    self,
    scene: str,
    top_k: int
) -> None
```

---

#### `set_language()`

切换语言。

**方法签名**:

```python
def set_language(
    self,
    language: str
) -> None
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `language` | str | 语言代码，支持 `"zh"` 或 `"en"` |

---

### 查询统计方法

#### `get_scenes()`

获取所有可用场景。

**返回值**: `list[str]` - 场景名称列表

---

#### `get_doc_types()`

获取所有支持的文档类型。

**返回值**: `list[str]` - 文档类型列表

---

#### `get_vector_count()`

获取向量库中的向量总数。

**返回值**: `int` - 向量数量

---

#### `delete_collection()`

删除当前集合。

**警告**: 此操作不可逆，会删除所有数据。

---

## 数据模型

### FastMeDocument

文档级数据模型。

**属性**:

| 属性 | 类型 | 说明 |
|------|------|------|
| `doc_id` | str | 文档唯一标识符 |
| `doc_type` | str | 文档类型 (log/manual/business/sop) |
| `file_name` | str | 文件名 |
| `file_path` | str | 文件完整路径 |
| `text` | str | 文档完整文本内容 |
| `metadata` | dict | 文档元数据 |

---

### FastMeChunk

切片级数据模型。

**属性**:

| 属性 | 类型 | 说明 |
|------|------|------|
| `chunk_id` | str | 切片唯一标识符 |
| `doc_id` | str | 所属文档 ID |
| `doc_type` | str | 文档类型 |
| `text` | str | 切片文本内容 |
| `metadata` | dict | 切片元数据 |

---

### FastMeSearchResult

检索结果模型。

**属性**:

| 属性 | 类型 | 说明 |
|------|------|------|
| `chunk_id` | str | 切片 ID |
| `doc_id` | str | 文档 ID |
| `doc_type` | str | 文档类型 |
| `text` | str | 切片文本内容 |
| `score` | float | 相似度得分，范围 [0, 1] |
| `metadata` | dict | 切片元数据 |

---

## 异常类

### ValueError

当参数无效时抛出。

**常见场景**:
- `doc_type` 未注册拆解器
- `scene` 不存在
- `language` 不支持

---

### FileNotFoundError

当文件或文件夹不存在时抛出。

---

## 相关文档

- [架构设计](ARCHITECTURE_CN.md) - 详细的架构设计和模块解耦说明
- [开发者指南](DEVELOPER_GUIDE_CN.md) - 添加场景、Splitter、向量库的详细步骤
- [快速开始](QUICKSTART_CN.md) - 简化的快速入门教程
