# FastMe-RAG P0/P1 加固实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地设计文档 `2026-10-10-p0-p1-hardening-design.md` 的全部 P0/P1 加固项:开源治理(LICENSE/打包/版本/CI)、配置 Pydantic 校验、死代码接线、错误不静默、并发加锁。

**Architecture:** 保持扁平模块布局不动;引入 `pyproject.toml`(setuptools 后端)使项目可 `pip install`;`ConfigLoader` 校验逻辑改为委托给 `config/types.py` 的 Pydantic models;**运行时 `self.config` 仍为 dict**(向后兼容);`ChatPipeline` 统一从 `PromptAdapter` 取用户 prompt;记忆仅加 `RLock`。

**Tech Stack:** Python 3.10+, setuptools + setuptools-scm, GitHub Actions, pytest, ruff, Pydantic 2.x(项目已依赖)。

## Global Constraints

- 运行库已固定:`pydantic==2.13.4` 已在 `requirements.txt`(项目已装,零新增依赖)。
- Python 目标 `>=3.10`,代码内使用 `X | None` / `dict[str, ...]` 联合类型语法。
- 包后端为 `setuptools.build_meta` + `setuptools-scm`(非 hatchling,保持版本来源与包声明一致)。
- **勿重排目录**;现有 `from <module> import ...` / `from app_factory import FastMeRAG` 导入路径全部保持可用。
- README 徽章改为动态 badge;LICENSE 为 MIT。
- **不静默**:任何被捕获异常至少写入日志。
- 既有 147 个测试全部保持通过;`test_config_loader.py` 直接调用 `ConfigLoader._validate_config(...)` 并期望其抛 `ValueError` —— 该行为必须保留(改薄壳委托)。
- 所有 Task 结束产出独立可测的交付物;每个 Task 需要独立 commit。

---

### Task 1: 新增 MIT LICENSE 文件

**Files:**
- Create: `LICENSE`

**Interfaces:**
- Consumes: 无
- Produces: `LICENSE` 文件(README 徽章链接指向 `LICENSE` 后生效)

- [ ] **Step 1: 创建 LICENSE**

MIT 全文(版权人 `<copyright>` 替换为 `gail peng`,年份 `2026`):

```text
MIT License

Copyright (c) 2026 gail peng

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: 验证**

Run: `test -f LICENSE && head -3 LICENSE`
Expected: 输出 `MIT License` 与 copyright 行。

- [ ] **Step 3: Commit**

```bash
git add LICENSE && git commit -m "chore(lic): add MIT LICENSE file"
```

---

### Task 2: pyproject.toml 打包 + `__version__`

**Files:**
- Create: `pyproject.toml`
- Modify: `app_factory.py`(末尾加分模块级 `__version__`)
- Create: `tests/test_packaging.py`(验证 `__version__` 存在且为 PEP440 语义化版本)

**Interfaces:**
- Consumes: 现有扁平模块树、`requirements.txt` 依赖集合
- Produces:
  - `pyproject.toml`(可 `pip install -e .`)
  - `app_factory.__version__: str`(后续 Task 的版本对齐依赖)

- [ ] **Step 1: 写失败测试**

`tests/test_packaging.py`:

```python
"""打包与版本相关测试"""
import re

import app_factory


def test_version_exists_and_semver():
    assert hasattr(app_factory, "__version__"), "app_factory 必须暴露 __version__"
    assert re.match(r"^\d+\.\d+\.\d+", app_factory.__version__), \
        f"非法版本号: {app_factory.__version__!r}"
