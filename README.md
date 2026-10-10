# FastMe RAG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://img.shields.io/github/actions/workflow/status/happy-momo/FastMe-RAG-Frame/ci.yml?branch=frame-0.2)](https://github.com/happy-momo/FastMe-RAG-Frame/actions)

**FastMe RAG** 是一个面向制造业的轻量化、可插拔检索增强生成（RAG）框架，专为工厂设备手册、运维日志、车间工单、工艺 SOP 等制造业文档设计，提供场景化问答与工业元数据自动抽取能力。

> 📖 [English README](README_EN.md)｜📖 [详细文档](docs/README.md)｜📖 [示例说明](examples/README.md)

---

## ✨ 核心特性

- 🏭 **制造业专属拆解器**：内置日志、手册、工单、SOP 四种拆解器，按工业文档结构智能拆分。
- 🔍 **场景化问答**：内置故障诊断、手册查询、工单追溯等场景，自动路由到对应知识库。
- 🏷️ **工业元数据抽取**：自动提取设备 ID、产线号、故障码、工单号等工业字段，提升检索精度。
- 🔌 **可插拔架构**：基于 LangChain，Embedding、向量库、LLM 均由配置驱动，可按需替换。
- 🗃️ **多向量库支持**：内置 Chroma（持久化）与 FAISS（高速）适配器，支持元数据过滤。
- ⚙️ **配置化驱动**：场景、Prompt 模板、字段标签均通过 YAML 配置，无需修改代码即可扩展。
- 🌐 **多语言支持**：内置中英文，字段标签可配置。
- 💬 **流式输出**：支持流式问答，首字更快，交互体验更佳。

---

## 🧭 架构

```
                    ┌──────────────────────────────────────┐
用户问题 ──────────▶ │              FastMeRAG               │ 主框架入口
                    │  ┌──────────────┐  ┌───────────────┐ │
                    │  │ IngestPipeline│  │  ChatPipeline │ │ 入库 / 对话流水线
                    │  └──────┬───────┘  └──────┬────────┘ │
                    │         └────────┬────────┘          │
                    │          SceneAwareRetriever         │ 场景感知检索
                    │                   │                  │
                    │          VectorStoreFactory          │
                    │             │      │                 │
                    │     ChromaAdapter  FAISSAdapter      │  向量库
                    └──────────────────────────────────────┘
```

核心模块：

| 组件 | 文件 | 职责 |
|------|------|------|
| `FastMeRAG` | `app_factory.py` | 工厂入口，加载配置并组装全部组件 |
| `IngestPipeline` | `core/ingest_pipeline.py` | 文档入库流水线：加载 → 拆解 → 向量化 → 存储 |
| `ChatPipeline` | `core/chat_pipeline.py` | 对话流水线：场景路由 → 检索 → Prompt → LLM → 溯源 |
| `SceneAwareRetriever` | `retrievers/scene_aware.py` | 场景感知检索器，绑定场景配置与向量库 |
| `IndustrialMetadataExtractor` | `manufacturing/metadata_extractor.py` | 工业元数据抽取器 |

---

## 📦 安装

```bash
pip install git+https://github.com/happy-momo/FastMe-RAG-Frame.git
```

或本地可编辑安装（含开发依赖）：

```bash
git clone https://github.com/happy-momo/FastMe-RAG-Frame.git
cd FastMe-RAG-Frame
pip install -e ".[dev]"
```

---

## 🚀 快速开始

### 1. 配置

复制环境变量模板并编辑：

```bash
cp .env.example .env
```

核心配置项：

```bash
# LLM（OpenAI 兼容端点）
FASTME_LLM_BASE_URL=http://localhost:8000/v1
FASTME_LLM_API_KEY=your-api-key
FASTME_LLM_MODEL=qwen-plus

# Embedding 模型（支持本地路径或 HuggingFace 模型名）
FASTME_EMBEDDING_MODEL=BAAI/bge-m3

# 向量库：chroma | faiss
FASTME_VECTOR_STORE_TYPE=chroma
```

### 2. 使用

