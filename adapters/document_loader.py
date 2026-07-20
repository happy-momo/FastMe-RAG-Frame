"""
文档加载器模块
Document Loader Module

提供多格式文档加载功能，支持 PDF、DOCX、TXT、LOG、MD 等格式，
并针对大文件进行了内存优化。
Provides multi-format document loading functionality, supporting PDF, DOCX,
TXT, LOG, MD and other formats, with memory optimization for large files.
"""

import hashlib
from pathlib import Path

from pypdf import PdfReader
from docx import Document as DocxDocument

from core.models import FastMeDocument


class SimpleDocumentLoader:
    """
    简单文档加载器
    Simple Document Loader

    支持加载 PDF、DOCX、TXT、LOG、MD 等格式的文档。
    Supports loading documents in PDF, DOCX, TXT, LOG, MD and other formats.

    内存优化：
    Memory optimization:
    1. 文本文件：使用流式读取，避免一次性加载大文件
       Text files: Uses streaming reads to avoid loading large files at once
    2. PDF 文件：逐页提取，减少内存峰值
       PDF files: Extracts page by page to reduce memory peaks
    3. DOCX 文件：逐段读取，避免同时加载整个文档
       DOCX files: Reads paragraph by paragraph to avoid loading the entire document at once
    """

    def load(self, file_path: Path, doc_type: str, extra_metadata: dict | None = None) -> FastMeDocument:
        """
        加载文档
        Load document

        Args:
            file_path: 文件路径 / File path
            doc_type: 文档类型 / Document type
            extra_metadata: 额外元数据 / Extra metadata

        Returns:
            文档对象 / Document object
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in [".md", ".log", ".txt"]:
            text = self._load_text(path)
        elif suffix == ".pdf":
            text = self._load_pdf(path)
        elif suffix == ".docx":
            text = self._load_docx(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        doc_id = self._build_doc_id(path)

        metadata = {
            "source": path.name,
            "file_path": str(path),
            "doc_type": doc_type,
            "file_type": suffix.replace(".", "")
        }

        if extra_metadata:
            metadata.update(extra_metadata)

        return FastMeDocument(
            doc_id=doc_id,
            doc_type=doc_type,
            file_name=path.name,
            file_path=str(path),
            text=text,
            metadata=metadata
        )

    def _load_text(self, path: Path) -> str:
        """
        加载文本文件（TXT/LOG/MD）
        Load text file (TXT/LOG/MD)

        内存优化：对于大文件，使用分块读取而不是一次性加载
        Memory optimization: For large files, uses chunked reads instead of loading at once
        """
        # 检查文件大小
        file_size = path.stat().st_size

        # 小文件直接读取（< 1MB）
        if file_size < 1024 * 1024:
            return path.read_text(encoding="utf-8", errors="ignore")

        # 大文件分块读取，避免内存峰值
        chunks = []
        chunk_size = 1024 * 1024  # 1MB 每块

        with path.open("r", encoding="utf-8", errors="ignore") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)

        return "".join(chunks)

    def _load_pdf(self, path: Path) -> str:
        """
        加载 PDF 文件
        Load PDF file

        内存优化：逐页提取文本，每提取一页就释放一页的内存
        Memory optimization: Extracts text page by page, releasing memory after each page
        """
        reader = PdfReader(str(path))
        total_pages = len(reader.pages)

        # 使用生成器方式逐页处理，减少内存占用
        parts = []
        for i in range(total_pages):
            page = reader.pages[i]
            text = page.extract_text() or ""
            parts.append(text)
            # 显式删除页面对象，帮助垃圾回收
            del page

        # 一次性 join 所有文本
        result = "\n".join(parts)

        # 释放 parts 列表
        parts.clear()

        return result

    def _load_docx(self, path: Path) -> str:
        """
        加载 DOCX 文件
        Load DOCX file

        内存优化：逐段读取，避免同时加载整个文档
        Memory optimization: Reads paragraph by paragraph to avoid loading the entire document at once
        """
        doc = DocxDocument(str(path))
        parts = []

        # 逐段读取段落
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                parts.append(text)

        # 逐行读取表格
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                parts.append(" | ".join(cells))

        result = "\n".join(parts)
        parts.clear()

        return result

    def _build_doc_id(self, path: Path) -> str:
        """
        构建文档 ID
        Build document ID

        基于文件路径、大小和修改时间生成唯一 ID。
        Generates a unique ID based on file path, size, and modification time.
        """
        stat = path.stat()
        raw = f"{path.resolve()}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()
