# FastMe RAG 文档中心

欢迎使用 FastMe RAG 框架文档。本目录包含完整的框架文档，分为中文和英文两个版本。

---

## 文档索引

### 中文文档

| 文档 | 说明 |
|------|------|
| [快速开始指南](QUICKSTART_CN.md) | 5 分钟快速上手教程 |
| [架构设计文档](ARCHITECTURE_CN.md) | 系统架构、模块解耦、调用链路详解 |
| [开发者指南](DEVELOPER_GUIDE_CN.md) | 添加场景、Splitter、向量库的详细步骤 |
| [API 参考文档](API_REFERENCE_CN.md) | 所有公开 API 的详细说明 |

### English Documentation

| Document | Description |
|----------|-------------|
| [Quick Start Guide](QUICKSTART_EN.md) | 5-minute quick start tutorial |
| [Architecture Design](ARCHITECTURE_EN.md) | System architecture, module decoupling, call chain details |
| [Developer Guide](DEVELOPER_GUIDE_EN.md) | Detailed steps for adding scenes, splitters, and vector stores |
| [API Reference](API_REFERENCE_EN.md) | Detailed description of all public APIs |

---

## 快速导航

### 新手入门

1. 阅读 [快速开始指南](QUICKSTART_CN.md) 了解基本使用方法
2. 查看 [API 参考文档](API_REFERENCE_CN.md) 了解所有可用 API
3. 参考 examples/ 目录下的示例代码

### 架构理解

1. 阅读 [架构设计文档](ARCHITECTURE_CN.md) 了解整体架构
2. 查看各模块的源码注释

### 功能扩展

1. 阅读 [开发者指南](DEVELOPER_GUIDE_CN.md) 学习扩展方法
2. 参考现有实现（如 ChromaAdapter、LogSplitter）

---

## 项目结构

```
FASTME-RAG/
├── app_factory.py              # 主框架入口
├── app.py                      # 使用示例
├── requirements.txt            # Python 依赖
├── README.md                   # 项目说明
├── docs/                       # 文档目录
│   ├── README.md               # 文档索引（本文件）
│   ├── QUICKSTART_CN.md        # 中文快速开始
│   ├── QUICKSTART_EN.md        # 英文快速开始
│   ├── ARCHITECTURE_CN.md      # 中文架构设计
│   ├── ARCHITECTURE_EN.md      # 英文架构设计
│   ├── DEVELOPER_GUIDE_CN.md   # 中文开发者指南
│   ├── DEVELOPER_GUIDE_EN.md   # 英文开发者指南
│   ├── API_REFERENCE_CN.md     # 中文 API 参考
│   └── API_REFERENCE_EN.md     # 英文 API 参考
│
├── core/                       # 核心模块
├── vector_stores/              # 向量库模块
├── retrievers/                 # 检索器模块
├── splitters/                  # 文档拆解器
├── manufacturing/              # 制造业专属组件
├── routers/                    # 路由器
├── adapters/                   # 适配器
├── config/                     # 配置文件
├── examples/                   # 使用示例
└── tests/                      # 单元测试
```

---

## 相关链接

- [GitHub 仓库](https://github.com/happy-momo/FASTME-RAG)
- [问题反馈](https://github.com/happy-momo/FASTME-RAG/issues)

---

## 版本信息

- 文档版本：1.0
- 最后更新：2024-01
- 框架版本：见 requirements.txt

---

<div align="center">

**Made with care for Manufacturing Industry**

</div>
