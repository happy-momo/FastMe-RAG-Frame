"""
FastMe RAG Chatbot Demo — 后端入口 / Backend Entrypoint

基于 FastMe RAG 框架的开箱即用 RAG Chatbot 服务。
框架零改动，本服务将 FastMeRAG 当作黑盒依赖使用。

运行 / Run (需 /app/backend 在 sys.path 上，使 `app` 包可导入):
    PYTHONPATH=/app:/app/backend uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import (
    chat_router,
    health_router,
    ingest_router,
    scenes_router,
    sessions_router,
)

logger = logging.getLogger("fastme_rag_demo")

# 框架日志若未配置则保持默认；这里确保 demo 日志可见
if not logging.getLogger("fastme_rag_demo").handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动即触发 FastMeRAG 单例初始化（加载/下载 embedding 模型，失败则启动失败）
    from app.core.rag import RAGManager
    try:
        RAGManager()
        logger.info("后端启动完成，RAG 实例已就绪")
    except Exception as e:
        logger.error("FastMeRAG 初始化失败：%s", e)
        raise
    yield


app = FastAPI(
    title="FastMe RAG Chatbot Demo",
    description="基于 FastMe RAG 框架的开箱即用 RAG Chatbot 服务模板",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS：demo 直接放行，生产应改为受控来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 汇总路由 / Mount routers
app.include_router(ingest_router)
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(scenes_router)
app.include_router(health_router)


@app.get("/")
async def root() -> dict:
    return {
        "service": "FastMe RAG Chatbot Demo",
        "docs": "/docs",
        "healthz": "/healthz",
    }


# =====================================================================
# 全局异常处理 / Global exception handlers
# =====================================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "请求参数校验失败", "errors": exc.errors(), "status_code": 422},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理异常：%s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误：{exc}", "status_code": 500},
    )