# FastMe-RAG P0/P1 加固设计文档

> 日期:2026-10-10
> 状态:已确认(待生成实现计划)
> 范围:**全部 P0 + P1**;本次只产出评估与实现计划,**不写代码**

## 概述

本设计针对 FastMe RAG 框架作为"亮点项目 / 开源项目"的 P0(default: 开源硬伤)与 P1(交付质量与正确性)问题,给出统一的改进方向与修复方法。目标是:项目可被 `pip install`、可被 CI 验证、配置有运行时校验、无死代码、错误不静默、并发安全。

### 关键选型(用户确认)
- config/types.py 处理:**A. 改 Pydantic**(项目已依赖 pydantic 2.13.4,零新增)
- 多轮记忆处理:**C. 只加锁不动记忆**(保留 `langchain-classic` 的 `ConversationBufferWindowMemory`,仅补线程锁)
- 包布局:**不重排目录**,把现有顶层包声明为待安装包(最小改动)
- delete_collection 契约:**抛异常**(不静默)
- 锁粒度:**整段持锁**(简单一致)
- app_test.py 迁移目标:**`examples/smoke_test.py`**

---

## P0 治理与打包

### P0-1 缺失 LICENSE(法律硬伤)
**问题**:README 标 MIT、有 MIT 徽章,但仓库根无 `LICENSE` 文件。MIT 缺少文件时无法合法引用/分发。
**修复**:新增 `LICENSE`(MIT 全文),版权人取自 git config(`gail peng`);README 徽章链接指向该文件。

### P0-2 无法 pip 安装 —— 缺 pyproject
**问题**:无 `pyproject.toml`,用户只能 `git clone`,无法 `pip install`,无法发布 PyPI。
**修复**:
- 新增 `pyproject.toml`,`name = "fastme-rag"`,`build-backend = "setuptools.build_meta"`。
  - **技术选型一致性**:选择 `setuptools` 后端(而非 hatchling),因其原生支持 `setuptools-scm` 版本来源,且 `[tool.setuptools] packages` 声明顶层包最直观;仅靠 setuptools + `[tool.setuptools_scm]` 即完成版本动态化,无需额外插件。
- **包布局(最小改动)**:项目为扁平模块(`core/ splitters/ vector_stores/ retrievers/ routers/ adapters/ manufacturing/ config/` + 根级 `app_factory.py`)。不重排目录,在 `[tool.setuptools]` 中把上述顶层包 + `app_factory` 模块声明为待安装包,使安装后 `from app_factory import FastMeRAG` 仍可用。
- 将 `requirements.txt` 内容并入 `[project] dependencies`,保证 `pip install` 携带运行时依赖。
- 版本号走 `dynamic = ["version"]` + `setuptools-scm`(从 git tag 生成),并在 `app_factory` 暴露 `__version__`。

### P0-3 无 CI/CD,测试徽章失效
**问题**:无 `.github/workflows`;README 徽章写死 "89 passed",实际 147 个测试函数,已过时且无法自证。
**修复**:
- 新增 `.github/workflows/ci.yml`:`pytest tests/ -v`(embedding 用 mock fixture,避免联网下载)、`ruff check .`、可选 `mypy core/`。
- README 徽章改为 shields.io 动态 badge 指向 CI 结果。

### P0-4 缺版本管理
**问题**:无 `__version__`,无法在依赖/Release 对齐版本。
**修复**:随 P0-2 一并落地(`setuptools-scm` + 暴露 `__version__`)。

---

## P1 交付质量与正确性

