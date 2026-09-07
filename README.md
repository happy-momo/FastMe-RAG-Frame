# FastMe RAG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-89%20passed-green.svg)]()

**FastMe RAG** 是一个面向制造业的轻量化、可插拔 RAG（检索增强生成）框架。专为工厂设备手册、运维日志、车间工单、工艺 SOP 等制造业文档设计，提供场景化问答和工业元数据自动抽取能力。

> 📖 [English README](README_EN.md) | 📖 [配置使用指南](examples/README.md) | 📖 [详细文档](docs/README.md)

---

## 🚀 Chatbot 演示模板（`chatbot-demo` 分支）

本仓库提供一个**开箱即用的 RAG Chatbot 服务模板**，位于 `chatbot-demo` 分支。基于 FastMe RAG 框架，使用 **Vue 3 + FastAPI + Docker Compose** 构建，完整演示框架的核心能力，可直接用于验证和二次开发。

This repository includes a **ready-to-use RAG Chatbot service template** on the `chatbot-demo` branch. Built on FastMe RAG framework with **Vue 3 + FastAPI + Docker Compose**, it fully demonstrates the framework's core capabilities.

### ✨ Demo 功能 / Demo Features

<img width="1907" height="861" alt="image" src="https://github.com/user-attachments/assets/47d53a28-869e-49fb-a69a-2781b6bd6c9f" />

<img width="1891" height="880" alt="image" src="https://github.com/user-attachments/assets/f4c1e929-820f-4148-bae5-8567164e91b2" />


| 功能 | 说明 |
|------|------|
| 💬 **流式对话** | SSE 流式输出，打字机效果 / Streaming chat with typewriter effect |
| 🎯 **4 种场景** | 故障诊断 / 手册查询 / 工单追溯 / 默认问答 / 4 scenarios: fault diagnosis / manual query / work order trace / default Q&A |
| 🔍 **溯源展示** | 相似度进度条、彩色标签、元数据详情 / Source tracing with similarity bars, colored tags, metadata details |
| 📄 **文档入库** | 拖拽上传、类型选择、4 步入库流程可视化 / Document ingestion with drag-drop, type selection, 4-step flow |
| 💾 **多会话记忆** | 多会话独立历史 / Multi-session independent history |
| 📊 **LLM 状态监控** | 实时连接状态指示 / Real-time connection status indicator |
| 🎨 **现代化 UI** | 渐变配色、卡片设计、流畅动画 / Modern UI with gradients, cards, smooth animations |

### 🚀 快速开始 / Quick Start

```bash
# 1. 克隆仓库 / Clone the repository
git clone https://github.com/happy-momo/FastMe-RAG-Frame.git
cd FastMe-RAG-Frame

# 2. 切换到 chatbot-demo 分支 / Switch to chatbot-demo branch
git checkout chatbot-demo

# 3. 配置 LLM / Configure LLM
cp .env.example .env
# 编辑 .env，设置你的 OpenAI 兼容 LLM 端点 / Edit .env with your OpenAI-compatible LLM endpoint

# 4. 一键启动 / One-click start
docker compose up -d

# 5. 访问 / Access
# 前端 Frontend:    http://localhost:8080
# 后端 API Backend: http://localhost:8000
# API 文档 Docs:    http://localhost:8000/docs
```

> **💡 本地开发 / Local Development**：详见 `chatbot-demo` 分支的文档。
>
> See docs on the `chatbot-demo` branch for detailed local development instructions.

### 🏗️ 与框架的关系 / Relationship with the Framework

Demo **完全不修改框架源码**，通过 `RAGManager` 单例以线程锁串行调用 FastMe RAG 框架，将其包装为 HTTP 服务。

The demo **does not modify framework source code at all**. It wraps FastMe RAG as an HTTP service through a `RAGManager` singleton with thread-lock serialization.

---

## 目录

