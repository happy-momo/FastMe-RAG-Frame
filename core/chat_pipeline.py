"""
对话流水线
Chat Pipeline

负责场景化问答的检索、Prompt 组装、LLM 调用、溯源信息构建和对话记忆管理。
Handles scene-aware Q&A retrieval, prompt assembly, LLM invocation, source tracing, and conversation memory management.

Classes:
    ChatPipeline: 对话流水线，编排完整的问答流程 / Chat pipeline orchestrating the full Q&A flow

Example:
    >>> from core.chat_pipeline import ChatPipeline
    >>> from retrievers import SceneAwareRetriever
    >>> pipeline = ChatPipeline(
    ...     scene_aware_retriever=retriever,
    ...     prompt_adapter=adapter,
    ...     llm=llm
    ... )
    >>> result = pipeline.chat("设备报警怎么处理？", scene="fault_diagnosis")
    >>> print(result["answer"])
"""

import logging
from typing import Dict, Optional, Generator, Tuple, List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferWindowMemory

from core.models import FastMeSearchResult
from retrievers.scene_aware import SceneAwareRetriever

# 框架日志配置
logger = logging.getLogger("fastme_rag")


class ChatPipeline:
    """
    对话流水线
    Chat Pipeline

    编排对话的完整流程：
    Orchestrates the full conversation flow:
    1. 场景路由（确定 doc_type、Prompt 模板、溯源字段）
       Scene routing (determine doc_type, prompt template, source fields)
    2. 检索上下文（带 metadata 过滤）
       Retrieve context (with metadata filtering)
    3. 组装 Prompt（系统 Prompt + 用户 Prompt）
       Assemble prompt (system prompt + user prompt)
    4. 调用 LLM 生成回答
       Invoke LLM to generate answer
    5. 构建溯源信息
       Build source tracing information

    Attributes:
        scene_aware_retriever: SceneAwareRetriever 实例 / SceneAwareRetriever instance
        prompt_adapter: Prompt 适配器 / Prompt adapter
        llm: LLM 实例（ChatOpenAI）/ LLM instance (ChatOpenAI)

    Example:
        >>> pipeline = ChatPipeline(retriever, adapter, llm)
        >>> result = pipeline.chat(
        ...     question="E001 设备有什么故障？",
        ...     scene="fault_diagnosis",
        ...     filters={"device_id": "EQ001"}
        ... )
        >>> print(result["answer"])
    """

    def __init__(
        self,
        scene_aware_retriever: SceneAwareRetriever,
        prompt_adapter,
        llm,
    ):
        """
        初始化对话流水线
        Initialize chat pipeline

        Args:
            scene_aware_retriever: SceneAwareRetriever 实例 / SceneAwareRetriever instance
            prompt_adapter: Prompt 适配器，管理 Prompt 模板 / Prompt adapter managing prompt templates
            llm: LLM 实例（ChatOpenAI）/ LLM instance (ChatOpenAI)
        """
        self.scene_aware_retriever = scene_aware_retriever
        self.prompt_adapter = prompt_adapter
        self.llm = llm

        # 初始化记忆管理
        self.memories: Dict[str, ConversationBufferWindowMemory] = {}
        # 保存每个会话的 max_turns 配置
        self.memory_configs: Dict[str, int] = {}

    def chat(
        self,
        question: str,
        scene: str = "default",
        filters: Optional[dict] = None,
        top_k: Optional[int] = None
    ) -> dict:
        """
        执行场景化问答
        Execute scene-aware Q&A

        Args:
            question (str): 用户问题 / User question
            scene (str): 场景名称，默认 "default" / Scene name, default "default"
            filters (dict, optional): 过滤条件，如 {"device_id": "EQ001"} / Filter conditions, e.g. {"device_id": "EQ001"}
            top_k (int, optional): 召回数量，默认使用场景配置 / Retrieval count, default uses scene config

        Returns:
            dict: 问答结果，包含：/ Q&A result containing:
                - question (str): 用户问题 / User question
                - scene (str): 场景名称 / Scene name
                - filters (dict): 过滤条件 / Filter conditions
                - answer (str): LLM 生成的回答 / LLM-generated answer
                - sources (list): 溯源信息列表 / Source tracing information list

        Example:
            >>> result = pipeline.chat("设备报警怎么处理？", scene="fault_diagnosis")
            >>> print(result["answer"])
        """
        # [必须] 问答请求信息
        logger.info(f"[问答] 收到请求：question='{question}', scene={scene}, filters={filters}, top_k={top_k}")

        # 1. 执行场景化检索
        contexts, source_fields = self.scene_aware_retriever.retrieve(
            question=question,
            scene=scene,
            filters=filters,
            top_k=top_k
        )

        # [调试] 上下文检索结果摘要
        logger.debug(f"[调试 - 上下文] 场景={scene}, 检索到 {len(contexts)} 条上下文，source_fields={source_fields}")
        for i, ctx in enumerate(contexts):
            logger.debug(f"[调试 - 上下文]   上下文 [{i}]: score={ctx.score:.4f}, "
                         f"chunk_id={ctx.chunk_id}, doc_type={ctx.doc_type}")
            logger.debug(f"[调试 - 上下文]   上下文 [{i}] 文本预览：{ctx.text[:150].replace(chr(10), chr(92)+'n')}...")

        # 2. 格式化上下文
        context_text = self.prompt_adapter._format_context(contexts, source_fields)

        # [调试] 格式化后的上下文全文
        logger.debug(f"[调试 - 上下文] 格式化后上下文:\n{context_text}")

        # 3. 获取场景配置和系统 Prompt
        scene_config = self.scene_aware_retriever.scene_router.route(scene)
        prompt_template_name = scene_config.get("prompt_template", "default")
        system_prompt = self.prompt_adapter.get_system_prompt(prompt_template_name)

        # [调试] 系统 Prompt
        logger.debug(f"[调试-Prompt] system_prompt:\n{system_prompt}")

        # 4. 构建消息并调用 LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户问题：{question}\n\n检索到的上下文信息：{context_text}\n\n基于以上内容回答")
        ]

        answer = self.llm.invoke(messages).content

        # [必须] 问答完成信息
        answer_preview = answer[:100].replace('\n', '\\n') if answer else ""
        logger.info(f"[问答] 回答完成：answer 预览='{answer_preview}...', 溯源数={len(contexts)}")

        # 5. 构建溯源信息
        sources = self._build_sources(contexts, source_fields)

        return {
            "question": question,
            "scene": scene,
            "filters": filters,
            "answer": answer,
            "sources": sources
        }

    def chat_stream(
        self,
        question: str,
        scene: str = "default",
        filters: Optional[dict] = None,
        top_k: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        执行流式场景化问答
        Execute streaming scene-aware Q&A

        Args:
            question (str): 用户问题 / User question
            scene (str): 场景名称 / Scene name
            filters (dict, optional): 过滤条件 / Filter conditions
            top_k (int, optional): 召回数量 / Retrieval count

        Yields:
            str: LLM 生成的文本片段 / LLM-generated text chunks

        Example:
            >>> for chunk in pipeline.chat_stream("设备报警怎么处理？", scene="fault_diagnosis"):
            ...     print(chunk, end="", flush=True)
        """
        # 1. 执行场景化检索
        contexts, source_fields = self.scene_aware_retriever.retrieve(
            question=question,
            scene=scene,
            filters=filters,
            top_k=top_k
        )

        # [调试] 流式问答上下文
        logger.debug(f"[调试 - 流式上下文] 检索到 {len(contexts)} 条上下文")

        # 2. 格式化上下文
        context_text = self.prompt_adapter._format_context(contexts, source_fields)

        # 3. 获取场景配置和系统 Prompt
        scene_config = self.scene_aware_retriever.scene_router.route(scene)
        prompt_template_name = scene_config.get("prompt_template", "default")
        system_prompt = self.prompt_adapter.get_system_prompt(prompt_template_name)

        # 4. 构建消息
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户问题：{question}\n\n检索到的上下文信息：{context_text}\n\n基于以上内容回答")
        ]

        # 5. 流式调用 LLM
        for chunk in self.llm.stream(messages):
            if chunk.content:
                yield chunk.content

    def _build_sources(self, contexts: list, source_fields: list) -> list:
        """
        根据配置的字段列表动态构建溯源信息
        Dynamically build source tracing information based on configured field list

        Args:
            contexts: 检索结果列表（FastMeSearchResult）/ Retrieval result list (FastMeSearchResult)
            source_fields: 需要返回的字段列表 / List of fields to return

        Returns:
            list: 溯源信息字典列表 / List of source tracing dictionaries
        """
        sources = []
        for item in contexts:
            source_item = {
                "score": getattr(item, "score", None),
                "preview": item.text[:200]
            }

            for field in source_fields:
                # 优先从对象属性取，其次从 metadata 取
                value = getattr(item, field, None)
                if value is None:
                    value = item.metadata.get(field)
                if value is not None:
                    source_item[field] = value

            sources.append(source_item)

        return sources

    # ========== 记忆管理 ==========

    def create_memory(self, session_id: str, max_turns: int = 10):
        """
        创建对话记忆
        Create conversation memory

        Args:
            session_id: 会话 ID / Session ID
            max_turns: 最大保留轮次 / Maximum turns to retain
        """
        self.memories[session_id] = ConversationBufferWindowMemory(
            k=max_turns,
            return_messages=True
        )
        self.memory_configs[session_id] = max_turns

    def get_memory(self, session_id: str) -> Optional[ConversationBufferWindowMemory]:
        """
        获取会话记忆
        Get session memory

        Args:
            session_id: 会话 ID / Session ID

        Returns:
            对话记忆对象，不存在则返回 None / Conversation memory object, or None if not found
        """
        return self.memories.get(session_id)

    def clear_memory(self, session_id: str = None):
        """
        清除记忆
        Clear memory

        Args:
            session_id: 会话 ID，None 则清除所有 / Session ID, None clears all
        """
        if session_id is not None:
            self.memories.pop(session_id, None)
            self.memory_configs.pop(session_id, None)
        else:
            self.memories.clear()
            self.memory_configs.clear()

    def chat_with_memory(
        self,
        question: str,
        session_id: str,
        scene: str = "default",
        filters: Optional[dict] = None,
        top_k: Optional[int] = None
    ) -> dict:
        """
        带记忆的对话
        Chat with memory

        Args:
            question (str): 用户问题 / User question
            session_id (str): 会话 ID / Session ID
            scene (str): 场景名称 / Scene name
            filters (dict, optional): 过滤条件 / Filter conditions
            top_k (int, optional): 召回数量 / Retrieval count

        Returns:
            dict: 对话结果，包含 question, scene, answer, sources / Conversation result containing question, scene, answer, sources
        """
        # 如果没有记忆，创建一个新的
        if session_id not in self.memories:
            self.create_memory(session_id)

        memory = self.memories[session_id]

        # 加载历史对话
        history = memory.load_memory_variables({})
        history_messages = history.get("history", [])

        # 构建带历史的 Prompt
        if history_messages:
            # 根据 max_turns 配置决定取多少条历史消息（每轮2条：Human + AI）
            max_turns = self.memory_configs.get(session_id, 10)
            max_history_messages = max_turns * 2
            history_text = "\n".join([
                f"{msg.type}: {msg.content}"
                for msg in history_messages[-max_history_messages:]
            ])
            question_with_history = f"历史对话:\n{history_text}\n\n当前问题：{question}"
        else:
            question_with_history = question

        # 执行对话（调用内部 chat 方法）
        result = self.chat(
            question=question_with_history,
            scene=scene,
            filters=filters,
            top_k=top_k
        )

        # 保存记忆
        memory.save_context(
            {"input": question},
            {"output": result["answer"]}
        )

        return result