```python
from app_factory import FastMeRAG

rag = FastMeRAG()  # 自动读取 .env 配置

# 文档入库
rag.ingest("设备手册.pdf", doc_type="manual")

# 场景化问答
result = rag.chat("设备报警怎么处理？", scene="fault_diagnosis")
print(result["answer"])
```

---

## 📖 核心 API

### `ingest()` — 单文档入库

```python
result = rag.ingest(
    file_path: str,              # 文件路径（必填），支持 PDF/DOCX/TXT/LOG/MD
    doc_type: str,               # 文档类型（必填）：log/manual/business/sop
    extra_metadata: dict = None, # 额外元数据，注入到所有切片
    require_review: bool = False # True 时预览切片，不实际入库
)
```

### `batch_ingest()` — 批量入库

```python
results = rag.batch_ingest(
    folder_path: str,            # 文件夹路径（必填）
    doc_type: str,               # 文档类型（必填）
    file_extensions: list = None # 扩展名过滤
)
```

### `chat()` — 场景化问答

```python
result = rag.chat(
    question: str,                # 用户问题（必填）
    scene: str = "default",       # 场景：fault_diagnosis / manual_query / work_order_trace / default
    filters: dict = None,         # 过滤条件，如 {"device_id": "EQ001"}
    top_k: int = None             # 召回数量，默认取场景配置
)
# result = {"answer": str, "sources": [...], "scene": str}
```

### `chat_stream()` — 流式问答

```python
for chunk in rag.chat_stream("设备报警怎么处理？", scene="fault_diagnosis"):
    print(chunk, end="", flush=True)
```

### 对话记忆

```python
rag.create_memory("user_001", max_turns=10)
result = rag.chat_with_memory("E001 设备有什么故障？", session_id="user_001", scene="fault_diagnosis")
memory = rag.get_memory("user_001")
rag.clear_memory("user_001")
```

### 配置加载

```python
# 从 YAML 配置文件加载
rag = FastMeRAG.from_config("./config/fastme_chroma.yaml")

# 从配置字典加载，并覆盖部分值
rag = FastMeRAG.from_config(
    "./config/fastme_chroma.yaml",
    overrides={"vector_store": {"config": {"collection_name": "new_coll"}}}
)
```

---

## 📚 支持的文档类型

| 文档类型 | `doc_type` | 拆解器 | 适用场景 |
|----------|------------|--------|----------|
| 运维日志 | `"log"` | `LogSplitter` | 设备故障日志、系统运行日志 |
| 设备手册 | `"manual"` | `ManualSplitter` | 操作手册、维修手册、技术规格书 |
| 车间工单 | `"business"` | `BusinessSplitter` | 质检单、生产记录、工单 |
| 工艺 SOP | `"sop"` | `SopSplitter` | 作业指导书、BOM 文档、工艺流程 |

---

## 🎯 预置场景

| 场景 | `scene` | 说明 | 文档类型 |
|------|---------|------|----------|
| 故障诊断 | `"fault_diagnosis"` | 基于运维日志进行诊断 | log |
| 手册查询 | `"manual_query"` | 设备手册、技术文档查询 | manual |
| 工单追溯 | `"work_order_trace"` | 工单、生产记录追溯 | business |
| 默认问答 | `"default"` | 通用问答 | 全部 |

场景通过 `config/scenes.yaml` 配置，支持单文档类型与多文档类型。

---

## 📁 项目结构

```
FastMe-RAG-Frame/
├── app_factory.py          # 主框架入口（FastMeRAG 类）
├── core/                   # 数据模型、入库/对话流水线
├── vector_stores/          # 向量库（Chroma / FAISS）与索引
├── retrievers/             # 场景感知检索器
├── splitters/              # 文档拆解器
├── manufacturing/          # 工业元数据抽取
├── routers/                # 场景路由器
├── adapters/               # Prompt 适配、文档加载
├── config/                 # YAML 配置（场景、Prompt、字段标签）
├── examples/               # 使用示例
└── tests/                  # 单元测试
```

---

## 🧪 运行测试

```bash
python -m pytest tests/ -v
```

---

## 🤝 贡献

欢迎提交 issue 与 pull request。参见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [开发者指南](docs/DEVELOPER_GUIDE_CN.md)。

---

## 📄 许可证

[MIT](LICENSE) © gail peng
