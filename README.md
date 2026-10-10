# FastMe RAG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://img.shields.io/github/actions/workflow/status/happy-momo/FastMe-RAG-Frame/ci.yml?branch=frame-0.2)](https://github.com/happy-momo/FastMe-RAG-Frame/actions)

**FastMe RAG** 是一个面向制造业的轻量化、可插拔检索增强生成（RAG）框架，专为工厂设备手册、运维日志、车间工单、工艺 SOP 等制造业文档设计，提供场景化问答、工业元数据自动抽取与多向量库接入能力。

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

## 🚀 Chatbot 演示（`chatbot-demo` 分支）

本仓库同时提供一个**开箱即用的 RAG Chatbot 服务模板**，位于 `chatbot-demo` 分支。它基于 FastMe RAG 框架，使用 **Vue 3 + FastAPI + Docker Compose** 构建，完整演示框架核心能力，可直接用于验证和二次开发。

<img width="1907" height="861" alt="image" src="https://github.com/user-attachments/assets/47d53a28-869e-49fb-a69a-2781b6bd6c9f" />

<img width="1891" height="880" alt="image" src="https://github.com/user-attachments/assets/f4c1e929-820f-4148-bae5-8567164e91b2" />

| 功能 | 说明 |
|------|------|
| 💬 流式对话 | SSE 打字机效果，首字即出 |
| 📄 文档上传 | 拖拽上传 PDF/DOCX/TXT/LOG/MD，选择类型后入库 |
| 🧵 多会话记忆 | 新建 / 切换 / 删除会话，基于框架 `session_id` 记忆 |
| 🎯 场景选择 | fault_diagnosis / manual_query / work_order_trace / default |
| 🔍 溯源展示 | 回答附来源片段与相似度分数 |

```bash
git checkout chatbot-demo          # 切换到 demo 分支
cp backend/.env.example .env       # 配置你的 LLM 端点
docker compose up --build          # 一键启动
# 前端 http://localhost:8080 | 后端 API 文档 http://localhost:8000/docs
```

Demo **零改动框架源码**：`backend/app/core/rag.py` 通过 `RAGManager` 单例以线程锁串行调用 `FastMeRAG`，将其包装为 HTTP 服务。

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
rag.ingest("设备手册.pdf", doc_type="manual")      # 入库
result = rag.chat("设备报警怎么处理？", scene="fault_diagnosis")
print(result["answer"])
```

---

## 📖 框架使用详解

### 文档入库 `ingest()`

```python
result = rag.ingest(
    file_path: str,              # 必填；支持 PDF/DOCX/TXT/LOG/MD
    doc_type: str,               # 必填；log/manual/business/sop
    extra_metadata: dict = None, # 注入到所有切片的附加元数据
    require_review: bool = False # True 时仅预览切片，不实际入库
)
# result = {"status": "success", "doc_id": ..., "chunks_count": N}
```

批量入库一个文件夹：

```python
results = rag.batch_ingest(
    folder_path="./logs",
    doc_type="log",
    extra_metadata={"project": "生产线A"},     # 所有文件共享元数据
    file_extensions=[".log"]                   # 扩展名过滤
)
# [{"status": "success", ...}, {"status": "error", "file": "...", "error": "..."}]
```

### 场景化问答 `chat()`

```python
result = rag.chat(
    question="E001 设备有什么故障？",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"},   # 过滤条件，只检索该设备
    top_k=5                           # 召回数量，默认取场景配置
)
# result = {"answer": str, "sources": [{"score": 0.95, "preview": "...", ...}], "scene": str}
```

`filters` 支持单条件与多条件（AND 关系）；FAISS 通过「召回 + 后过滤」实现同等过滤，需先召回 `top_k × post_filter_multiplier` 个结果再过滤。

### 流式问答 `chat_stream()`

```python
for chunk in rag.chat_stream("设备报警怎么处理？", scene="fault_diagnosis"):
    print(chunk, end="", flush=True)