### P1-5 config/types.py 死代码 → Pydantic
**问题**:`config/types.py` 的整套 `TypedDict` 生产零引用;配置以裸 dict 加载、无运行时校验。
**修复(方案 A:改 Pydantic)**:
- 用 Pydantic models 替换全部 TypedDict,镜像现有结构(`VectorStoreConfig` / `EmbeddingConfig` / `LLMConfig` / `ChunkingConfig` / `IngestPipelineConfig` / `ChatPipelineConfig` / `FastMeRAGConfig`)。
- `@field_validator` 落地现有手动校验(base_url 以 http(s) 开头、`0≤temperature≤2`、chunk 大小为正整数、缺 `persist_directory`/`index_path` 报错),**替代并删除** `ConfigLoader` 的 4 个手动校验方法。
- **集成点**:`ConfigLoader.load()` 及 `FastMeRAG.__init__` 合并出 `self.config` 后,用 `FastMeRAGConfig.model_validate(merged)` 作门禁;非法立即抛清晰错误。
- **运行时仍返回 dict**:`self.config` 保持 dict(`self.config.get(...)` 与 `_deep_merge` 全兼容);model 作类型契约供 IDE 补全,可选暴露 `rag.config_model`。
- **宽松模型 + 关键强校验**:env override 会注入 `config_dir`/`data_dir` 等非核心字段,model 设 `extra="allow"`,仅对关键字段强校验。
- 依赖:项目已依赖 `pydantic==2.13.4`,零新增。

### P1-6 build_user_prompt 死代码
**问题**:`PromptAdapter.build_user_prompt()` 零调用;`chat_pipeline` 三处(`chat`/`chat_stream`/`chat_with_memory`)内联手写 `HumanMessage`,逻辑重复分叉。
**修复**:
- 三处改用 `self.prompt_adapter.build_user_prompt(question, contexts, source_fields)` 生成用户侧内容,与系统侧 `get_system_prompt` 对齐。
- `_format_context` 保留在 `prompt_adapter` 单一来源,删除 `chat_pipeline` 内重复手写模板。
- 验证:补断言 `build_user_prompt` 输出(片段标号、字段标签、question 位置)的单测。

### P1-7 app_test.py 误放仓库根
**问题**:手动冒烟脚本放根目录,污染包结构、暗示为测试入口。
**修复**:迁移至 `examples/smoke_test.py`;删除根目录脚本;更新 `examples/README.md`;不进 pytest 默认 suites(依赖真实 embedding/LLM/files,已有 `test_fixes_p0_p1` 覆盖其逻辑的 mock 版)。
**范围控制**:其他 `examples/*` 脚本本次不动,避免蔓延。

### P1-8 错误处理过粗
**问题**:`FastMeRAG.delete_collection()` 用 `try/except: pass` 吞异常;`ChromaAdapter.delete_collection()` 空吞。
**修复**:`delete_collection()` 去掉空吞,失败**抛异常**;全库扫描 `except: pass`,按场景改为 `logger.warning/error`,保证不静默(至少落日志)。

### P1-9 线程安全(方案 C:只加锁不动记忆)
**问题**:`memories`/`memory_configs` 为普通 dict,`chat_with_memory` 并发读写不安全(chatbot-demo 用线程锁串行即是绕开此缺口)。
**修复**:
- `ChatPipeline` 加 `threading.RLock(self._lock)`。
- 对记忆全部读写点(`create_memory`/`get_memory`/`clear_memory`/`chat_with_memory`)原子化。
- **锁粒度:整段持锁**——`chat_with_memory` 内"检索 → 读历史 → 构建消息 → LLM 调用 → save_context"整段持锁,保证 `save_context` 与消息构建一致。
- 验证:并发单测(多线程同会话,断言消息数不脏、无异常)。

---

## 收尾(合并进计划)
- `app_factory.py` 暴露 `__version__`。
- README 顶部补 `pip install -e .` 安装方式。
- `CONTRIBUTING.md` 补"如何贡献 + 跑 CI"指引。

---

## 测试策略
- 单元:config 校验(非法配置抛错)、`build_user_prompt` 输出、delete_collection 抛异常、并发记忆。
- CI:mock embedding 跑全 `tests/` + ruff + 可选 mypy。
- 既有 147 测试保持通过,不引入破坏。

## 范围外(不纳入本次)
- P2/P3(混合检索、reranker、缓存、遥测、双语文档站、命中/召回 benchmark 等)仅记录,不实现。
- 不重排包目录、不移除 langchain-classic、不改 memory 实现。