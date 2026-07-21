"""
文档入库流水线
Document Ingest Pipeline

负责将原始文档加载、拆解、元数据抽取并向量化入库。
Handles loading, splitting, metadata extraction, and vectorized ingestion of raw documents.

Classes:
    IngestPipeline: 文档入库流水线，编排整个入库流程 / Document ingest pipeline orchestrating the full ingestion flow

Example:
    >>> from core.ingest_pipeline import IngestPipeline
    >>> from vector_stores.base import VectorStoreAdapter
    >>> pipeline = IngestPipeline(
    ...     document_loader=loader,
    ...     splitter_registry=registry,
    ...     metadata_extractor=extractor,
    ...     vector_store=adapter  # VectorStoreAdapter 实例
    ... )
    >>> result = pipeline.ingest("manual.pdf", doc_type="manual")
"""

import logging
import gc
from pathlib import Path
from typing import Optional, List

from langchain_core.documents import Document

from vector_stores.base import VectorStoreAdapter

# 框架日志配置
logger = logging.getLogger("fastme_rag")


class IngestPipeline:
    """
    文档入库流水线
    Document Ingest Pipeline

    编排文档入库的完整流程：
    Orchestrates the full document ingestion flow:
    1. 加载文档（PDF/DOCX/TXT/LOG）
       Load document (PDF/DOCX/TXT/LOG)
    2. 使用拆解器拆分文档
       Split document using splitter
    3. 提取工业元数据
       Extract industrial metadata
    4. （可选）审核模式预览
       (Optional) Review mode preview
    5. 分批向量化入库
       Batch vectorized ingestion

    Attributes:
        document_loader: 文档加载器实例 / Document loader instance
        splitter_registry: 拆解器注册表（splitter 已初始化，包含 chunk_max_size 配置）/ Splitter registry (initialized, includes chunk_max_size config)
        metadata_extractor: 元数据抽取器 / Metadata extractor
        vector_store: VectorStoreAdapter 实例 / VectorStoreAdapter instance
        ingest_batch_size: 入库分批大小 / Ingestion batch size
        show_progress_bar: 是否显示进度条 / Whether to show progress bar

    Example:
        >>> pipeline = IngestPipeline(
        ...     loader, registry, extractor, adapter,
        ...     ingest_batch_size=32
        ... )
        >>> result = pipeline.ingest(
        ...     file_path="fault_log.log",
        ...     doc_type="log",
        ...     extra_metadata={"device_id": "EQ001"}
        ... )
        >>> print(result["chunks_count"])  # 输出切片数量
    """

    def __init__(
        self,
        document_loader,
        splitter_registry,
        metadata_extractor,
        vector_store: VectorStoreAdapter,
        ingest_batch_size: int = 32,
        show_progress_bar: bool = False,
    ):
        """
        初始化入库流水线
        Initialize ingest pipeline

        Args:
            document_loader: 文档加载器，负责读取文件 / Document loader responsible for reading files
            splitter_registry: 拆解器注册表，按 doc_type 获取拆解器 / Splitter registry, gets splitter by doc_type
            metadata_extractor: 元数据抽取器，提取工业字段 / Metadata extractor for industrial fields
            vector_store: VectorStoreAdapter 实例，负责向量化和入库 / VectorStoreAdapter instance for vectorization and ingestion
            ingest_batch_size: 入库分批大小，默认 32 / Ingestion batch size, default 32
            show_progress_bar: 是否显示进度条，默认 False / Whether to show progress bar, default False
        """
        self.document_loader = document_loader
        self.splitter_registry = splitter_registry
        self.metadata_extractor = metadata_extractor
        self.vector_store = vector_store
        self.ingest_batch_size = ingest_batch_size
        self.show_progress_bar = show_progress_bar

    def ingest(
        self,
        file_path: str,
        doc_type: str,
        extra_metadata: Optional[dict] = None,
        require_review: bool = False
    ) -> dict:
        """
        执行文档入库
        Execute document ingestion

        Args:
            file_path (str): 文件路径 / File path
            doc_type (str): 文档类型 (log/manual/business/sop) / Document type (log/manual/business/sop)
            extra_metadata (dict, optional): 额外元数据，默认 None / Extra metadata, default None
            require_review (bool, optional): 是否需要审核，默认 False / Whether review is required, default False
                - True: 返回切片预览，不入库 / True: return chunk preview, no ingestion
                - False: 直接入库 / False: ingest directly

        Returns:
            dict: 入库结果，包含：/ Ingestion result containing:
                - status (str): "success" | "waiting_review"
                - doc_id (str): 文档 ID / Document ID
                - file_name (str): 文件名 / File name
                - chunks_count (int): 切片数量（成功时）/ Chunk count (on success)
                - vector_count (int): 向量总数（成功时）/ Total vector count (on success)
                - chunks (list): 切片列表（审核模式时）/ Chunk list (in review mode)

        Raises:
            ValueError: 当 doc_type 未注册拆解器时 / When doc_type has no registered splitter
            FileNotFoundError: 当文件不存在时 / When file does not exist

        Example:
            >>> # 直接入库 / Direct ingestion
            >>> result = pipeline.ingest("manual.pdf", "manual")
            >>> print(f"入库 {result['chunks_count']} 个切片")

            >>> # 审核模式 / Review mode
            >>> result = pipeline.ingest("manual.pdf", "manual", require_review=True)
            >>> if result["status"] == "waiting_review":
            ...     print(f"待审核：{len(result['chunks'])} 个切片")
        """
        # 1. 加载文档
        document = self.document_loader.load(Path(file_path), doc_type, extra_metadata)

        # [必须] 文档加载信息
        logger.info(f"[入库] 文档加载完成：{document.file_name} (doc_id={document.doc_id}, doc_type={doc_type})")

        # 2. 获取拆解器并拆分文档
        splitter = self.splitter_registry.get(doc_type)
        chunks = splitter.split(document)

        # [调试] 切分结果详情
        logger.debug(f"[调试 - 切分] 文档 '{document.file_name}' 切分完成，共 {len(chunks)} 个 chunk")
        for i, chunk in enumerate(chunks):
            logger.debug(f"[调试 - 切分]   chunk[{i}]: chunk_id={chunk.chunk_id}, "
                         f"文本长度={len(chunk.text)}字，"
                         f"metadata={chunk.metadata}")
            # [调试] 每个 chunk 的前 200 字预览
            preview = chunk.text[:200].replace('\n', '\\n')
            logger.debug(f"[调试 - 切分]   chunk[{i}] 预览：{preview}...")

        # 3. 提取元数据
        chunks = self.metadata_extractor.enrich_chunk(chunks)

        # [调试] 元数据提取结果
        for i, chunk in enumerate(chunks):
            extracted = {k: v for k, v in chunk.metadata.items()
                         if k in self.metadata_extractor.get_available_fields() and v is not None}
            if extracted:
                logger.debug(f"[调试 - 元数据] chunk[{i}] ({chunk.chunk_id}) 提取到：{extracted}")

        # [必须] 入库摘要
        logger.info(f"[入库] 切分 + 元数据提取完成：{len(chunks)} 个 chunk 待入库")

        # 4. 审核模式：返回预览
        if require_review:
            return {
                "status": "waiting_review",
                "doc_id": document.doc_id,
                "file_name": document.file_name,
                "doc_type": document.doc_type,
                "chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.text,
                        "metadata": chunk.metadata
                    }
                    for chunk in chunks
                ]
            }

        # 5. 向量化入库 - 分批处理以避免内存峰值
        BATCH_SIZE = self.ingest_batch_size
        total_chunks = len(chunks)
        num_batches = (total_chunks + BATCH_SIZE - 1) // BATCH_SIZE

        logger.info(f"[入库] 开始分批入库：共 {total_chunks} 个 chunk, 分为 {num_batches} 批，每批最多 {BATCH_SIZE} 个")

        for batch_idx in range(num_batches):
            start_idx = batch_idx * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, total_chunks)
            batch_chunks = chunks[start_idx:end_idx]

            # 构建 LangChain Document 列表
            docs = []
            for chunk in batch_chunks:
                # 防御性检查：确保 doc_type 存在
                if not chunk.doc_type:
                    logger.error(
                        f"[入库] chunk {chunk.chunk_id} 缺失 doc_type 字段. "
                        f"file={document.file_name}, doc_id={document.doc_id}"
                    )
                    raise ValueError(
                        f"Chunk {chunk.chunk_id} missing 'doc_type'. "
                        f"Please ensure splitter sets doc_type correctly."
                    )

                docs.append(Document(
                    page_content=chunk.text,
                    metadata={
                        "chunk_id": chunk.chunk_id,
                        "doc_id": chunk.doc_id,
                        "doc_type": chunk.doc_type,  # 显式传递，不依赖 chunk.metadata
                        **chunk.metadata            # 其他元数据
                    }
                ))

            # 添加当前批次（适配器会自动清洗元数据）
            batch_ids = [chunk.chunk_id for chunk in batch_chunks]
            self.vector_store.add_documents(documents=docs, ids=batch_ids)

            # 批次完成日志
            logger.debug(f"[入库] 批次 {batch_idx + 1}/{num_batches} 完成：入库 {len(batch_chunks)} 个 chunk")

        # [必须] 入库完成信息
        vector_count = self.vector_store.get_count()
        logger.info(f"[入库] 入库完成：doc_id={document.doc_id}, "
                     f"本次入库 {len(chunks)} 个 chunk, "
                     f"向量库总量 {vector_count}")

        return {
            "status": "success",
            "doc_id": document.doc_id,
            "file_name": document.file_name,
            "doc_type": doc_type,
            "chunks_count": len(chunks),
            "vector_count": vector_count
        }

    def batch_ingest(
        self,
        folder_path: str,
        doc_type: str,
        extra_metadata: Optional[dict] = None,
        file_extensions: Optional[List[str]] = None,
        persist_interval: int = 10
    ) -> list:
        """
        批量文件夹入库
        Batch folder ingestion

        Args:
            folder_path (str): 文件夹路径 / Folder path
            doc_type (str): 文档类型 / Document type
            extra_metadata (dict, optional): 额外元数据（所有文件共享），默认 None / Extra metadata shared by all files, default None
            file_extensions (list, optional): 文件扩展名过滤，默认 [".pdf", ".docx", ".txt", ".log", ".md"]
                                              / File extension filter, default [".pdf", ".docx", ".txt", ".log", ".md"]
            persist_interval (int, optional): 每处理 N 个文件后执行内存清理，默认 10
                                              设为 0 可禁用内存清理
                                              / Memory cleanup every N files, default 10; set 0 to disable

        Returns:
            list: 每个文件的入库结果列表 / List of ingestion results per file

        Raises:
            FileNotFoundError: 当文件夹不存在时 / When folder does not exist

        Example:
            >>> # 默认每 10 个文件清理一次内存 / Default: memory cleanup every 10 files
            >>> results = pipeline.batch_ingest("./logs", doc_type="log")

            >>> # 大文件时使用更小的间隔 / Use smaller interval for large files
            >>> results = pipeline.batch_ingest("./manuals", doc_type="manual", persist_interval=5)
        """
        if file_extensions is None:
            file_extensions = [".pdf", ".docx", ".txt", ".log", ".md"]

        results = []
        folder = Path(folder_path)

        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        # 统计信息
        total_files = 0
        success_files = 0
        error_files = 0

        logger.info(f"[批量入库] 开始处理文件夹：{folder_path}, doc_type={doc_type}, persist_interval={persist_interval}")

        for file in folder.glob("*"):
            if file.is_file() and file.suffix.lower() in file_extensions:
                total_files += 1
                try:
                    logger.info(f"[批量入库] 处理文件 ({total_files}): {file.name}")
                    result = self.ingest(
                        file_path=str(file),
                        doc_type=doc_type,
                        extra_metadata=extra_metadata
                    )
                    results.append(result)
                    success_files += 1
                    logger.info(f"[批量入库] 文件 {file.name} 入库成功：{result['chunks_count']} 个切片")

                    # 定期执行内存清理
                    if persist_interval > 0 and total_files % persist_interval == 0:
                        logger.info(f"[批量入库] 已处理 {total_files} 个文件，执行内存清理...")
                        self.vector_store.reset_for_memory_cleanup()
                        gc.collect()
                        logger.info(f"[批量入库] 内存清理完成")

                except Exception as e:
                    results.append({
                        "status": "error",
                        "file": str(file),
                        "error": str(e)
                    })
                    error_files += 1
                    logger.error(f"[批量入库] 文件 {file.name} 入库失败：{e}")

        # [必须] 批量入库完成信息
        logger.info(f"[批量入库] 完成：共处理 {total_files} 个文件，成功 {success_files} 个，失败 {error_files} 个")

        return results
