"""
FastMe RAG 配置化使用示例

本示例演示如何通过配置参数调整 FastMe RAG 的行为，以适应不同的使用场景。
"""

from app_factory import FastMeRAG


# ==============================================================================
# 场景 1: 默认配置（快速开始）
# ==============================================================================
# 适用于：大多数标准场景，快速测试和原型开发

print("=" * 60)
print("场景 1: 默认配置")
print("=" * 60)

rag_default = FastMeRAG()
# 默认配置:
# - chunk_max_size: 1000 字符
# - ingest_batch_size: 32
# - embedding_batch_size: 32
# - show_progress_bar: True


# ==============================================================================
# 场景 2: 内存受限环境
# ==============================================================================
# 适用于：笔记本电脑、低内存服务器、容器环境
# 特点：减小批量大小，降低内存峰值

print("\n场景 2: 内存受限配置")
print("=" * 60)

rag_low_memory = FastMeRAG(
    chunk_max_size=800,        # 减小 chunk 尺寸
    ingest_batch_size=16,      # 减小入库批次
    embedding_batch_size=16,   # 减小 embedding 批量
    show_progress_bar=True,    # 保留进度显示
)


# ==============================================================================
# 场景 3: 高性能环境
# ==============================================================================
# 适用于：高配服务器、GPU 环境、批量处理
# 特点：增大批量，提高吞吐量

print("\n场景 3: 高性能配置")
print("=" * 60)

rag_high_perf = FastMeRAG(
    chunk_max_size=1500,       # 增大 chunk 尺寸
    ingest_batch_size=64,      # 增大入库批次
    embedding_batch_size=64,   # 增大 embedding 批量
    show_progress_bar=True,    # 显示进度
)


# ==============================================================================
# 场景 4: API 服务配置
# ==============================================================================
# 适用于：生产环境 API 服务
# 特点：关闭进度条，平衡性能

print("\n场景 4: API 服务配置")
print("=" * 60)

rag_api = FastMeRAG(
    chunk_max_size=1000,       # 标准 chunk 尺寸
    ingest_batch_size=32,      # 标准批次
    embedding_batch_size=32,   # 标准批量
    show_progress_bar=False,   # 关闭进度条（日志友好）
)


# ==============================================================================
# 场景 5: 日志分析专用
# ==============================================================================
# 适用于：运维日志、故障记录分析
# 特点：较小的 chunk 尺寸，便于精确定位

print("\n场景 5: 日志分析配置")
print("=" * 60)

rag_log = FastMeRAG(
    chunk_max_size=500,        # 小 chunk 便于定位
    ingest_batch_size=32,
    embedding_batch_size=32,
    show_progress_bar=True,
)

# 入库日志文件
# rag_log.ingest("./logs/fault_log.log", doc_type="log")


# ==============================================================================
# 场景 6: 设备手册专用
# ==============================================================================
# 适用于：设备操作手册、维修手册查询
# 特点：较大的 chunk 尺寸，保留完整章节上下文

print("\n场景 6: 设备手册配置")
print("=" * 60)

rag_manual = FastMeRAG(
    chunk_max_size=1500,       # 大 chunk 保留上下文
    ingest_batch_size=32,
    embedding_batch_size=32,
    show_progress_bar=True,
)

# 入库手册
# rag_manual.ingest("./data/equipment_manual.pdf", doc_type="manual")


# ==============================================================================
# 场景 7: 混合配置（高级用法）
# ==============================================================================
# 适用于：需要为不同文档类型使用不同配置的场景
# 特点：手动创建 splitters，独立配置

print("\n场景 7: 混合配置（高级）")
print("=" * 60)

from splitters.log_splitter import LogSplitter
from splitters.manual_splitter import ManualSplitter
from splitters.business_splitter import BusinessSplitter
from splitters.sop_splitter import SopSplitter

rag_mixed = FastMeRAG()

# 为不同文档类型注册不同的 splitters
rag_mixed.splitter_registry.register("log", LogSplitter(max_chunk_size=500))
rag_mixed.splitter_registry.register("manual", ManualSplitter(max_chunk_size=1500))
rag_mixed.splitter_registry.register("business", BusinessSplitter(max_chunk_size=1000))
rag_mixed.splitter_registry.register("sop", SopSplitter(max_chunk_size=1200))

print("混合配置 splitters:")
print(f"  LogSplitter: {rag_mixed.splitter_registry.get('log').max_chunk_size}")
print(f"  ManualSplitter: {rag_mixed.splitter_registry.get('manual').max_chunk_size}")
print(f"  BusinessSplitter: {rag_mixed.splitter_registry.get('business').max_chunk_size}")
print(f"  SopSplitter: {rag_mixed.splitter_registry.get('sop').max_chunk_size}")


# ==============================================================================
# 配置参数说明
# ==============================================================================
"""
chunk_max_size (int): 单个 chunk 最大字符数
    - 默认值：1000
    - 建议值：
        - 日志：500-800（便于精确定位）
        - 手册：1000-1500（保留章节上下文）
        - 工单：800-1200（平衡定位和上下文）
        - SOP: 1000-1500（保留完整工序）
    - 影响：chunk 越小，检索精度越高，但可能丢失上下文

ingest_batch_size (int): 入库分批大小
    - 默认值：32
    - 建议值：
        - 内存受限：16-24
        - 标准环境：32-48
        - 高性能：64-128
    - 影响：批次越小，内存峰值越低，但入库速度越慢

embedding_batch_size (int): Embedding 批量大小
    - 默认值：32
    - 建议值：
        - CPU/内存受限：8-16
        - 标准环境：32-48
        - GPU 环境：64-128
    - 影响：批量越大，GPU 利用率越高，但内存占用越大

show_progress_bar (bool): 是否显示进度条
    - 默认值：True
    - 建议值：
        - 交互式/调试：True
        - API 服务/后台任务：False
    - 影响：关闭进度条可减少日志输出，适合生产环境
"""

print("\n" + "=" * 60)
print("配置示例完成!")
print("=" * 60)