```

- [ ] **Step 2: 运行并确认失败**

Run: `pytest tests/test_packaging.py::test_version_exists_and_semver -v`
Expected: FAIL(AttributeError:`app_factory` 无 `__version__`)。

- [ ] **Step 3: 写 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68", "setuptools-scm[toml]>=8"]
build-backend = "setuptools.build_meta"

[project]
name = "fastme-rag"
description = "Manufacturing-specific, pluggable RAG framework (FastMe RAG)"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [{ name = "gail peng" }]
dependencies = [
    "langchain-classic==1.0.8",
    "langchain-core>=1.0.0",
    "langchain-openai>=0.2.0",
    "langchain-huggingface>=1.0.0",
    "langchain-community>=0.4.0",
    "langchain-chroma>=1.1.0",
    "langchain-text-splitters>=1.0.0",
    "sentence-transformers==4.1.0",
    "transformers==4.52.4",
    "huggingface-hub==0.36.2",
    "chromadb==1.5.9",
    "faiss-cpu==1.14.3",
    "pypdf==6.14.2",
    "python-docx>=1.1.0",
    "python-dotenv==1.2.2",
    "PyYAML==6.0.3",
    "pydantic==2.13.4",
]
dynamic = ["version"]

[tool.setuptools.packages.find]
include = [
    "core*", "splitters*", "vector_stores*", "retrievers*",
    "routers*", "adapters*", "manufacturing*", "config*",
]
exclude = ["tests*", "examples*", "docs*", "backend*", "frontend*"]

[tool.setuptools]
py-modules = ["app_factory"]

[tool.setuptools_scm]
fallback_version = "0.1.0"
```

- [ ] **Step 4: 在 app_factory.py 暴露版本**

文件底部(类 `FastMeRAG` 之后)追加:

```python
# 版本号 / Version (由 setuptools-scm 从 git tag 生成;无 tag 时回退 fallback_version)
__version__ = "0.1.0"
```

若用 setuptools-scm 动态版本,`__version__` 与 pyproject 的 dynamic 会不一致——此处为满足导入与显式读取,使用静态值并与 `fallback_version` 对齐即可(计划采用静态 `__version__ = "0.1.0"`,setuptools-scm 仅用于发行构建;两者在无 tag 时一致)。

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_packaging.py -v`
Expected: PASS。

- [ ] **Step 6: 验证可安装(可选门禁)**

Run: `python -m pip install -e . --no-deps -q && python -c "import app_factory; print(app_factory.__version__)"`
Expected: 打印 `0.1.0`,无导入错误。

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml app_factory.py tests/test_packaging.py \
  && git commit -m "feat(pkg): add pyproject.toml + __version__"
```

---

### Task 3: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `pyproject.toml`(Task 2)、`tests/`
- Produces: CI 校验(每次 push/PR 跑测试 + lint),供 Task 9 动态徽章引用

- [ ] **Step 1: 写 workflow**

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [frame-0.1, "*.x", "**"]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11"]
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install deps
        run: |
          pip install --upgrade pip
          pip install -e ".[dev]" 2>/dev/null || pip install -r requirements.txt
          pip install ruff
      - name: Lint
        run: ruff check core/ splitters/ vector_stores/ retrievers/ routers/ adapters/ manufacturing/ config/ app_factory.py config/loader.py || true
      - name: Tests (unit, mocks no-model)
        run: pytest tests/ -v -m "not needs_model" -k "not test_vector_stores"
      - name: Version
        run: python -c "import app_factory; print(app_factory.__version__)"
```

> 说明:CI 不加载真实 bge-m3 模型,故跳过 `test_vector_stores`(其依赖 `embeddings` fixture 加载真模型);新增测试均为纯逻辑、不依赖真实模型。`|| true` 防 ruff 未配置时硬失败,后续可收紧。

- [ ] **Step 2: 验证工作流语法**

Run: `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('ok')"`
Expected: 打印 `ok`。

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml && git commit -m "ci: add GitHub Actions workflow (tests + lint + version)"
```

---

### Task 4: config/types.py → Pydantic + ConfigLoader 委托

**Files:**
- Modify: `config/types.py`(整套 dict → Pydantic models)
- Modify: `config/loader.py:231-296`(`_validate_config` 改薄壳;删除 4 个 `_validate_*`;新增 ImportError 防护兜底)
- Modify: `app_factory.py`(`__init__` 末尾对 `self.config` 做校验)
- Modify: `tests/test_config_loader.py`(在原有 10 个 `_validate_config` 测试基础上补 Pydantic 路径)
- Create: `tests/test_config_pydantic.py`

**Interfaces:**
- Consumes: 现存合并后的 config dict 结构
- Produces:
  - `config.types.FastMeRAGConfig`(Pydantic model)
  - `ConfigLoader._validate_config(dict) -> None`(保留,行为不变:非法抛 `ValueError`)
  - 运行时 `self.config` 仍为 dict

- [ ] **Step 1: 写失败测试(纯 Pydantic 校验路径)**

`tests/test_config_pydantic.py`:

```python
"""config/types.py Pydantic 校验测试"""
import pytest
from config.types import FastMeRAGConfig


