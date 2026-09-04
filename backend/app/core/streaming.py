"""流式问答控制器 / Streaming answer orchestrator.

背景：框架的 `rag.chat_stream()` 不支持多轮记忆参数（`ChatPipeline.chat_stream`
没有 session 入参）。为在 demo 里同时获得"流式"与"多会话记忆"，本模块直接复用
框架的公开组件（scene_aware_retriever / prompt_adapter / llm / get_memory）自行组装
消息并流式生成。不改动框架源码，仅在应用层编排其组件。

Backstory: the framework's `rag.chat_stream()` does not accept a memory/session
argument (ChatPipeline.chat_stream has no session parameter). To get both
streaming and multi-session memory in this demo, this module reuses the
framework's public components (scene_aware_retriever / prompt_adapter / llm /
get_memory) to assemble messages itself and stream output. It does not modify the
framework source; it only orchestrates its components at the application layer.
"""

import logging
from typing import Any, Dict, Optional

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.rag import RAGManager

logger = logging.getLogger("fastme_rag_demo")


class SseFrame:
    """表示一个 SSE 帧 / Represents a single SSE frame."""

    def __init__(self, event: str, data: Any):
        self.event = event
        self.data = data


def stream_chat(
    manager: RAGManager,
    question: str,
    scene: str,
    session_id: Optional[str],
    filters: Optional[Dict[str, Any]],
    top_k: Optional[int],
    max_context_length: Optional[int] = 4096,
):
    """
    生成 SSE 帧序列：先发送检索元信息，再逐块发送文本增量，最后 [DONE]。
    Yields SSE frames: retrieval meta first, then text deltas, then done.
    """
    rag = manager.rag

    # 1. 场景化检索（同步阻塞，先于流式） / Scene-aware retrieval (before streaming)
    contexts, source_fields = rag.scene_aware_retriever.retrieve(
        question=question,
        scene=scene,
        filters=filters,
        top_k=top_k,
    )

    # 2. 组装上下文文本 / Assemble context text
    context_text = rag.prompt_adapter._format_context(contexts, source_fields)
    if max_context_length and len(context_text) > max_context_length:
        context_text = context_text[:max_context_length] + "\n...(上下文已截断)"

    # 3. 系统 Prompt / System prompt
    scene_config = rag.scene_router.route(scene)
    prompt_name = scene_config.get("prompt_template", "default")
    system_prompt = rag.prompt_adapter.get_system_prompt(prompt_name)

    # 4. 组装消息列表（含历史记忆）/ Build message list (with history memory)
    messages = [SystemMessage(content=system_prompt)]
    memory = None
    if session_id:
        memory = rag.get_memory(session_id)
        if memory:
            history = memory.load_memory_variables({}).get("history", [])
            messages.extend(history)
    messages.append(HumanMessage(
        content=f"用户问题：{question}\n\n检索到的上下文信息：{context_text}\n\n基于以上内容回答"
    ))

    # 5. 发送检索元信息（溯源）/ Emit retrieval meta (sources)
    yield SseFrame("meta", {
        "sources": _build_sources(contexts, source_fields),
        "context_count": len(contexts),
    })

    # 6. 流式生成 / Stream generation
    full_answer = []
    try:
        for chunk in rag.llm.stream(messages):
            if chunk.content:
                full_answer.append(chunk.content)
                yield SseFrame("delta", chunk.content)
    except Exception as e:
        logger.exception("流式生成失败")
        yield SseFrame("error", {"message": str(e)})

    # 7. 保存记忆（仅当 LLM 有正常产出）/ Save memory (only if LLM produced output)
    answer = "".join(full_answer)
    if session_id and memory and answer and answer.strip():
        try:
            memory.save_context({"input": question}, {"output": answer})
        except Exception as e:
            logger.warning("保存记忆失败：%s", e)

    yield SseFrame("done", {"answer": answer})


def _build_sources(contexts: list, source_fields: list) -> list:
    """与框架 ChatPipeline._build_sources 对齐，构建溯源列表。"""
    sources = []
    for item in contexts:
        source_item = {
            "score": getattr(item, "score", None),
            "preview": item.text[:200],
        }
        for field in source_fields:
            value = getattr(item, field, None)
            if value is None:
                value = item.metadata.get(field)
            if value is not None:
                source_item[field] = value
        sources.append(source_item)
    return sources