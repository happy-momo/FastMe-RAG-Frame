# FastMe RAG 快速开始指南

本指南帮助您在 5 分钟内快速上手 FastMe RAG 框架。

---

## 前置条件

- Python 3.10+
- 已安装依赖：`pip install -r requirements.txt`
- 已配置环境变量（见下文）

---

## 1. 环境配置

### 1.1 复制环境变量模板

```bash
cp .env.example .env
```

### 1.2 编辑 .env 文件

```bash
# LLM 配置
LLM_BASE_URL=http://localhost:8000/v1/chat/completions
LLM_API_KEY=your-api-key
LLM_MODEL=qwen-plus

# Embedding 模型
EMBEDDING_MODEL=BAAI/bge-m3
```

---

## 2. 基本使用

### 2.1 初始化框架

```python
from app_factory import FastMeRAG

# 使用默认配置
rag = FastMeRAG()
```

### 2.2 文档入库

```python
# 单文档入库
result = rag.ingest("设备手册.pdf", doc_type="manual")
print(f"入库成功：{result['chunks_count']} 个切片")

# 批量入库
results = rag.batch_ingest("./logs", doc_type="log")
```

### 2.3 场景化问答

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

# 流式输出
for chunk in rag.chat_stream("设备操作步骤是什么？", scene="manual_query"):
    print(chunk, end="", flush=True)
```

---

## 3. 支持的文档类型

| 文档类型 | doc_type | 说明 |
|----------|----------|------|
| 运维日志 | `"log"` | 设备故障日志、系统运行日志 |
| 设备手册 | `"manual"` | 操作手册、维修手册、技术规格书 |
| 车间工单 | `"business"` | 质检单、生产记录、工单 |
| 工艺 SOP | `"sop"` | 作业指导书、BOM 文档、工艺流程 |

---

## 4. 预置场景

| 场景 | scene | 说明 |
|------|-------|------|
| 故障诊断 | `"fault_diagnosis"` | 基于运维日志进行故障诊断 |
| 手册查询 | `"manual_query"` | 设备手册、技术文档查询 |
| 工单追溯 | `"work_order_trace"` | 工单、生产记录追溯 |
| 默认问答 | `"default"` | 通用问答场景 |

---

## 5. 完整示例

### 示例 1：故障诊断

```python
from app_factory import FastMeRAG

# 初始化
rag = FastMeRAG()

# 入库故障日志
rag.ingest("故障日志.log", doc_type="log")

# 故障诊断问答
result = rag.chat(
    question="E001 设备最近有什么故障？",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}
)

print(f"回答：{result['answer']}")

# 查看溯源
for source in result["sources"]:
    print(f"  - [{source['timestamp']}] {source['fault_code']}")
```

### 示例 2：手册查询

```python
from app_factory import FastMeRAG

# 初始化
rag = FastMeRAG()

# 入库设备手册
rag.ingest("设备手册.pdf", doc_type="manual")

# 手册查询
result = rag.chat(
    question="设备的启动步骤是什么？",
    scene="manual_query"
)

print(f"回答：{result['answer']}")

# 查看来源章节
for source in result["sources"]:
    print(f"  - 第 {source.get('chapter_num', '?')} 章")
```

### 示例 3：流式问答

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("设备手册.pdf", doc_type="manual")

print("AI: ", end="", flush=True)
for chunk in rag.chat_stream(
    question="设备的维护周期是多久？",
    scene="manual_query"
):
    print(chunk, end="", flush=True)
print()
```

### 示例 4：带记忆的对话

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("故障日志.log", doc_type="log")

# 创建会话
rag.create_memory(session_id="user_001", max_turns=10)

# 第一轮对话
result1 = rag.chat_with_memory(
    question="E001 设备有什么故障？",
    session_id="user_001",
    scene="fault_diagnosis"
)
print(f"回答 1：{result1['answer']}")

# 第二轮对话（自动携带上下文）
result2 = rag.chat_with_memory(
    question="那怎么处理这个故障？",
    session_id="user_001",
    scene="fault_diagnosis"
)
print(f"回答 2：{result2['answer']}")
```

---

## 6. 向量库配置

### 6.1 使用 Chroma（默认）

```python
rag = FastMeRAG(
    vector_store_type="chroma",
    vector_store_config={
        "persist_directory": "./data/chroma",
        "collection_name": "my_collection"
    }
)
```

### 6.2 使用 FAISS

```python
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={
        "index_path": "./data/faiss_index"
    }
)
```

---

## 7. 高级配置

### 7.1 内存受限环境

```python
rag = FastMeRAG(
    chunk_max_size=800,        # 减小 chunk 尺寸
    ingest_batch_size=16,      # 减小入库批次
    embedding_batch_size=16,   # 减小 embedding 批量
)
```

### 7.2 高性能配置（GPU 环境）

```python
rag = FastMeRAG(
    chunk_max_size=1500,       # 增大 chunk 尺寸
    ingest_batch_size=64,      # 增大入库批次
    embedding_batch_size=64,   # 增大 embedding 批量
    show_progress_bar=True,
)
```

---

## 8. 下一步

- 查看 [API 参考](API_REFERENCE_CN.md) 了解所有 API 详细说明
- 查看 [开发者指南](DEVELOPER_GUIDE_CN.md) 学习如何扩展框架
- 查看 [架构设计](ARCHITECTURE_CN.md) 了解系统架构

---

## 常见问题

### Q1: 如何切换语言？

```python
rag = FastMeRAG(language="en")  # 使用英文界面
rag.set_language("zh")           # 切换为中文
```

### Q2: 如何查看向量库统计信息？

```python
count = rag.get_vector_count()
scenes = rag.get_scenes()
doc_types = rag.get_doc_types()
```

### Q3: 如何清空向量库？

```python
rag.delete_collection()  # 删除所有数据
```

---

## 相关文档

- [架构设计](ARCHITECTURE_CN.md)
- [开发者指南](DEVELOPER_GUIDE_CN.md)
- [API 参考](API_REFERENCE_CN.md)