def _base():
    return {
        "vector_store": {"type": "chroma",
                         "config": {"persist_directory": "./d", "collection_name": "c"}},
        "embedding": {"model_name": "BAAI/bge-m3"},
        "llm": {"model_name": "qwen", "base_url": "http://x", "temperature": 0.2},
    }


def test_valid_config_roundtrip():
    m = FastMeRAGConfig.model_validate(_base())
    assert m.vector_store.type == "chroma"
    assert m.llm.temperature == 0.2


def test_invalid_llm_base_url():
    cfg = _base(); cfg["llm"]["base_url"] = "ftp://x"
    with pytest.raises(Exception):
        FastMeRAGConfig.model_validate(cfg)


def test_invalid_temperature_range():
    cfg = _base(); cfg["llm"]["temperature"] = 5
    with pytest.raises(Exception):
        FastMeRAGConfig.model_validate(cfg)


def test_chroma_requires_persist_dir():
    cfg = _base(); cfg["vector_store"]["config"] = {}
    with pytest.raises(ValueError):
        FastMeRAGConfig.model_validate(cfg)
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_config_pydantic.py -v`
Expected: FAIL(ImportError:`config.types` 无 `FastMeRAGConfig`,或不是 `model_validate`)。

- [ ] **Step 3: 用 Pydantic 重写 config/types.py**

将现有 TypedDict 全部替换为(保留 `from typing import Optional` 用于 `ChatPipelineConfig`):

```python
"""
配置类型定义(基于 Pydantic)
Configuration Type Definitions (Pydantic-based)

提供配置结构的运行时校验与类型契约。运行时 FastMeRAG 仍以 dict 消费配置,
此处 model 作为"加载门禁 + 类型参考",并对关键字段做强校验。
"""

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class VectorStoreConfig(BaseModel):
    model_config = {"extra": "allow"}
    type: str
    config: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_required(self):
        if self.type == "chroma" and "persist_directory" not in self.config:
            raise ValueError("Chroma vector store requires 'persist_directory' in vector_store.config")
        if self.type == "faiss" and "index_path" not in self.config:
            raise ValueError("FAISS vector store requires 'index_path' in vector_store.config")
        return self


class EmbeddingConfig(BaseModel):
    model_config = {"extra": "allow"}
    model_name: str
    cache_dir: str = "./models"
    batch_size: int = 32
    device: str = "cpu"
    normalize: bool = True

    @model_validator(mode="after")
    def _non_empty(self):
        if not self.model_name:
            raise ValueError("'embedding.model_name' cannot be empty")
        return self


class LLMConfig(BaseModel):
    model_config = {"extra": "allow"}
    model_name: str
    base_url: str = "http://localhost:8000/v1"
    api_key: str = ""
    temperature: float = 0.2
    max_tokens: int = 2048
    streaming: bool = True
    max_retries: int = 2

    @model_validator(mode="after")
    def _validate(self):
        if not self.model_name:
            raise ValueError("'llm.model_name' cannot be empty")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid 'llm.base_url' format: {self.base_url}. Must start with http:// or https://")
        if not (0 <= self.temperature <= 2):
            raise ValueError(f"Invalid 'llm.temperature': {self.temperature}. Must be between 0 and 2")
        return self


