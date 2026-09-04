"""入库与健康检查数据契约 / Ingest & health data contracts."""

from typing import Any, Dict, List

from pydantic import BaseModel


class IngestResponse(BaseModel):
    status: str
    doc_id: str
    file_name: str
    doc_type: str
    chunks_count: int
    vector_count: int


class SceneInfo(BaseModel):
    name: str
    description: str = ""


class HealthResponse(BaseModel):
    status: str
    llm_reachable: bool
    vector_count: int
    models_dir: str