- [核心特性](#-核心特性)
- [快速开始](#-快速开始)
- [核心概念](#-核心概念)
- [API 详细说明](#-api-详细说明)
  - [初始化配置](#初始化配置)
  - [文档入库](#文档入库)
  - [场景化问答](#场景化问答)
  - [流式输出](#流式输出)
  - [对话记忆](#对话记忆)
  - [向量库配置](#向量库配置)
- [支持的文档类型](#-支持的文档类型)
- [预置场景](#-预置场景)
- [元数据字段](#-元数据字段)
- [高级配置](#-高级配置)
- [开发者指南](#-开发者指南)
  - [添加新场景](#添加新场景)
  - [添加新 Splitter](#添加新-splitter)
  - [添加新向量库](#添加新向量库)
- [项目结构](#-项目结构)

---

## 🚀 核心特性

| 特性 | 描述 |
|------|------|
| 🏭 **制造业专属拆解器** | 内置 4 种拆解器（日志/手册/工单/SOP），按工业文档结构智能拆分 |
| 🔍 **场景化问答路由** | 4 种预置场景（故障诊断/手册查询/工单追溯/默认），自动路由到对应知识库 |
| 🏷️ **工业元数据抽取** | 自动提取设备 ID、产线号、故障码、工单号等 16 个工业字段 |
| 🌐 **多语言支持** | 中英文界面切换，字段标签可配置 |
| 🔌 **可插拔架构** | 基于 LangChain，Embedding/向量库/LLM 全部可配置替换 |
| 💾 **多向量库支持** | 支持 Chroma（持久化）、FAISS（内存/持久化）等向量数据库 |
| ⚙️ **配置化驱动** | YAML 配置文件定义场景、Prompt、字段标签，无需改代码 |
| 📊 **流式输出** | 支持流式问答，首字更快，体验更佳 |
| 🎛️ **灵活配置** | chunk 尺寸、批次大小、进度条等参数可自由调整 |

---

## 📦 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

> **💡 依赖说明**：`requirements.txt` 包含框架所需的所有依赖，包括 `python-docx`（用于 DOCX 文档解析，v1.1.0+）。

### 2. 配置环境变量

```bash
# 复制环境变量模板 / Copy environment variable template
cp .env.example .env

# 编辑 .env 文件，配置本地模型和 LLM 地址
# Edit .env file to configure local model and LLM endpoint

# LLM 配置 / LLM Configuration
LLM_BASE_URL=http://localhost:8000/v1
FASTME_LLM_API_KEY=your-api-key-here
LLM_MODEL=qwen-plus

# Embedding 模型配置（支持本地路径或 HuggingFace 模型名）
# Embedding model configuration (supports local path or HuggingFace model name)
# 方式 1：使用本地已下载的模型（推荐，避免重复下载）
# Option 1: Use locally downloaded model (recommended, avoids re-downloading)
EMBEDDING_MODEL=./models/bge-m3

# 方式 2：使用 HuggingFace 模型名（首次使用会自动下载）
# Option 2: Use HuggingFace model name (will auto-download on first use)
# EMBEDDING_MODEL=BAAI/bge-m3

# 向量库配置 / Vector Store Configuration
# 向量库类型：chroma | faiss（切换只需修改这一行）
# Vector store type: chroma | faiss (change this line to switch)
FASTME_VECTOR_STORE_TYPE=chroma
```

> **💡 提示 / Tip**：`FastMeRAG` 会自动从项目根目录的 `.env` 文件读取配置，无需手动传入参数。
> `FastMeRAG` automatically reads configuration from the `.env` file in the project root, no need to pass parameters manually.

### 3. 最简单的使用方式

```python
from app_factory import FastMeRAG

# 初始化（自动读取 .env 配置）
# Initialize (automatically reads .env configuration)
rag = FastMeRAG()

# 文档入库 / Document ingestion
rag.ingest("设备手册.pdf", doc_type="manual")

# 场景化问答 / Scene-aware Q&A
result = rag.chat("设备报警怎么处理？", scene="fault_diagnosis")
print(result["answer"])
```

### 4. 使用配置文件（高级）

```python
from app_factory import FastMeRAG

# 方式 1：从 YAML 配置文件加载
# Method 1: Load from YAML config file
rag = FastMeRAG.from_config("./config/fastme_chroma.yaml")

# 方式 2：从配置字典加载
# Method 2: Load from config dictionary
rag = FastMeRAG(config={
    "vector_store": {
        "type": "faiss",
        "config": {"index_path": "./data/faiss_index"}
    },
    "embedding": {"model_name": "BAAI/bge-m3"},
    "llm": {"model_name": "qwen-plus"},
})

# 方式 3：加载配置并覆盖部分值
# Method 3: Load config and override partial values
rag = FastMeRAG.from_config(
    "./config/fastme_chroma.yaml",
    overrides={"vector_store": {"config": {"collection_name": "new_coll"}}}
)
```

---

## 📖 核心概念

### 架构概览

```
用户问题
    ↓
┌─────────────────────────────────────────────────┐
│           FastMeRAG (主框架入口)                 │
├─────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────────────┐   │
│  │ 文档入库     │    │  场景化问答           │   │
│  │ IngestPipe  │    │  ChatPipeline        │   │
│  └──────┬──────┘    └──────────┬───────────┘   │
│         ↓                      ↓                │
│  ┌─────────────────────────────────────────┐   │
│  │      SceneAwareRetriever (场景感知)      │   │
│  └──────────────────┬──────────────────────┘   │
│                     ↓                           │
│  ┌─────────────────────────────────────────┐   │
│  │  VectorStoreFactory → VectorStoreAdapter │   │
│  │  (ChromaAdapter / FAISSAdapter)          │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `FastMeRAG` | `app_factory.py` | 主框架入口，编排所有组件 |
| `IngestPipeline` | `core/ingest_pipeline.py` | 文档入库流水线 |
| `ChatPipeline` | `core/chat_pipeline.py` | 对话流水线 |
| `SceneAwareRetriever` | `retrievers/scene_aware.py` | 场景感知检索器 |
| `VectorStoreAdapter` | `vector_stores/base.py` | 向量库抽象基类 |
| `ChromaAdapter` | `vector_stores/chroma.py` | Chroma 向量库适配器 |
| `FAISSAdapter` | `vector_stores/faiss.py` | FAISS 向量库适配器 |

---

## ⚙️ 环境变量配置

### `.env` 文件说明

`FastMeRAG` 框架会自动从项目根目录的 `.env` 文件读取配置，无需在代码中手动传入参数。

**完整的 `.env` 配置示例：**

```bash
# ===== LLM 配置 / LLM Configuration =====
LLM_BASE_URL=http://localhost:8000/v1
FASTME_LLM_API_KEY=your-api-key-here
LLM_MODEL=qwen-plus

# ===== Embedding 模型配置 / Embedding Model Configuration =====
# 方式 1：使用本地已下载的模型（推荐，避免重复下载）
# Option 1: Use locally downloaded model (recommended, avoids re-downloading)
EMBEDDING_MODEL=./models/bge-m3

# 方式 2：使用 HuggingFace 模型名（首次使用会自动下载）
# Option 2: Use HuggingFace model name (will auto-download on first use)
# EMBEDDING_MODEL=BAAI/bge-m3

# 可选：模型缓存目录（当使用 HuggingFace 模型名时生效）
# Optional: Model cache directory (only used when EMBEDDING_MODEL is a HuggingFace model name)
# MODEL_CACHE_DIR=./models

# ===== 向量库配置 / Vector Store Configuration =====
# 向量库类型：chroma | faiss
# 切换向量库只需修改这一行即可
# Vector store type: change this line to switch vector store
FASTME_VECTOR_STORE_TYPE=chroma

# Chroma 配置（FASTME_VECTOR_STORE_TYPE=chroma 时生效）
# Chroma configuration (effective when FASTME_VECTOR_STORE_TYPE=chroma)
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION=fastme_rag

# FAISS 配置（FASTME_VECTOR_STORE_TYPE=faiss 时生效）
# FAISS configuration (effective when FASTME_VECTOR_STORE_TYPE=faiss)
FAISS_INDEX_PATH=./data/faiss_index

# ===== 其他配置 / Other Configuration =====
# FASTME_LANGUAGE=zh  # 界面语言，可选：zh（中文）| en（英文）
```

### 切换向量库 / Switching Vector Store

**只需修改一行配置即可切换向量库：**

```bash
# 使用 Chroma（默认）/ Use Chroma (default)
FASTME_VECTOR_STORE_TYPE=chroma

# 切换到 FAISS / Switch to FAISS
FASTME_VECTOR_STORE_TYPE=faiss
```

| 向量库 | 特点 | 适用场景 |
|--------|------|----------|
| **Chroma** | 持久化存储，支持元数据过滤 | 生产环境，需要数据持久化 |
| **FAISS** | 内存索引，支持自动持久化，速度极快 | 开发测试，对性能要求高的场景 |

### 环境变量优先级

配置值的优先级顺序：**配置文件 > 环境变量 > 代码默认值**

```python
from app_factory import FastMeRAG

# 场景 1：不传参数，从 .env 读取（推荐）
# Scenario 1: No parameters, read from .env (recommended)
rag = FastMeRAG()  # 使用 .env 中的配置

# 场景 2：从配置文件加载
# Scenario 2: Load from config file
rag = FastMeRAG.from_config("./config/fastme_faiss.yaml")

# 场景 3：使用配置字典
# Scenario 3: Use config dictionary
rag = FastMeRAG(config={
    "vector_store": {"type": "faiss"},
    "embedding": {"model_name": "BAAI/bge-m3"},
    "llm": {"model_name": "qwen-plus"}
})
```

### 本地模型 vs HuggingFace 模型

**`EMBEDDING_MODEL` 支持两种配置方式：**

| 配置方式 | 示例 | 说明 |
|---------|------|------|
| **本地路径** | `./models/bge-m3` | 直接从本地加载，无需网络连接，速度快 |
| **HuggingFace 模型名** | `BAAI/bge-m3` | 首次使用会自动下载到 `MODEL_CACHE_DIR` 目录 |

**推荐使用本地路径**，避免每次初始化时尝试连接 HuggingFace 下载模型。

**步骤：**

1. 首次手动下载模型：
   ```bash
   # 可以使用 git clone 或 huggingface-cli 下载
   git lfs install
   git clone https://huggingface.co/BAAI/bge-m3 ./models/bge-m3
   ```

2. 在 `.env` 中配置本地路径：
   ```bash
   EMBEDDING_MODEL=./models/bge-m3
   ```

---

## 🔧 API 详细说明

### 初始化配置

#### `FastMeRAG.__init__()`

```python
from app_factory import FastMeRAG

# 方式 1：使用 .env 文件中的配置（推荐）
# 环境变量会自动从项目根目录的 .env 文件加载
rag = FastMeRAG()

# 方式 2：通过参数覆盖 .env 配置
rag = FastMeRAG(
    # ========== 模型配置 ==========
    embedding_model: str = "BAAI/bge-m3",      # Embedding 模型名称（本地路径或 HuggingFace 模型名）
    model_cache_dir: str = "./models",          # 模型缓存目录
    llm_base_url: str = "http://localhost:8000/v1/chat/completions",  # LLM API 地址
    llm_api_key: str = "sk-xxx",                # LLM API Key
    llm_model: str = "qwen-plus",               # LLM 模型名称
    temperature: float = 0.2,                   # LLM 温度参数
    language: str = "zh",                       # 语言 ("zh" | "en")

    # ========== Chunk 与批量处理配置 ==========
    chunk_max_size: int = 1000,                 # 单个 chunk 最大字符数
    ingest_batch_size: int = 32,                # 入库分批大小
    embedding_batch_size: int = 32,             # Embedding 批量大小
    show_progress_bar: bool = False,            # 是否显示进度条

    # ========== 向量库配置 ==========
    vector_store_type: str = "chroma",          # 向量库类型 ("chroma" | "faiss")
    vector_store_config: dict = None,           # 向量库特定配置

    # ========== 向后兼容参数 ==========
    chroma_dir: str = "./data/chroma",          # Chroma 数据目录（向后兼容）
    chroma_collection: str = "fastme_rag",      # Chroma 集合名称（向后兼容）
)
```

> **💡 重要提示**：
> - 推荐在 `.env` 文件中配置环境变量，`FastMeRAG()` 会自动读取
> - `EMBEDDING_MODEL` 支持两种格式：
>   - **本地路径**：`./models/bge-m3`（直接从本地加载，无需下载）
>   - **HuggingFace 模型名**：`BAAI/bge-m3`（首次使用会自动下载到 `model_cache_dir`）

#### 参数详细说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `embedding_model` | str | `"BAAI/bge-m3"` | HuggingFace Embedding 模型名称，或本地模型路径（如 `./models/bge-m3`）。**优先从 `.env` 读取** |
| `model_cache_dir` | str | `"./models"` | 模型缓存目录。当 `embedding_model` 是 HuggingFace 模型名时，模型会下载到此目录。**优先从 `.env` 读取** |
| `llm_base_url` | str | `"http://localhost:8000/v1/chat/completions"` | LLM API 地址（兼容 OpenAI 格式）。**优先从 `.env` 读取** |
| `llm_api_key` | str | `"sk-1234567890abcdef..."` | LLM API Key。**优先从 `.env` 读取** |
| `llm_model` | str | `"qwen-plus"` | LLM 模型名称。**优先从 `.env` 读取** |
| `temperature` | float | `0.2` | LLM 温度参数，值越小回答越确定 |
| `language` | str | `"zh"` | 界面语言，支持 `"zh"`（中文）和 `"en"`（英文） |
| `chunk_max_size` | int | `1000` | 单个 chunk 最大字符数。建议：日志 500-800，手册 1000-1500，工单 800-1200 |
| `ingest_batch_size` | int | `32` | 入库分批大小。内存受限时减小（16-24），高性能环境可增大（64-128） |
| `embedding_batch_size` | int | `32` | Embedding 批量大小。GPU 用户可增大（64-128），内存受限减小（8-16） |
| `show_progress_bar` | bool | `False` | 是否显示进度条。ingest 大文件时建议开启 |
| `vector_store_type` | str | `"chroma"` | 向量库类型，支持 `"chroma"` 或 `"faiss"` |
| `vector_store_config` | dict | `None` | 向量库特定配置（见下文） |

> **环境变量优先级**：参数传入 > `.env` 文件 > 代码默认值
> - 如果传入了参数（如 `embedding_model="./models/bge-m3"`），使用参数值
> - 如果没有传入参数，从 `.env` 文件读取
> - 如果 `.env` 中也没有配置，使用代码中的默认值
>
> **YAML 配置新增生效字段**：
> - `embedding.device`：指定 Embedding 模型运行设备（如 `cuda` / `cpu`），之前被硬编码忽略，现已生效
> - `chat_pipeline.default_top_k`：对话管道的默认召回数量，优先级低于调用方显式传入和场景配置
> - `chat_pipeline.max_context_length`：上下文最大字符数，超过则截断（追加 `...(上下文已截断)`），设为 `null` 不限制

#### 配置示例

**默认配置（从 .env 读取）：**
```python
# 推荐方式：在 .env 文件中配置，代码自动读取
rag = FastMeRAG()
```

**使用 FAISS 向量库：**
```python
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={
        "index_path": "./data/faiss_index"
    }
)
```

**内存受限环境配置：**
```python
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={
        "index_path": "./data/faiss_index"
    }
)
```

**内存受限环境配置：**
```python
rag = FastMeRAG(
    chunk_max_size=800,        # 减小 chunk 尺寸
    ingest_batch_size=16,      # 减小入库批次
    embedding_batch_size=16,   # 减小 embedding 批量
    show_progress_bar=False,
)
```

**高性能配置（GPU 环境）：**
```python
rag = FastMeRAG(
    chunk_max_size=1500,       # 增大 chunk 尺寸
    ingest_batch_size=64,      # 增大入库批次
    embedding_batch_size=64,   # 增大 embedding 批量
    show_progress_bar=True,
)
```

**使用英文界面：**
```python
rag = FastMeRAG(language="en")
```

---

### 文档入库

#### `ingest()` - 单文档入库

```python
result = rag.ingest(
    file_path: str,                    # 文件路径（必填）
    doc_type: str,                     # 文档类型（必填）：log/manual/business/sop
    extra_metadata: dict = None,       # 额外元数据（可选）
    require_review: bool = False       # 是否需要审核（可选）
)
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_path` | str | ✅ | 文件路径，支持 PDF、DOCX、TXT、LOG、MD 格式 |
| `doc_type` | str | ✅ | 文档类型：`"log"`（日志）、`"manual"`（手册）、`"business"`（工单）、`"sop"`（工艺） |
| `extra_metadata` | dict | ❌ | 额外元数据，会注入到所有切片中。例如：`{"device_id": "EQ001", "line_id": "LN01"}` |
| `require_review` | bool | ❌ | 是否需要审核。`True` 时返回切片预览，不实际入库 |

**返回值：**

```python
# 成功入库时
{
    "status": "success",
    "doc_id": "doc_20240115_abc123",     # 文档唯一 ID
    "file_name": "设备手册.pdf",          # 文件名
    "doc_type": "manual",                # 文档类型
    "chunks_count": 15,                  # 切片数量
    "vector_count": 115                  # 向量库总量
}

# 审核模式时
{
    "status": "waiting_review",
    "doc_id": "doc_20240115_abc123",
    "file_name": "设备手册.pdf",
    "doc_type": "manual",
    "chunks": [                          # 切片列表（预览用）
        {
            "chunk_id": "doc_20240115_abc123_0",
            "text": "第一章 设备概述...",
            "metadata": {"chapter_num": "1", "chapter_title": "设备概述"}
        },
        ...
    ]
}
```

> **💡 FAISS 持久化说明**：`ingest()` 在入库完成后会自动调用 `persist()` 将数据写入磁盘，确保进程退出后数据不丢失。Chroma 后端行为不变（自动持久化）。`batch_ingest()` 的 `persist_interval` 参数含义不变（内存清理间隔）。

**示例：**

```python
from app_factory import FastMeRAG

rag = FastMeRAG()

# 1. 基本入库
result = rag.ingest("设备手册.pdf", doc_type="manual")
print(f"入库成功：{result['chunks_count']} 个切片")

# 2. 带额外元数据入库
result = rag.ingest(
    file_path="故障日志.log",
    doc_type="log",
    extra_metadata={
        "device_id": "EQ001",    # 设备 ID
        "line_id": "LN01"        # 产线 ID
    }
)

# 3. 审核模式（预览切片，不入库）
result = rag.ingest("工单.xlsx", doc_type="business", require_review=True)
if result["status"] == "waiting_review":
    print(f"待审核：{len(result['chunks'])} 个切片")
    for chunk in result["chunks"][:3]:  # 预览前 3 个
        print(f"  - {chunk['chunk_id']}: {chunk['text'][:50]}...")
```

#### `batch_ingest()` - 批量入库

```python
results = rag.batch_ingest(
    folder_path: str,                      # 文件夹路径（必填）
    doc_type: str,                         # 文档类型（必填）
    extra_metadata: dict = None,           # 额外元数据（可选）
    file_extensions: list = None,          # 文件扩展名过滤（可选）
    persist_interval: int = 10             # 内存清理间隔（可选）
)
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `folder_path` | str | - | 文件夹路径 |
| `doc_type` | str | - | 文档类型 |
| `extra_metadata` | dict | `None` | 所有文件共享的额外元数据 |
| `file_extensions` | list | `[".pdf", ".docx", ".txt", ".log", ".md"]` | 文件扩展名过滤 |
| `persist_interval` | int | `10` | 每处理 N 个文件后执行内存清理，设为 `0` 禁用 |

**返回值：**

```python
[
    {"status": "success", "doc_id": "doc_001", "chunks_count": 10, ...},
    {"status": "success", "doc_id": "doc_002", "chunks_count": 15, ...},
    {"status": "error", "file": "failed.pdf", "error": "无法解析文件"}
]
```

**示例：**

```python
# 批量入库日志文件夹
results = rag.batch_ingest(
    folder_path="./logs",
    doc_type="log",
    extra_metadata={"project": "生产线A"}
)

# 统计结果
success = sum(1 for r in results if r["status"] == "success")
print(f"成功入库 {success} 个文件")

# 大文件时使用更小的内存清理间隔
results = rag.batch_ingest(
    folder_path="./manuals",
    doc_type="manual",
    persist_interval=5  # 每 5 个文件清理一次
)
```

---

### 场景化问答

#### `chat()` - 同步问答

```python
result = rag.chat(
    question: str,                    # 用户问题（必填）
    scene: str = "default",           # 场景名称（可选）
    filters: dict = None,             # 过滤条件（可选）
    top_k: int = None                 # 召回数量（可选）
)
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `question` | str | - | 用户问题 |
| `scene` | str | `"default"` | 场景名称，可选：`"fault_diagnosis"`、`"manual_query"`、`"work_order_trace"`、`"default"` |
| `filters` | dict | `None` | 过滤条件，例如：`{"device_id": "EQ001", "line_id": "LN01"}` |
| `top_k` | int | 场景配置 | 召回数量，默认使用场景配置（通常为 5） |

**返回值：**

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
            "doc_type": "log",
            "device_id": "EQ001",
            "fault_code": "E001",
            "timestamp": "2024-01-15 10:30:00",
            "score": 0.95,               # 相似度得分
            "preview": "设备报警记录..."   # 文本预览
        },
        ...
    ]
}
```

**示例：**

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("故障日志.log", doc_type="log")

# 1. 基本问答
result = rag.chat("设备报警怎么处理？", scene="fault_diagnosis")
print(f"回答：{result['answer']}")

# 2. 带过滤条件的问答
result = rag.chat(
    question="E001 设备有哪些故障？",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}  # 只检索设备 EQ001 的记录
)

# 3. 查看溯源信息
print("\n溯源信息：")
for source in result["sources"]:
    print(f"  - [{source['score']:.2f}] {source['device_id']}: {source['preview'][:50]}...")

# 4. 自定义召回数量
result = rag.chat("设备手册内容", scene="manual_query", top_k=10)
```

#### 过滤条件详解

**Chroma 向量库（原生支持）：**
```python
# 单条件过滤
filters = {"device_id": "EQ001"}

# 多条件过滤（AND 关系）
filters = {
    "device_id": "EQ001",
    "line_id": "LN01"
}

# 检索时只返回同时满足 device_id=EQ001 AND line_id=LN01 的结果
result = rag.chat("故障记录", scene="fault_diagnosis", filters=filters)
```

**FAISS 向量库（后过滤策略）：**
```python
# FAISS 不支持原生过滤，使用"召回 + 后过滤"策略
# 会先召回 top_k * post_filter_multiplier 个结果，再按条件过滤

filters = {"device_id": "EQ001"}
result = rag.chat("故障记录", scene="fault_diagnosis", filters=filters)
```

---

### 流式输出

#### `chat_stream()` - 流式问答

```python
for chunk in rag.chat_stream(
    question: str,                    # 用户问题（必填）
    scene: str = "default",           # 场景名称（可选）
    filters: dict = None,             # 过滤条件（可选）
    top_k: int = None                 # 召回数量（可选）
):
    print(chunk, end="", flush=True)
```

**参数说明：**

与 `chat()` 相同。

**返回值：**

- 生成器（Generator），每次 `yield` 一个文本片段（`str`）

**示例：**

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("设备手册.pdf", doc_type="manual")

# 流式问答（类似 ChatGPT 的打字机效果）
print("AI: ", end="", flush=True)
for chunk in rag.chat_stream(
    question="设备操作步骤是什么？",
    scene="manual_query"
):
    print(chunk, end="", flush=True)
print()  # 换行

# 输出示例：
# AI: 根据设备手册，操作步骤如下：
# 1. 启动前检查电源连接...
# 2. 按下启动按钮...
# ...
```

---

### 对话记忆

#### `create_memory()` - 创建会话记忆

```python
rag.create_memory(
    session_id: str,              # 会话 ID（必填）
    max_turns: int = 10           # 最大保留轮次（可选）
)
```

#### `chat_with_memory()` - 带记忆的对话

```python
result = rag.chat_with_memory(
    question: str,                    # 用户问题（必填）
    session_id: str,                  # 会话 ID（必填）
    scene: str = "default",           # 场景名称（可选）
    filters: dict = None,             # 过滤条件（可选）
    top_k: int = None                 # 召回数量（可选）
)
```

> **💡 记忆保护**：当 LLM 返回空回答时，框架会返回兜底文本"抱歉，未能生成有效回答…"，但**不会将其存入对话记忆**，避免污染多轮上下文。

#### `get_memory()` - 获取会话记忆

```python
memory = rag.get_memory(session_id: str)
```

#### `clear_memory()` - 清除记忆

```python
# 清除指定会话
rag.clear_memory(session_id: str)

# 清除所有会话
rag.clear_memory()
```

**完整示例：**

```python
from app_factory import FastMeRAG

rag = FastMeRAG()
rag.ingest("故障日志.log", doc_type="log")

# 创建会话记忆
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
    question="那怎么处理这个故障？",  # 可以引用上一轮的 E001 设备
    session_id="user_001",
    scene="fault_diagnosis"
)
print(f"回答 2：{result2['answer']}")

# 查看历史记忆
memory = rag.get_memory("user_001")
print(f"历史对话：{memory}")

# 清除记忆
rag.clear_memory(session_id="user_001")
```

---

### 向量库配置

#### Chroma 向量库（默认）

**特性：**
- ✅ 持久化存储（数据保存在磁盘）
- ✅ 原生支持元数据过滤
- ✅ 集合（Collection）隔离

**配置方式：**

```python
# 方式 1：通过向后兼容参数
rag = FastMeRAG(
    chroma_dir="./data/chroma",           # Chroma 数据目录
    chroma_collection="my_collection"     # 集合名称
)

# 方式 2：通过 vector_store_config
rag = FastMeRAG(
    vector_store_type="chroma",
    vector_store_config={
        "persist_directory": "./data/chroma",
        "collection_name": "my_collection"
    }
)
```

**配置参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `persist_directory` | str | `"./data/chroma"` | Chroma 数据目录 |
| `collection_name` | str | `"fastme_rag"` | 集合名称（数据隔离） |

**使用场景：**

```python
# 不同环境隔离
rag_dev = FastMeRAG(chroma_collection="dev_collection")
rag_prod = FastMeRAG(chroma_collection="prod_collection")

# 不同项目隔离
rag_project_a = FastMeRAG(chroma_collection="project_a")
rag_project_b = FastMeRAG(chroma_collection="project_b")

# 不同文档类型隔离
rag_manual = FastMeRAG(chroma_collection="manual_collection")
rag_log = FastMeRAG(chroma_collection="log_collection")
```

#### FAISS 向量库

**特性：**
- ✅ 内存存储（高性能）
- ✅ 支持持久化到磁盘
- ⚠️ 不支持原生元数据过滤（使用后过滤策略）

**配置方式：**

```python
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={
        "index_path": "./data/faiss_index"
    }
)
```

**配置参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `index_path` | str | `"./data/faiss_index"` | FAISS 索引路径 |

**后过滤策略：**

FAISS 不支持原生元数据过滤，使用"召回 + 后过滤"策略：

```python
# 检索流程：
# 1. 先召回 top_k * post_filter_multiplier 个结果
# 2. 按 filters 条件过滤
# 3. 返回符合条件的 top_k 个结果

result = rag.chat(
    question="故障记录",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}
)
```

---

## 📚 支持的文档类型

| 文档类型 | `doc_type` | 拆解器 | 适用场景 | 推荐配置 |
|----------|------------|--------|----------|----------|
| 📋 运维日志 | `"log"` | `LogSplitter` | 设备故障日志、系统运行日志 | `chunk_max_size=500-800` |
| 📖 设备手册 | `"manual"` | `ManualSplitter` | 操作手册、维修手册、技术规格书 | `chunk_max_size=1000-1500` |
| 📝 车间工单 | `"business"` | `BusinessSplitter` | 质检单、生产记录、工单 | `chunk_max_size=800-1200` |
| 🔧 工艺 SOP | `"sop"` | `SopSplitter` | 作业指导书、BOM 文档、工艺流程 | `chunk_max_size=1000-1500` |

### 文档类型对应的元数据字段

**日志文档（log）：**
```python
metadata = {
    "device_id": "EQ001",       # 设备 ID
    "line_id": "LN01",          # 产线 ID
    "fault_code": "E001",       # 故障码
    "timestamp": "2024-01-15",  # 时间戳
    ...
}
```

**手册文档（manual）：**
```python
metadata = {
    "chapter_num": "1",         # 章节号
    "chapter_title": "设备概述", # 章节标题
    "device_model": "EQ-1000",  # 设备型号
    ...
}
```

**工单文档（business）：**
```python
metadata = {
    "work_order_id": "WO001",   # 工单号
    "material_id": "M001",      # 物料号
    "station": "Station_A",     # 工位
    "quality_result": "合格",    # 质检结果
    ...
}
```

**SOP 文档（sop）：**
```python
metadata = {
    "process_num": "工序 1",     # 工序号
    "bom_items": ["零件A", "零件B"],  # BOM 物料
    "device_model": "EQ-1000",  # 设备型号
    ...
}
```

---

## 🎯 预置场景

| 场景 | `scene` | 描述 | 对应文档类型 |
|------|---------|------|-------------|
| 🛠️ 故障诊断 | `"fault_diagnosis"` | 基于运维日志、故障记录进行诊断 | log |
| 📖 手册查询 | `"manual_query"` | 设备手册、技术文档查询 | manual |
| 📋 工单追溯 | `"work_order_trace"` | 工单、生产记录追溯 | business |
| 💬 默认问答 | `"default"` | 通用问答场景 | 所有类型 |

### 场景配置文件（config/scenes.yaml）

#### 单文档类型场景

```yaml
scenes:
  fault_diagnosis:
    doc_type: log                        # 单个文档类型
    prompt_template: fault_diagnosis     # Prompt 模板名称
    top_k: 5                             # 召回数量
    source_fields:                       # 溯源字段
      - chunk_id
      - doc_id
      - device_id
      - fault_code
      - timestamp
    description: "设备故障诊断"
```

#### 多文档类型场景（🆕 新增支持）

```yaml
scenes:
  # 综合查询场景 - 同时检索日志和手册
  comprehensive_search:
    doc_type:                            # 列表格式：匹配多个文档类型
      - log
      - manual
    prompt_template: comprehensive
    top_k: 10
    source_fields:
      - chunk_id
      - doc_id
      - doc_type
      - source
    description: "综合查询 - 日志+手册"

  # 知识库场景 - 排除日志类型
  knowledge_base:
    doc_type:
      - manual
      - sop
      - business
    prompt_template: default
    top_k: 5
    description: "知识库查询 - 排除日志"
```

**多文档类型说明：**
- `doc_type: ["log", "manual"]` 自动转换为 Chroma 的 `$in` 操作符
- 支持单值字符串、列表、null 三种格式
- FAISS 向量库通过后过滤实现相同功能

### 溯源字段说明

每个场景返回的 `sources` 中包含的字段：

**故障诊断场景：**
- `chunk_id`: 切片 ID
- `doc_id`: 文档 ID
- `device_id`: 设备 ID
- `line_id`: 产线 ID
- `fault_code`: 故障码
- `timestamp`: 时间戳
- `score`: 相似度得分

**手册查询场景：**
- `chunk_id`: 切片 ID
- `doc_id`: 文档 ID
- `chapter_num`: 章节号
- `chapter_title`: 章节标题
- `device_model`: 设备型号
- `score`: 相似度得分

**工单追溯场景：**
- `chunk_id`: 切片 ID
- `doc_id`: 文档 ID
- `work_order_id`: 工单号
- `material_id`: 物料号
- `station`: 工位
- `quality_result`: 质检结果
- `score`: 相似度得分

---

## 🏷️ 元数据字段

### 自动提取的工业字段

| 字段 | 中文标签 | 英文标签 | 适用文档类型 | 正则示例 |
|------|---------|---------|-------------|---------|
| `device_id` | 设备 | Device | log, manual, sop | `设备 ID: EQ001` |
| `line_id` | 产线 | Production Line | log, business | `产线号: LN01` |
| `fault_code` | 故障码 | Fault Code | log | `故障代码: E001` |
| `work_order_id` | 工单号 | Work Order | business | `工单号: WO001` |
| `material_id` | 物料号 | Material | business, sop | `物料号: M001` |
| `station` | 工位 | Station | business | `工位: Station_A` |
| `quality_result` | 质检结果 | Quality Result | business | `质检结果: 合格` |
| `device_model` | 设备型号 | Device Model | manual, sop | `设备型号: EQ-1000` |
| `process_num` | 工序号 | Process | sop | `工序号: 工序 1` |
| `bom_items` | BOM 物料 | BOM Items | sop | `BOM: 零件A, 零件B` |
| `timestamp` | 时间 | Timestamp | log | `时间: 2024-01-15 10:30:00` |
| `chapter_num` | 章节号 | Chapter | manual | `第 1 章` |
| `chapter_title` | 章节标题 | Chapter Title | manual | `设备概述` |

### 配置文件（config/field_labels.yaml）

```yaml
zh:
  chunk_id: "片段 ID"
  doc_id: "文档 ID"
  device_id: "设备"
  fault_code: "故障码"
  ...

en:
  chunk_id: "Chunk ID"
  doc_id: "Document ID"
  device_id: "Device"
  fault_code: "Fault Code"
  ...
```

### 自定义元数据抽取规则

```python
# 添加设备型号抽取规则
rag.add_metadata_rule(
    field="device_model",
    patterns=[
        r"设备型号 [::\s]*([A-Za-z0-9\-_]+)",
        r"产品型号 [::\s]*([A-Za-z0-9\-_]+)"
    ],
    description="设备型号"
)

# 测试提取
result = rag.ingest("设备手册.pdf", doc_type="manual")
# metadata 中会包含自动提取的 device_model 字段
```

---

## ⚙️ 高级配置

### 自定义场景

```python
rag = FastMeRAG()

# 添加质检查询场景
rag.add_scene(
    name="quality_check",                    # 场景名称
    doc_type="business",                     # 对应文档类型
    prompt_template="default",               # Prompt 模板
    top_k=5,                                 # 召回数量
    source_fields=["work_order_id", "quality_result", "station"],  # 溯源字段
    description="质检查询场景"
)

# 使用新场景
result = rag.chat("批次 2024001 合格吗？", scene="quality_check")
```

### 更新场景配置

```python
# 更新场景的 top_k
rag.update_scene_top_k(scene="fault_diagnosis", top_k=10)
```

### 切换语言

```python
# 切换为英文界面
rag.set_language("en")

# 切换回中文
rag.set_language("zh")
```

### 查询统计信息

```python
# 获取所有可用场景
scenes = rag.get_scenes()
# ['fault_diagnosis', 'manual_query', 'work_order_trace', 'default']

# 获取所有支持的文档类型
doc_types = rag.get_doc_types()
# ['log', 'manual', 'business', 'sop']

# 获取向量库中的向量总数
count = rag.get_vector_count()
print(f"向量总数：{count}")
```

### 删除集合

```python
# 删除当前集合（清空数据）
rag.delete_collection()

# 重新入库
rag.ingest("新文档.pdf", doc_type="manual")
```

---

## 👨‍💻 开发者指南

本章节面向需要扩展框架功能的开发者，介绍如何添加新的场景、拆解器和向量库。

---

### 添加新场景

场景（Scene）是 FastMe RAG 框架的核心概念，用于将用户问题路由到特定的知识库和 Prompt 模板。框架提供了两种添加新场景的方式。

#### 方式一：通过配置文件添加（推荐）

**配置文件位置：** `config/scenes.yaml`

**配置结构：**

```yaml
scenes:
  <场景名称>:
    doc_type: <文档类型>          # log/manual/business/sop，或 null 表示不限制
    prompt_template: <模板名称>    # 引用 prompt_templates.yaml 中的模板
    top_k: <召回数量>              # 检索时返回的文档数量
    source_fields:                 # 溯源字段列表
      - chunk_id
      - doc_id
      - <其他元数据字段>
    description: <场景描述>
```

**完整示例：添加"质检查询"场景**

编辑 `config/scenes.yaml`，添加新场景配置：

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

然后，在 `config/prompt_templates.yaml` 中添加对应的 Prompt 模板：

```yaml
quality_check:
  system: |
    你是一个专业的质量检测助手。请根据检索到的质检记录回答用户问题。

    回答要求：
    1. 准确引用工单号、质检结果等关键信息
    2. 如有不合格项，说明具体问题和处理建议
    3. 回答简洁专业，突出关键数据
```

**使用新场景：**

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

#### 方式二：通过代码动态添加

使用 `add_scene()` 方法可以在运行时动态添加场景，无需修改配置文件。

**方法签名：**

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

**完整示例：**

```python
from app_factory import FastMeRAG

# 初始化框架
rag = FastMeRAG()

# 1. 定义 Prompt 模板（需要先在 prompt_templates.yaml 中配置）
# 或使用已有模板，如 "default"

# 2. 动态添加"设备维护"场景
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

# 3. 入库文档
rag.ingest("设备维护手册.pdf", doc_type="manual")

# 4. 使用动态添加的场景
result = rag.chat(
    question="EQ-1000 设备的日常维护步骤是什么？",
    scene="device_maintenance"
)
print(result["answer"])

# 5. 查看溯源信息
for source in result["sources"]:
    print(f"  - 第 {source['chapter_num']} 章: {source['chapter_title']}")
```

**注意事项：**

- 动态添加的场景在框架重启后不会保留，如需持久化请使用配置文件方式
- `source_fields` 默认为 `["chunk_id", "doc_id", "doc_type", "source"]`
- 场景名称不能与已有场景重复

---

### 添加新 Splitter

Splitter（拆解器）负责将文档按其结构特点拆分成语义完整的切片。添加新 Splitter 需要继承 `BaseSplitter` 并实现 `split()` 方法。

#### 步骤说明

| 步骤 | 文件位置 | 说明 |
|------|----------|------|
| 1. 创建新 Splitter 类 | `splitters/<name>_splitter.py` | 继承 `BaseSplitter`，实现 `split()` 方法 |
| 2. 注册到 SplitterRegistry | `app_factory.py` | 在初始化时注册新的 Splitter |
| 3. 更新导出 | `splitters/__init__.py` | 导出新类（可选） |

#### 基类结构

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

**可用的辅助方法（继承自 BaseSplitter）：**

| 方法 | 用途 |
|------|------|
| `_split_by_paragraphs(lines, max_size)` | 按段落切分，控制大小 |
| `_split_large_text(content, max_size)` | 大文本切分助手 |
| `_generate_chunk_id(doc_id, chunk_index, ...)` | 生成切片 ID |
| `_build_chunk_metadata(document, ...)` | 构建标准元数据字典 |
| `_extract_with_patterns(text, patterns, findall)` | 正则提取助手 |

#### 完整示例：添加"技术规格书"拆解器

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
        # 示例文本：
        # 输入电压: 220V AC
        # 功率: 500W
        # 工作温度: -20°C ~ 60°C
        
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

# 在 FastMeRAG.__init__ 方法中，找到 Splitter 注册部分（约 221-225 行）
# 添加新的注册：

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

**使用新 Splitter：**

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

### 添加新向量库

FastMe RAG 支持多种向量数据库，通过适配器模式实现可插拔。添加新向量库需要：

1. 实现 `VectorStoreAdapter` 接口
2. 创建适配器类
3. 更新 `VectorStoreFactory`
4. 创建对应的 Retriever

#### 步骤说明

| 步骤 | 文件位置 | 说明 |
|------|----------|------|
| 1. 创建适配器类 | `vector_stores/<name>.py` | 继承 `VectorStoreAdapter`，实现所有抽象方法 |
| 2. 创建检索器类 | `vector_stores/<name>_retriever.py` | 继承 `BaseRetriever`，实现 `retrieve()` 方法 |
| 3. 更新 VectorStoreFactory | `vector_stores/factory.py` | 添加新向量库类型的创建逻辑 |
| 4. 更新 RetrieverFactory | `retrievers/factory.py` | 添加新检索器的创建逻辑 |

#### 接口定义

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
        # 默认实现已提供
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

#### 完整示例：添加 Milvus 向量库

以 Milvus 为例，展示如何添加新的向量库支持。

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
        """
        初始化 Milvus 适配器
        
        Args:
            collection_name: 集合名称
            connection_args: 连接参数，如 {"host": "localhost", "port": "19530"}
            embedding_function: Embedding 函数
        """
        self.collection_name = collection_name
        self.connection_args = connection_args
        self.embedding_function = embedding_function
        
        # 延迟导入，避免未安装时报错
        from langchain_milvus import Milvus
        
        # 创建 Milvus 向量库实例
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
        """
        添加文档到 Milvus
        
        Args:
            documents: LangChain Document 列表
            ids: 可选的文档 ID 列表
        """
        # 清理元数据（Milvus 只支持基本类型）
        sanitized_docs = []
        for doc in documents:
            clean_metadata = self.sanitize_metadata(doc.metadata)
            sanitized_docs.append(Document(
                page_content=doc.page_content,
                metadata=clean_metadata
            ))
        
        # Milvus 会自动生成 ID，传入的 ids 参数目前不支持
        self._milvus.add_documents(sanitized_docs)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        相似度搜索
        
        Args:
            query: 查询文本
            k: 返回数量
            filter: 元数据过滤条件
        
        Returns:
            (Document, score) 元组列表
        """
        # Milvus 支持原生元数据过滤
        # 过滤条件格式示例：{"device_id": "EQ001"}
        results = self._milvus.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter  # Milvus 使用 expr 参数，LangChain 会自动转换
        )
        return results
    
    def get_count(self) -> int:
        """返回向量总数"""
        # Milvus 统计需要查询集合
        from pymilvus import connections, Collection
        
        # 获取集合统计
        connections.connect(
            alias="default",
            host=self.connection_args.get("host", "localhost"),
            port=self.connection_args.get("port", "19530")
        )
        collection = Collection(self.collection_name)
        count = collection.num_entities
        return count
    
    def delete_collection(self) -> None:
        """删除集合"""
        from pymilvus import connections, utility
        
        connections.connect(
            alias="default",
            host=self.connection_args.get("host", "localhost"),
            port=self.connection_args.get("port", "19530")
        )
        
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
        
        # 重新创建空集合
        self._milvus = Milvus(
            embedding_function=self.embedding_function,
            collection_name=self.collection_name,
            connection_args=self.connection_args
        )
    
    def get_config(self) -> Dict[str, Any]:
        """返回配置信息"""
        return {
            "collection_name": self.collection_name,
            "connection_args": self.connection_args,
            "vector_count": self.get_count(),
            "supports_filter": True
        }
    
    def supports_filter(self) -> bool:
        """Milvus 支持原生元数据过滤"""
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
from langchain_core.documents import Document
from core.models import FastMeSearchResult
from core.retriever import BaseRetriever, ResultConverterMixin, FilterCondition
from vector_stores.milvus import MilvusAdapter


class MilvusRetriever(BaseRetriever, ResultConverterMixin):
    """Milvus 检索器"""
    
    def __init__(self, adapter: MilvusAdapter):
        """
        初始化检索器
        
        Args:
            adapter: Milvus 适配器实例
        """
        self.adapter = adapter
    
    def retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[List[FilterCondition]] = None
    ) -> List[FastMeSearchResult]:
        """
        执行检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            filters: 过滤条件列表
        
        Returns:
            FastMeSearchResult 列表
        """
        # 将 FilterCondition 列表转换为 Milvus 过滤表达式
        milvus_filter = None
        if filters:
            milvus_filter = self._to_milvus_filter(filters)
        
        # 执行相似度搜索
        results = self.adapter.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=milvus_filter
        )
        
        # 转换为 FastMeSearchResult
        return self._to_fastme_results(results)
    
    def _to_milvus_filter(
        self,
        conditions: List[FilterCondition]
    ) -> Optional[str]:
        """
        将 FilterCondition 列表转换为 Milvus 过滤表达式
        
        Milvus 使用类 SQL 表达式，如：
        - 单条件: device_id == "EQ001"
        - 多条件: device_id == "EQ001" and line_id == "LN01"
        
        Args:
            conditions: FilterCondition 列表
        
        Returns:
            Milvus 过滤表达式字符串
        """
        if not conditions:
            return None
        
        # 操作符映射
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
            
            # 处理字符串值
            if isinstance(value, str):
                expr_parts.append(f'{field} {op} "{value}"')
            # 处理列表值（$in, $nin）
            elif isinstance(value, list):
                value_str = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                expr_parts.append(f'{field} {op} [{value_str}]')
            # 处理数值值
            else:
                expr_parts.append(f'{field} {op} {value}')
        
        # 多条件使用 AND 连接
        return " and ".join(expr_parts)
    
    def supports_filter(self) -> bool:
        """支持过滤"""
        return True
```

**步骤 3：更新 VectorStoreFactory**

修改 `vector_stores/factory.py`，添加 Milvus 类型：

```python
# 在文件顶部添加导入
from vector_stores.milvus import MilvusAdapter

class VectorStoreFactory:
    @staticmethod
    def create(
        vector_store_type: str,
        embeddings: Embeddings,
        vector_store_config: Dict[str, Any]
    ) -> VectorStoreAdapter:
        """
        创建向量库适配器
        
        Args:
            vector_store_type: 向量库类型 ("chroma" | "faiss" | "milvus")
            embeddings: Embedding 函数
            vector_store_config: 配置字典
        
        Returns:
            VectorStoreAdapter 实例
        """
        if vector_store_type == "chroma":
            return ChromaAdapter(
                collection_name=vector_store_config.get("collection_name", "fastme_rag"),
                persist_directory=vector_store_config.get("persist_directory", "./data/chroma"),
                embedding_function=embeddings
            )
        
        elif vector_store_type == "faiss":
            return FAISSAdapter(
                embedding_function=embeddings,
                index_path=vector_store_config.get("index_path", "./data/faiss_index"),
                load_existing=True
            )
        
        # 新增：Milvus 向量库
        elif vector_store_type == "milvus":
            return MilvusAdapter(
                collection_name=vector_store_config.get("collection_name", "fastme_rag"),
                connection_args=vector_store_config.get("connection_args", {"host": "localhost", "port": "19530"}),
                embedding_function=embeddings
            )
        
        else:
            raise ValueError(f"不支持的向量库类型: {vector_store_type}")
```

**步骤 4：更新 RetrieverFactory**

修改 `retrievers/factory.py`，添加 Milvus 检索器：

```python
# 在文件顶部添加导入
from vector_stores.milvus_retriever import MilvusRetriever

class RetrieverFactory:
    @staticmethod
    def create(
        vector_store_type: str,
        vector_store_adapter: VectorStoreAdapter,
        scene_router: SceneRouter,
        retriever_config: Optional[Dict[str, Any]] = None
    ) -> BaseRetriever:
        """
        创建检索器
        
        Args:
            vector_store_type: 向量库类型
            vector_store_adapter: 向量库适配器
            scene_router: 场景路由器
            retriever_config: 检索器配置
        
        Returns:
            BaseRetriever 实例（被 SceneAwareRetriever 包装）
        """
        retriever_config = retriever_config or {}
        
        # 根据向量库类型创建对应检索器
        if vector_store_type == "chroma":
            from vector_stores.chroma_retriever import ChromaRetriever
            base_retriever = ChromaRetriever(adapter=vector_store_adapter)
        
        elif vector_store_type == "faiss":
            from vector_stores.faiss_retriever import FAISSRetriever
            post_filter_multiplier = retriever_config.get("post_filter_multiplier", 5)
            base_retriever = FAISSRetriever(
                adapter=vector_store_adapter,
                post_filter_multiplier=post_filter_multiplier
            )
        
        # 新增：Milvus 检索器
        elif vector_store_type == "milvus":
            base_retriever = MilvusRetriever(adapter=vector_store_adapter)
        
        else:
            raise ValueError(f"不支持的向量库类型: {vector_store_type}")
        
        # 包装为场景感知检索器
        from retrievers.scene_aware import SceneAwareRetriever
        return SceneAwareRetriever(base_retriever, scene_router)
```

**使用新向量库：**

```python
from app_factory import FastMeRAG

# 使用 Milvus 向量库
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

# 入库文档
rag.ingest("设备手册.pdf", doc_type="manual")

# 问答
result = rag.chat("设备操作步骤", scene="manual_query")
print(result["answer"])
```

#### 添加向量库的最佳实践

1. **元数据处理**：不同向量库对元数据类型支持不同，建议在 `add_documents()` 中调用 `sanitize_metadata()` 清理

2. **过滤条件转换**：每个向量库的过滤语法不同，需要在 Retriever 中实现转换逻辑

3. **延迟导入**：使用 `try/except` 或延迟导入处理依赖未安装的情况

4. **连接管理**：分布式向量库需要管理连接池，建议在适配器内部处理

5. **错误处理**：封装向量库特定异常，提供友好的错误信息

---

## 📁 项目结构

```
FASTME-RAG/
├── app_factory.py              # 主框架入口（FastMeRAG 类）
├── app.py                      # 使用示例
├── requirements.txt            # Python 依赖
├── README.md                   # 中文文档
├── README_EN.md                # 英文文档
│
├── core/                       # 核心模块
│   ├── models.py              # 数据模型（FastMeDocument, FastMeChunk, FastMeSearchResult）
│   ├── ingest_pipeline.py     # 文档入库流水线
│   ├── chat_pipeline.py       # 对话流水线
│   └── retriever.py           # 检索器抽象基类
│
├── vector_stores/              # 向量库模块
│   ├── __init__.py            # 导出 VectorStoreFactory, ChromaAdapter, FAISSAdapter
│   ├── base.py                # VectorStoreAdapter 抽象基类
│   ├── factory.py             # VectorStoreFactory（向量库工厂）
│   ├── chroma.py              # ChromaAdapter（Chroma 适配器）
│   ├── faiss.py               # FAISSAdapter（FAISS 适配器）
│   ├── chroma_retriever.py    # ChromaRetriever（Chroma 检索器）
│   └── faiss_retriever.py     # FAISSRetriever（FAISS 检索器）
│
├── retrievers/                 # 检索器模块
│   ├── __init__.py            # 导出 RetrieverFactory, SceneAwareRetriever
│   ├── factory.py             # RetrieverFactory（检索器工厂）
│   └── scene_aware.py         # SceneAwareRetriever（场景感知检索器）
│
├── splitters/                  # 文档拆解器
│   ├── base.py                # BaseSplitter（拆解器基类）
│   ├── log_splitter.py        # LogSplitter（日志拆解器）
│   ├── manual_splitter.py     # ManualSplitter（手册拆解器）
│   ├── business_splitter.py   # BusinessSplitter（工单拆解器）
│   └── sop_splitter.py        # SopSplitter（SOP 拆解器）
│
├── manufacturing/              # 制造业专属组件
│   └── metadata_extractor.py  # IndustrialMetadataExtractor（元数据抽取器）
│
├── routers/                    # 路由器
│   └── scene_router.py        # SceneRouter（场景路由器）
│
├── adapters/                   # 适配器
│   ├── __init__.py            # 导出 PromptAdapter, SimpleDocumentLoader
│   ├── prompt_adapter.py      # PromptAdapter（Prompt 适配器）
│   └── document_loader.py     # SimpleDocumentLoader（文档加载器）
│
├── config/                     # 配置文件
│   ├── scenes.yaml            # 场景配置
│   ├── metadata_rules.yaml    # 元数据抽取规则
│   ├── prompt_templates.yaml  # Prompt 模板
│   └── field_labels.yaml      # 字段标签（多语言）
│
├── examples/                   # 使用示例
│   ├── README.md              # 示例说明
│   ├── quickstart.py          # 快速开始
│   ├── scene_chat.py          # 场景问答示例
│   ├── custom_config.py       # 自定义配置示例
│   └── chat_stream_example.py # 流式输出示例
│
└── tests/                      # 单元测试
    ├── test_app_factory.py    # 主框架测试
    ├── test_splitters.py      # 拆解器测试
    ├── test_retrievers.py     # 检索器测试
    └── test_vector_stores.py  # 向量库测试
```

---

## 🧪 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_splitters.py -v
python -m pytest tests/test_retrievers.py -v

# 运行测试并显示覆盖率
python -m pytest tests/ -v --cov=. --cov-report=html
```

---

## 📝 完整示例

### 示例 1：故障诊断场景

```python
from app_factory import FastMeRAG

# 初始化
rag = FastMeRAG(
    chroma_collection="fault_diagnosis_collection"
)

# 入库故障日志
rag.ingest(
    file_path="./logs/fault_log_20240115.log",
    doc_type="log",
    extra_metadata={
        "project": "生产线A",
        "date": "2024-01-15"
    }
)

# 故障诊断问答
result = rag.chat(
    question="E001 设备最近有什么故障？",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}
)

print(f"回答：{result['answer']}")
print("\n溯源信息：")
for source in result["sources"]:
    print(f"  - [{source['timestamp']}] {source['fault_code']}: {source['preview'][:50]}...")
```

### 示例 2：手册查询场景

```python
from app_factory import FastMeRAG

# 初始化
rag = FastMeRAG(
    vector_store_type="faiss",
    vector_store_config={"index_path": "./data/manuals_faiss"}
)

# 批量入库手册
rag.batch_ingest(
    folder_path="./manuals",
    doc_type="manual"
)

# 手册查询问答
result = rag.chat(
    question="设备的启动步骤是什么？",
    scene="manual_query"
)

print(f"回答：{result['answer']}")
print("\n来源章节：")
for source in result["sources"]:
    print(f"  - 第 {source['chapter_num']} 章 {source['chapter_title']}")
```

### 示例 3：工单追溯场景

```python
from app_factory import FastMeRAG

# 初始化
rag = FastMeRAG()

# 入库工单
rag.ingest("./work_orders/wo_20240115.xlsx", doc_type="business")

# 工单追溯问答
result = rag.chat(
    question="工单 WO001 的质检结果是什么？",
    scene="work_order_trace",
    filters={"work_order_id": "WO001"}
)

print(f"回答：{result['answer']}")
for source in result["sources"]:
    print(f"  - 工单号: {source['work_order_id']}")
    print(f"  - 质检结果: {source['quality_result']}")
    print(f"  - 工位: {source['station']}")
```

### 示例 4：流式问答

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

### 示例 5：多语言支持

```python
from app_factory import FastMeRAG

# 使用中文界面
rag_zh = FastMeRAG(language="zh")
result_zh = rag_zh.chat("设备故障如何处理？", scene="fault_diagnosis")

# 切换为英文界面
rag_en = FastMeRAG(language="en")
result_en = rag_en.chat("How to handle device faults?", scene="fault_diagnosis")

# 动态切换语言
rag = FastMeRAG(language="zh")
rag.set_language("en")  # 切换为英文
result = rag.chat("Device maintenance steps?", scene="manual_query")
```

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - RAG 框架基础
- [ChromaDB](https://github.com/chroma-core/chroma) - 向量数据库
- [FAISS](https://github.com/facebookresearch/faiss) - 向量检索库
- [HuggingFace](https://huggingface.co/) - Embedding 模型

---

## 📬 联系方式

- 🐛 Issues: [GitHub Issues](https://github.com/happy-momo/FASTME-RAG/issues)

---

<div align="center">

**Made with ❤️ for Manufacturing Industry**

[⭐ Star this repo](https://github.com/happy-momo/FASTME-RAG) if you find it useful!

</div>