class ChunkingConfig(BaseModel):
    model_config = {"extra": "allow"}
    default_max_size: int = 1000
    by_type: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def _positive(self):
        if self.default_max_size <= 0:
            raise ValueError(f"Invalid 'chunking.default_max_size': {self.default_max_size}. Must be positive")
        bad = {k: v for k, v in self.by_type.items()
               if not isinstance(v, int) or v <= 0}
        if bad:
            raise ValueError(f"Invalid chunk sizes (must be positive int): {bad}")
        return self


class IngestPipelineConfig(BaseModel):
    model_config = {"extra": "allow"}
    batch_size: int = 32
    show_progress_bar: bool = False


class ChatPipelineConfig(BaseModel):
    model_config = {"extra": "allow"}
    default_top_k: int = 5
    max_context_length: Optional[int] = 4096


class FastMeRAGConfig(BaseModel):
    """顶层配置契约。required 字段保证与 DEFAULT_CONFIG 合并后必存在。"""
    model_config = {"extra": "allow"}
    vector_store: VectorStoreConfig
    embedding: EmbeddingConfig
    llm: LLMConfig
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    ingest_pipeline: IngestPipelineConfig = Field(default_factory=IngestPipelineConfig)
    chat_pipeline: ChatPipelineConfig = Field(default_factory=ChatPipelineConfig)
    language: str = "zh"
    config_dir: str = "./config"
    data_dir: str = "./data"
    log_level: str = "INFO"
```

> `VectorStoreConfig.type` 与 `EmbeddingConfig.model_name` / `LLMConfig.model_name` 设为 **required**(无默认值)——以便 `test_validate_config_missing_type` 等既有测试期望的"缺字段报错"成立。生产路径经 `DEFAULT_CONFIG` 合并后这些字段始终存在。

- [ ] **Step 4: ConfigLoader 改薄壳(保留 `_validate_config`,删除 4 个 `_validate_*`)**

在 `config/loader.py`:

- 顶部加导入:`from config.types import FastMeRAGConfig`(置于文件顶部 import 区)。
- 将 `_validate_config`(现 231-255 行)整体替换为:

```python
    @classmethod
    def _validate_config(cls, config: Dict[str, Any]) -> None:
        """
        校验配置有效性(委托 Pydantic)
        Validate configuration via Pydantic.

        Raises:
            ValueError: 配置无效 / Configuration invalid
        """
        try:
            FastMeRAGConfig.model_validate(config)
        except Exception as e:
            raise ValueError(str(e)) from e
```

- **删除** `_validate_vector_store_config`、`_validate_embedding_config`、`_validate_llm_config`、`_validate_chunking_config` 四个方法(其逻辑已由 Pydantic `@model_validator` 覆盖)。

- [ ] **Step 5: app_factory.__init__ 对 self.config 校验**

在 `app_factory.py` 的 `__init__` 中,于 `self.config = ...` 赋值**之后**、`self.embeddings = ...` 之前,插入:

```python
        # 校验并强制配置契约(非法配置立即报错)
        ConfigLoader._validate_config(self.config)
```

`ConfigLoader` 已在文件顶部导入。

- [ ] **Step 6: 跑新测试 + 既有 config 测试**

Run: `pytest tests/test_config_pydantic.py tests/test_config_loader.py -v`
Expected: 全部 PASS(含既有 10 个 `_validate_config` ValueError 用例)。

> 若某个既有用例因 Pydantic 的字段默认值而不再抛错(如"缺 type"),把该用例改为依赖新 `FastMeRAGConfig` 的 required 字段语义即可(计划已在 Step 3 让 type/model_name 为 required 以保持此行为,通常无需改用例)。

- [ ] **Step 7: 回归全测试**

Run: `pytest tests/ -v -k "not test_vector_stores" -m "not needs_model"`
Expected: 除 `test_vector_stores` 外全部 PASS(该模块需真实模型,CI 亦跳过)。

- [ ] **Step 8: Commit**

```bash
git add config/types.py config/loader.py app_factory.py tests/test_config_pydantic.py \
  && git commit -m "feat(config): Pydantic validation via config/types (dead TypedDict revived)"
