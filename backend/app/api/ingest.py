"""入库 API / Ingest API.

处理前端文件上传：UploadFile -> 落临时文件 -> FastMeRAG.ingest() -> 返回结果。
框架的文档加载器只认本地路径，因此必须先把上传内容落盘。
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.rag import RAGManager
from app.schemas.health import IngestResponse

logger = logging.getLogger("fastme_rag_demo")
router = APIRouter(prefix="/api/ingest", tags=["ingest"])

# 允许的文档类型（与框架 splitter 注册一致）
SUPPORTED_DOC_TYPES = {"log", "manual", "business", "sop"}
# 允许的扩展名
SUPPORTED_EXTENSIONS = {".md", ".log", ".txt", ".pdf", ".docx"}


def _parse_extra_metadata(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError
        return data
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=422, detail="extra_metadata 必须是合法的 JSON 对象")


@router.post("", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(..., description="待入库文档"),
    doc_type: str = Form("manual", description="文档类型：log/manual/business/sop"),
    extra_metadata: Optional[str] = Form(None, description="额外元数据 (JSON)"),
) -> dict:
    if doc_type not in SUPPORTED_DOC_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"不支持的 doc_type: {doc_type}，可选 {sorted(SUPPORTED_DOC_TYPES)}",
        )

    ext = Path(file.filename or "").suffix.lower() or ".txt"
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"不支持的文件类型: {ext}，可选 {sorted(SUPPORTED_EXTENSIONS)}",
        )

    extra = _parse_extra_metadata(extra_metadata)
    content = await file.read()

    # 落临时文件后交给框架入库 / Persist to temp file, then ingest
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = await run_in_threadpool(
            RAGManager().ingest, tmp_path, doc_type, extra
        )

        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=str(result))

        logger.info("文档入库成功：%s (%s chunks)", file.filename, result.get("chunks_count"))
        return IngestResponse(
            status=result["status"],
            doc_id=result["doc_id"],
            file_name=result["file_name"],
            doc_type=result["doc_type"],
            chunks_count=result["chunks_count"],
            vector_count=result["vector_count"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("文档入库失败：%s", file.filename)
        raise HTTPException(status_code=500, detail=f"入库失败：{e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)