```

### 对话记忆

```python
rag.create_memory("user_001", max_turns=10)          # 创建会话记忆
result = rag.chat_with_memory("E001 有什么故障？", session_id="user_001", scene="fault_diagnosis")
memory = rag.get_memory("user_001")                  # 查看历史
rag.clear_memory("user_001")                         # 清除指定会话
```

### 配置加载

```python
# 从 YAML 配置文件加载
rag = FastMeRAG.from_config("./config/fastme_chroma.yaml")

# 从配置字典加载，或覆盖部分值
rag = FastMeRAG.from_config(
    "./config/fastme_chroma.yaml",
    overrides={"vector_store": {"config": {"collection_name": "new_coll"}}}
)
```

配置优先级：**配置文件 > 环境变量 > 代码默认值**。

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

场景通过 `config/scenes.yaml` 配置，支持单文档类型与多文档类型（`doc_type` 列表自动转换为 `$in` 操作符）。

---

## 🚢 部署方法

### 方式一：作为 Python 库集成（推荐）

在自有服务中安装并调用：

```python
# 你的服务代码中
from app_factory import FastMeRAG

app_state = {"rag": None}

def get_rag():
    if app_state["rag"] is None:
        app_state["rag"] = FastMeRAG(config={...})   # 或用 .env / YAML
    return app_state["rag"]
```

适合作为 FastAPI / Flask / Django 服务的 RAG 引擎直接集成。

### 方式二：Docker 一键部署 Chatbot（`chatbot-demo` 分支）

```bash
git checkout chatbot-demo
cp backend/.env.example .env        # 配置 LLM 端点与 Embedding 策略
docker compose up --build           # 一键启动前后端
# 前端 http://localhost:8080 | 后端 http://localhost:8000/docs
```

| 配置项 | 说明 |
|--------|------|
| `FASTME_LLM_BASE_URL` | OpenAI 兼容端点；容器内访问宿主机用 `host.docker.internal` |
| `FASTME_LLM_API_KEY` | 必须非空；无鉴权服务填 `not-needed` |
| `FASTME_LLM_MODEL` | 模型名，如 `qwen-plus` / `llama3.2` |
| `EMBEDDING_MODEL` | `BAAI/bge-m3`（自动下载）或本地模型路径 `/app/models/bge-m3` |

> 换 Embedding 模型后需 `docker compose down -v` 清空数据卷再重建。

---

## 🔧 二次开发

### 添加新场景（动态 API）

无需改框架代码，运行时动态添加：

```python
rag.add_scene(
    name="custom_scene",
    doc_type="log",
    prompt_template="fault_diagnosis",   # 复用已有 Prompt 模板
    top_k=10,
    description="自定义场景"
)
# 之后即可使用
result = rag.chat("...", scene="custom_scene")
```

### 添加新场景（YAML 配置）

在 `config/scenes.yaml` 中追加：

```yaml
scenes:
  comprehensive_search:
    doc_type:            # 多文档类型：匹配多个知识库
      - log
      - manual
    prompt_template: comprehensive
    top_k: 10
    description: "综合查询 - 日志+手册"
```

### 添加自定义元数据抽取规则

```python
rag.add_metadata_rule(
    field="device_model",
    patterns=[r"型号[：:\s]*([A-Z0-9\-]+)"],
    description="设备型号抽取"
)
```

### 添加自定义 Splitter

新的拆解器继承 `BaseSplitter` 并注册：

```python
from splitters.base import BaseSplitter, SplitterRegistry

class MySplitter(BaseSplitter):
    def __init__(self, max_chunk_size: int = 1000):
        super().__init__(max_chunk_size)
    def split(self, document):
        # 实现你的拆分逻辑，返回 chunk 列表
        return [...]
```

> 详细二次开发指南见 [DEVELOPER_GUIDE_CN.md](docs/DEVELOPER_GUIDE_CN.md)。

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
python -m pytest tests/ -v                # 全部测试
python -m pytest tests/test_splitters.py  # 指定模块
```

---

## 🤝 贡献

欢迎提交 issue 与 pull request。参见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [开发者指南](docs/DEVELOPER_GUIDE_CN.md)。

---

## 📄 许可证

[MIT](LICENSE) © gail peng