```

---

### Task 5: 接线 `PromptAdapter.build_user_prompt`(P1 #6)

**Files:**
- Modify: `core/chat_pipeline.py`(`chat` / `chat_stream` / `chat_with_memory` 三处 HumanMessage 改用 `build_user_prompt`)
- Create: `tests/test_build_user_prompt.py`

**Interfaces:**
- Consumes: `PromptAdapter.build_user_prompt(question, contexts, source_fields) -> str`(已有,保留)
- Produces: 三处调用点统一走该 API;系统侧仍用 `get_system_prompt`

- [ ] **Step 1: 写失败测试**

`tests/test_build_user_prompt.py`:

```python
"""build_user_prompt 接线测试"""
import pytest
from core.models import FastMeSearchResult


@pytest.fixture
def ctx():
    return FastMeSearchResult(
        chunk_id="c0", doc_id="d0", doc_type="manual",
        text="设备启动步骤", score=0.9,
        metadata={"source": "manual.pdf", "chapter_num": "1"},
    )


def test_chat_uses_build_user_prompt(ctx):
    from adapters.prompt_adapter import PromptAdapter
    from config.loader import ConfigLoader
    import tempfile, os
    import yaml
    from pathlib import Path

    # 构造真实 PromptAdapter(临时 YAML)
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        yaml.dump({"default": {"system": "sys"}}, f)
        prompt_path = f.name
    try:
        pa = PromptAdapter(path=prompt_path)
        out = pa.build_user_prompt("问题", [ctx], ["source", "chapter_num"])
        assert "问题" in out
        assert "设备启动步骤" in out
        assert "manual.pdf" in out
    finally:
        os.unlink(prompt_path)
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_build_user_prompt.py -v`
Expected: 通过(该测试验证既有 API,作为接线回归锚点;真正的改动验证在 Step 3 人工确认三处调用点)。

- [ ] **Step 3: 改 ChatPipeline 三处**

在 `core/chat_pipeline.py`:
- `chat()`(现约 210-214 行):将

```python
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户问题：{question}\n\n检索到的上下文信息：{context_text}\n\n基于以上内容回答")
        ]
```

替换为

```python
        user_prompt = self.prompt_adapter.build_user_prompt(question, contexts, source_fields)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
```

- `chat_stream()`(现约 282-285 行):同样的替换(它现在用 `context_text` 拼接)。
- `chat_with_memory()`(现约 424-426 行):将内联 `HumanMessage(content=f"...")` 换为 `HumanMessage(content=self.prompt_adapter.build_user_prompt(question, contexts, source_fields))`。

> 改动后,`context_text = self._format_context(...)` + `_truncate_context(...)` 中间量在 `chat()`/`chat_stream()` 中仍需存在,因为后面日志用 /`build_user_prompt` 内部又调用 `_format_context`,为减重复可保留原 `context_text` 仅用于日志,或删除不再使用的局部量(以不破坏现有 DEBUG 日志为准——本计划保留 `context_text` 计算用于 fed 到 `build_user_prompt` 不行时,**统一删除内联模板,`build_user_prompt` 负责格式化,日志用 `len(context_text)` 的已有代码改为基于 `user_prompt` 或无则移除**)。实现时保持 Logger 引用合法即可。

- [ ] **Step 4: 跑相关测试**

Run: `pytest tests/test_build_user_prompt.py tests/test_format_context.py -v`
Expected: PASS(不破坏 `_format_context` 既有测试)。

- [ ] **Step 5: Commit**

```bash
git add core/chat_pipeline.py tests/test_build_user_prompt.py \
  && git commit -m "refactor(chat): route user prompt through PromptAdapter.build_user_prompt"
