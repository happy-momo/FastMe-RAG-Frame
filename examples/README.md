# FastMe RAG 示例代码

本目录包含 FastMe RAG 框架的使用示例，帮助你快速上手。

## 示例列表

### 1. quickstart.py - 快速开始
最适合第一次使用的用户，演示完整流程：
- 初始化 RAG 系统
- 查看支持的场景和文档类型
- 文档入库（单个文件）
- 场景化问答
- 查看溯源信息

**运行**：
```bash
python examples/quickstart.py
```

### 2. scene_chat.py - 场景化问答
演示 4 种预置场景的使用方法：
- `fault_diagnosis` - 故障诊断（基于运维日志）
- `manual_query` - 设备手册查询
- `work_order_trace` - 工单追溯
- `default` - 默认问答

**运行**：
```bash
python examples/scene_chat.py
```

### 3. custom_config.py - 自定义配置
演示如何动态扩展框架：
- 添加新场景
- 添加元数据抽取规则
- 更新场景配置
- 批量文件夹入库
- 带审核的入库流程

**运行**：
```bash
python examples/custom_config.py
```

### 4. config_usage.py - 配置化使用（新增）
演示如何通过配置参数调整系统行为：
- `chunk_max_size`: 控制 chunk 最大尺寸
- `ingest_batch_size`: 控制入库分批大小
- `embedding_batch_size`: 控制 Embedding 批量
- `show_progress_bar`: 控制进度条显示

包含 7 个场景化配置示例：
- 默认配置（快速开始）
- 内存受限环境
- 高性能环境
- API 服务配置
- 日志分析专用
- 设备手册专用
- 混合配置（高级用法）

**运行**：
```bash
python examples/config_usage.py
```

## 前置准备

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置 LLM_BASE_URL、LLM_API_KEY 等
   ```

3. **准备测试数据**
   将你的文档放入 `samples/` 目录，或修改示例中的文件路径。

## 示例代码结构

每个示例文件都包含详细注释，你可以：

1. **直接运行** - 查看效果
2. **修改参数** - 尝试不同配置
3. **复制代码** - 集成到你的项目

## 代码片段

### 最简单的使用方式

```python
from app_factory import FastMeRAG

rag = FastMeRAG()

# 文档入库
rag.ingest("设备手册.pdf", doc_type="manual")

# 场景化问答
result = rag.chat("设备报警怎么处理？", scene="fault_diagnosis")
print(result["answer"])
```

### 配置化使用（推荐）

```python
from app_factory import FastMeRAG

# 内存受限环境配置
rag = FastMeRAG(
    chunk_max_size=800,        # 减小 chunk 尺寸
    ingest_batch_size=16,      # 减小入库批次
    embedding_batch_size=16,   # 减小 embedding 批量
    show_progress_bar=True,
)

# 日志分析专用配置
rag_log = FastMeRAG(
    chunk_max_size=500,        # 小 chunk 便于精确定位
    ingest_batch_size=32,
    embedding_batch_size=32,
    show_progress_bar=True,
)

# 高性能配置
rag_perf = FastMeRAG(
    chunk_max_size=1500,       # 大 chunk 保留上下文
    ingest_batch_size=64,      # 增大入库批次
    embedding_batch_size=64,   # 增大 embedding 批量
    show_progress_bar=True,
)
```

### 批量入库

```python
# 批量导入文件夹
results = rag.batch_ingest("./logs", doc_type="log")

# 查看结果
for r in results:
    if r["status"] == "success":
        print(f"{r['file_name']}: {r['chunks_count']} 个切片")
```

### 带过滤的问答

```python
# 只查询特定设备的故障记录
result = rag.chat(
    "E001 设备有哪些故障？",
    scene="fault_diagnosis",
    filters={"device_id": "EQ001"}
)

# 打印溯源
for source in result["sources"]:
    print(f"来源：{source.get('device_id')} - {source.get('fault_code')}")
```

### 自定义场景

```python
# 添加质检查询场景
rag.add_scene(
    name="quality_check",
    doc_type="business",
    prompt_template="default",
    source_fields=["work_order_id", "quality_result", "station"]
)

# 使用新场景
result = rag.chat("批次 2024001 合格吗？", scene="quality_check")
```

## 常见问题

### Q: 没有测试数据怎么办？
A: 示例代码中包含注释的测试数据路径，你可以：
1. 使用 `samples/` 目录中的示例文件
2. 准备自己的文档进行测试
3. 先运行不依赖文件的配置示例（如 `custom_config.py` 的部分功能）

### Q: 如何查看详细的错误信息？
A: 在代码开头添加：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Q: 如何切换到不同的向量库？
A: 修改 `app_factory.py` 中的 `LangChainChromaAdapter`，替换为其他向量库适配器（如 PGVector）。

## 下一步

- 阅读 [README.md](../README.md) 了解完整文档
- 查看 [config/](../config/) 目录了解配置文件结构
- 开始构建你自己的 RAG 应用！
