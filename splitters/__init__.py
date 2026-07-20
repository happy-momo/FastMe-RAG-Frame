"""
文档拆解器模块
Document Splitters Module

提供多种文档类型的拆解器，将文档拆分为适合向量化的 chunk。
Provides multiple document-type splitters that break documents into vectorization-ready chunks.

可用拆解器:
Available splitters:
- LogSplitter: 运维日志拆解器（按时间戳分条） / Operations log splitter (by timestamp)
- ManualSplitter: 设备手册拆解器（按章节层级） / Equipment manual splitter (by chapter hierarchy)
- BusinessSplitter: 工单拆解器（按工单编号） / Work order splitter (by order ID)
- SopSplitter: 工艺 SOP 拆解器（按工序顺序） / SOP splitter (by process step)
- BaseSplitter: 拆解器公共基类（提供通用拆分逻辑） / Base splitter class (common splitting logic)

使用示例:
Usage example:
    from splitters import LogSplitter, ManualSplitter, BaseSplitter
    from splitters.base import SplitterRegistry

    # 直接使用 / Direct usage
    splitter = LogSplitter()
    chunks = splitter.split(document)

    # 或通过注册表 / Or via registry
    registry = SplitterRegistry()
    registry.register("log", LogSplitter())
    registry.register("manual", ManualSplitter())
    splitter = registry.get("log")
"""

from splitters.base import SplitterRegistry, BaseSplitter
from splitters.log_splitter import LogSplitter
from splitters.manual_splitter import ManualSplitter
from splitters.business_splitter import BusinessSplitter
from splitters.sop_splitter import SopSplitter

__all__ = [
    "SplitterRegistry",
    "BaseSplitter",
    "LogSplitter",
    "ManualSplitter",
    "BusinessSplitter",
    "SopSplitter",
]