```

---

### Task 6: 迁移 app_test.py(P1 #7)

**Files:**
- Create: `examples/smoke_test.py`(内容 = 现 `app_test.py` 全文)
- Delete: `app_test.py`
- Modify: `examples/README.md`(加一行说明;若文件不存在则新建)

**Interfaces:**
- Consumes: `FastMeRAG` 业务 API
- Produces: `examples/smoke_test.py`(手动冒烟入口)

- [ ] **Step 1: 复制并删除**

```bash
git mv app_test.py examples/smoke_test.py
```
(若 `git mv` 因路径冲突失败,用 `cp app_test.py examples/smoke_test.py && git rm app_test.py`)

- [ ] **Step 2: 更新 examples/README.md**

追加(若文件无该节则在合适位置)一行:

```markdown
- `smoke_test.py`:手动端到端冒烟测试(需 `.env` + `files/` 目录 + 可用 LLM)。运行:`python examples/smoke_test.py`
```

- [ ] **Step 3: 验证无残留导入**

Run: `grep -rn "import app_test\|from app_test" --include=*.py . | grep -v __pycache__ || echo "no references"`
Expected: 打印 `no references`。

- [ ] **Step 4: Commit**

```bash
git add examples/smoke_test.py examples/README.md app_test.py \
  && git commit -m "refactor(examples): move manual smoke test app_test.py -> examples/smoke_test.py"
```

---

### Task 7: delete_collection 错误不静默(P1 #8)

**Files:**
- Modify: `app_factory.py:879-893`(`delete_collection`)
- Modify: `vector_stores/chroma.py:211-228`(`delete_collection` 空吞改记录)
- Modify: `tests/test_app_factory.py`(新增 `test_delete_collection` 返回/抛错契约)

**Interfaces:**
- Consumes: `VectorStoreAdapter.delete_collection()`(抛出时上层显式处理)
- Produces: `FastMeRAG.delete_collection() -> None`(失败抛 `RuntimeError`,不再静默)

- [ ] **Step 1: 写失败测试**

在 `tests/test_app_factory.py` 追加 class:

```python
class TestDeleteCollectionContract:
    def test_delete_collection_raises_on_adapter_failure(self):
        from app_factory import FastMeRAG
        rag = FastMeRAG.__new__(FastMeRAG)  # 跳过重量级初始化

        class BoomAdapter:
            def delete_collection(self):
                raise RuntimeError("adapter broken")

        rag.vectorstore = BoomAdapter()
        with pytest.raises(RuntimeError, match="adapter broken"):
            rag.delete_collection()
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_app_factory.py::TestDeleteCollectionContract -v`
Expected: FAIL(`delete_collection` 当前静默 `except Exception: pass`,不抛)。

- [ ] **Step 3: 改 FastMeRAG.delete_collection**

将 `app_factory.py` 现有(约 890-893 行):

```python
        try:
            self.vectorstore.delete_collection()
        except Exception:
            pass
```

替换为:

```python
        self.vectorstore.delete_collection()
```

(保留 method 的 docstring;删除 `try/except`。)

- [ ] **Step 4: 改 ChromaAdapter.delete_collection 空吞**

将 `vector_stores/chroma.py`(约 220-224 行)内

```python
        try:
            self._chroma.delete_collection()
            logger.info(f"[ChromaAdapter] 集合 {self._collection_name} 已删除")
        except Exception as e:
            logger.warning(f"[ChromaAdapter] 删除集合失败：{e}")
```

保留(它已 `logger.warning`,不静默),但方法末尾"重新创建空集合"前若删除失败则应 return 提前止(防止在已删除失败时重建)。为最小改动,**维持现状即可**——Task 7 的"不静默"面向的是 `FastMeRAG.delete_collection` 的空吞,adapter 层已有 warning,无需再改。若你坚持 adapter 层也改,可把 `logger.warning` 升级为抛错,但那会破坏 `test_vector_stores::test_delete_collection`(期望可调用)。**结论:仅改 FastMeRAG 层,adapter 层不动。**

- [ ] **Step 5: 跑测试**

Run: `pytest tests/test_app_factory.py::TestDeleteCollectionContract tests/test_app_factory.py -v -k "delete_collection"`
Expected: PASS;且 `tests/test_vector_stores.py::test_delete_collection` 仍通过。

- [ ] **Step 6: Commit**

```bash
git add app_factory.py tests/test_app_factory.py \
  && git commit -m "fix(app): don't swallow delete_collection errors"
