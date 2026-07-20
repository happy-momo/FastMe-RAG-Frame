"""
适配器模块 - 外部适配层
Adapters Module - External Adapter Layer

提供第三方库的适配器，包括 Prompt 管理和文档加载功能。
Provides adapters for third-party libraries, including Prompt management and document loading.

可用组件：
Available components:
- PromptAdapter: Prompt 模板管理（支持多语言）
  PromptAdapter: Prompt template management (multi-language support)
- SimpleDocumentLoader: 简单文档加载器（支持 PDF/DOCX/TXT/LOG/MD）
  SimpleDocumentLoader: Simple document loader (supports PDF/DOCX/TXT/LOG/MD)

Example:
    >>> from adapters import PromptAdapter, SimpleDocumentLoader
    >>> adapter = PromptAdapter(path="prompt_templates.yaml", language="zh")
    >>> loader = SimpleDocumentLoader()
    >>> document = loader.load("manual.pdf", doc_type="manual")
"""

from adapters.prompt_adapter import PromptAdapter
from adapters.document_loader import SimpleDocumentLoader

__all__ = ["PromptAdapter", "SimpleDocumentLoader"]
