# FastMe RAG Chatbot Demo - Backend 镜像
# 后端镜像同时包含框架源码（COPY 仓库根）与服务代码，
# 通过 PYTHONPATH 直接 import 框架，零框架改动。
FROM python:3.11-slim

WORKDIR /app

# 安装框架 + 服务依赖 / Install framework + service deps
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir -r backend/requirements.txt

ENV PYTHONPATH=/app:/app/backend
ENV HF_HOME=/app/hf_cache

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]