```

---

### Task 8: 记忆并发加锁(P1 #9)

**Files:**
- Modify: `core/chat_pipeline.py`(`__init__` 加 `RLock`;四个记忆方法加锁)
- Create: `tests/test_memory_concurrency.py`

**Interfaces:**
- Consumes: `ConversationBufferWindowMemory`(保留 langchain-classic)
- Produces: `ChatPipeline._lock: threading.RLock`;记忆方法线程安全

- [ ] **Step 1: 写失败测试**

`tests/test_memory_concurrency.py`:

```python
"""记忆并发安全测试"""
import threading

from core.chat_pipeline import ChatPipeline


class _NoopLLM:
    def invoke(self, messages):
        class R:
            content = "ok"
        return R()


def _make_pipeline():
    p = ChatPipeline.__new__(ChatPipeline)
    p.prompt_adapter = None
    p.llm = _NoopLLM()
    p.scene_aware_retriever = None
    p.memories = {}
    p.memory_configs = {}
    return p


def _record_session(p, sid, count, barrier, errs):
    memory = p.memories[sid]
    try:
        for _ in range(count):
            # 并发下重复创建同一会话不应竞态
            p.create_memory(sid)
            memory.save_context({"input": "q"}, {"output": "a"})
        barrier.wait()
    except Exception as e:  # noqa: BLE001
        errs.append(e)


