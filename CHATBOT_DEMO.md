# 🚀 FastMe RAG Chatbot Demo

一个**开箱即用**的 RAG Chatbot 服务模板，用于演示 **FastMe RAG 框架**的可行性。

- **前端**：Vue 3 + Element Plus（流式对话 / 文档上传 / 多会话 / 场景选择 / 溯源展示）
- **后端**：FastAPI（`/api/chat`、`/api/chat/stream` SSE、`/api/ingest`、`/api/sessions`、`/api/scenes`）
- **框架**：FastMe RAG（**零改动**，仅作为只读依赖被后端引用）
- **部署**：`docker compose up` 一键启动

> 📌 本模板位于 `chatbot-demo` 分支。主分支（RAG 框架本身）不受影响。

---

## 1. 快速开始（Docker 一键栈）

### 1.1 前置条件

- Docker 20.10+（含 compose 插件）
- 一个 **OpenAI 兼容 `/v1` 端点**的 LLM（自备）：
  - 本地：[Ollama](https://ollama.com) / [vLLM](https://docs.vllm.ai) / [LM Studio] 等，或
  - 远程：智谱 / 通义 / 任意兼容服务

### 1.2 启动

```bash
# 1) 切到 demo 分支
git checkout chatbot-demo

# 2)（可选）配置你的 LLM 端点
cp backend/.env.example .env
#    编辑 .env，至少设置 FASTME_LLM_BASE_URL / FASTME_LLM_MODEL

# 3) 一键启动（首次会构建镜像并自动下载 embedding 模型，耗时取决于网络）
docker compose up --build

# 4) 访问
#    前端：http://localhost:8080
#    后端 API 文档：http://localhost:8000/docs
```

### 1.3 国内网络加速（可选）

```bash
# 在 .env 中启用 HuggingFace 镜像，加速 embedding 模型下载
HF_ENDPOINT=https://hf-mirror.com
```

---

## 2. 功能一览

| 功能 | 说明 |
|------|------|
| 💬 流式对话 | SSE 打字机效果，首字即出 |
| 📄 文档上传 | 拖拽上传 PDF/DOCX/TXT/LOG/MD，选择文档类型后入库 |
| 🧵 多会话记忆 | 新建/切换/删除会话，基于框架 `session_id` 记忆 |
| 🎯 场景选择 | fault_diagnosis / manual_query / work_order_trace / default |
| 🔍 溯源展示 | 回答附来源片段与相似度分数 |

---

## 3. 本地开发（不依赖 Docker）

```bash
# 后端（Python 3.10+）
PYTHONPATH=$PWD:$PWD/backend uvicorn app.main:app --reload --port 8000

# 前端（Node 18+）
cd frontend && npm install && npm run dev
# 打开 http://localhost:5173（vite 已代理 /api 到 :8000）
```

后端测试（无需真实 LLM / embedding，使用桩替代框架）：

```bash
PYTHONPATH=$PWD:$PWD/backend pytest backend/tests -q
```

---

## 4. 接入你自己的 LLM

在 `.env` 中配置三项即可：

| 变量 | 示例 | 说明 |
|------|------|------|
| `FASTME_LLM_BASE_URL` | `http://host.docker.internal:11434/v1` | OpenAI 兼容端点（容器内访问宿主机用 `host.docker.internal`） |
| `FASTME_LLM_API_KEY` | `sk-xxx` 或 `not-needed` | **必须非空**（openai 客户端要求）；无鉴权服务填占位值 `not-needed` |
| `FASTME_LLM_MODEL` | `qwen-plus` / `llama3.2` | 模型名 |

## 5. Embedding 策略（A2）

| 场景 | 做法 |
|------|------|
| 无本地模型（默认） | `EMBEDDING_MODEL=BAAI/bge-m3`，首次启动自动下载到卷 `rag-models` |
| 有本地模型 | 把模型放到卷内，`EMBEDDING_MODEL=/app/models/bge-m3` |
| 换模型 | 修改 `EMBEDDING_MODEL` 并删除旧卷 `docker compose down -v` 重灌 |

---

## 6. 架构与目录

```
chatbot-demo 分支（本分支）
├── backend/                  # FastAPI 服务
│   ├── app/
│   │   ├── main.py           # 应用入口 + 生命周期 + 异常处理
│   │   ├── api/              # ingest / chat / sessions / scenes / health
│   │   ├── core/             # rag 单例(锁) / streaming(SSE) / sessions 注册表
│   │   └── schemas/          # Pydantic 契约
│   ├── tests/                # API 契约测试（FakeFastMeRAG 桩）
│   ├── Dockerfile
│   └── .env.example
├── frontend/                 # Vue 3 + Vite + Element Plus
│   ├── src/views/            # ChatView / UploadView
│   ├── src/components/       # MessageBubble / SourcePanel / SceneSelector
│   ├── src/store/            # Pinia
│   ├── Dockerfile
│   └── nginx.conf            # 托管 dist + /api 反代
├── docker-compose.yml        # 一键栈
└── ...（框架源码，零改动）
```

## 7. 已知限制（demo 范围）

- **记忆存于内存**：重启进程后会话历史清空（框架本身的特性，demo 可接受）。
- **单实例串行**：后端用全局锁串行化入库与问答，适合 demo 级并发。
- **文档管理**：仅支持"上传入库"与"清空重建"，无按文档删除（框架未提供）。

---

## 8. 常见问题

**Q: 前端能打开但问答报错？**
A: 检查后端日志 `docker compose logs backend`；大概率是 LLM 端点未配置或不可达。确认 `/healthz` 中 `llm_reachable` 为 `true`。

**Q: 首次启动很慢 / 卡住？**
A: 首次需构建镜像 + 下载 embedding 模型（约数百 MB）。国内请设置 `HF_ENDPOINT=https://hf-mirror.com`。

**Q: 如何彻底重置？**
A: `docker compose down -v` 清空数据卷，重新 `docker compose up --build`。