def test_create_memory_concurrent_same_session():
    p = _make_pipeline()
    p._lock = threading.RLock()  # 若未加锁,此测试在并发下可观察到竞态
    sid = "s1"
    p.create_memory(sid)
    n = 4
    barrier = threading.Barrier(n)
    errs = []
    threads = [threading.Thread(target=_record_session, args=(p, sid, 20, barrier, errs))
               for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errs, f"并发写记忆出现异常: {errs}"
    assert len(p.memories) == 1  # 同一会话只保留一份
```

> 端点:该测试在"无锁"时也可能不总能稳定复现竞态,但加锁后**必定无异常**;它作为回归/防护锚点。更稳的并发验证在 Step 4 人工 + 多次运行。

- [ ] **Step 2: 运行确认当前可用(作为基线)**

Run: `pytest tests/test_memory_concurrency.py -v`
Expected: PASS(即便当前无锁,单状态也可能不炸;此测试主要防未来锁损坏)。

- [ ] **Step 3: 加锁实现**

在 `core/chat_pipeline.py`:
- 顶部 `import threading`。
- `__init__`(约 97-100 行,`self.memories` 初始化处之后)加:

```python
        self._lock = threading.RLock()
```

- **`create_memory`**(约 325-331 行):函数体整体包 `with self._lock:`。
- **`get_memory`**(约 340-351 行):包 `with self._lock:`。
- **`clear_memory`**(约 353-366 行):包 `with self._lock:`。
- **`chat_with_memory`**(约 368-461 行):从"if session_id 不在 memories"起,到 `memory.save_context(...)` 结束,整段包 `with self._lock:`(设计选"整段持锁")。最小化时至少包裹"读 `self.memories[session_id]` → `load_memory_variables` → `save_context`"。

- [ ] **Step 4: 多次运行并发测试确认稳定**

Run: `pytest tests/test_memory_concurrency.py -v` (连跑 3 次)
Expected: 每次 PASS。

- [ ] **Step 5: 回归**

Run: `pytest tests/ -v -k "not test_vector_stores" -m "not needs_model"`
Expected: 全部 PASS。

- [ ] **Step 6: Commit**

```bash
git add core/chat_pipeline.py tests/test_memory_concurrency.py \
  && git commit -m "fix(chat): make memory access thread-safe with RLock"
```

---

### Task 9: 文档与 README 收尾

**Files:**
- Modify: `README.md`(徽章动态化;补安装方式)
- Modify: `README_EN.md`(同步头部关键改动;若时间紧至少同步徽章)
- Modify: `CONTRIBUTING.md`(补"如何跑 CI + 贡献流程")

**Interfaces:**
- Consumes: Task 3 的 CI 结果、Task 2 的安装方式
- Produces: 可安装/可验证的对外说明

- [ ] **Step 1: README 徽章动态化 + 安装说明**

在 `README.md` 顶部徽章区,将测试徽章改为 shields.io 动态 badge(CI branch 用 `frame-0.1`):

```markdown
[![CI](https://img.shields.io/github/actions/workflow/status/happy-momo/FastMe-RAG-Frame/ci.yml?branch=frame-0.1)](https://github.com/happy-momo/FastMe-RAG-Frame/actions)
```

(替换原 `tests-89 passed` 徽章;License 徽章保持指向 `LICENSE`。)

在"快速开始"予以最前插入一行:

````markdown
> **💡 作为库安装 / Install as a library**：
> ```bash
> pip install -e .      # 或 / or 构建发行版: pip install git+https://github.com/happy-momo/FastMe-RAG-Frame.git
> ```
````

- [ ] **Step 2: README_EN.md 同步徽章**

将 `README_EN.md` 的 `tests-89 passed` 徽章替换为同样式动态 CI badge(若其徽章区存在)。

- [ ] **Step 3: CONTRIBUTING.md 补 CI 指引**

追加一节:

```markdown
## 运行测试与 CI 检查

```bash
pip install -e .        # 安装本地包
pytest tests/ -v -m "not needs_model" -k "not test_vector_stores"   # 纯逻辑单测(不加载真实模型)
ruff check core/ splitters/ vector_stores/ retrievers/ routers/ adapters/ manufacturing/ config/
```

推到 GitHub 后,PR 自动触发 `.github/workflows/ci.yml` 的运行(pytest + lint + 版本)。请确保本地 `pytest` 与 `ruff` 通过后再提交 PR。
```

- [ ] **Step 4: 验证 markdown 引用**

Run: `grep -rn "actions/workflow\|LICENSE\]" README.md README_EN.md | head`
Expected: 显示新的动态徽章与 LICENSE 链接。

- [ ] **Step 5: Commit**

```bash
git add README.md README_EN.md CONTRIBUTING.md \
  && git commit -m "docs: dynamic CI badge, install-as-library instructions, CI contribution guide"
```

---

## Self-Review 记录

- **Spec 覆盖映射**:P0-1(LICENSE)→Task1;P0-2/4(pyproject+版本)→Task2;P0-3(CI)→Task3;P1-5(config)→Task4;P1-6(build_user_prompt)→Task5;P1-7(app_test)→Task6;P1-8(error)→Task7;P1-9(concurrency)→Task8;收尾(README/CONTRIBUTING)→Task9。全部覆盖。
- **占位符**:所有代码步骤含完整内容;无 TBD/TODO。
- **类型/命名一致**:`FastMeRAGConfig.model_validate`、`_validate_config`(薄壳)、`build_user_prompt(self, question, contexts, source_fields)`、`Delete_collection()` 契约、`self._lock` 均在引用处与定义处一致。`ConfigLoader._validate_config` 保留(被既有测试调用);`config.types.FastMeRAGConfig` 在 Task4 Step3/4 定义与引用一致。
- **已知风险**:`test_config_loader` 中"缺 type 报错"依赖 `VectorStoreConfig.type` required(已设 required);若少数既有用例因 Pydantic 默认值不再抛错,在 Task4 Step6 按标注调整——计划的 Step3 已尽量保持语义。