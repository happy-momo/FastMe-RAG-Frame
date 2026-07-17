"""
Prompt 适配器模块
Prompt Adapter Module

管理 Prompt 模板和字段标签，支持多语言切换。
Manages Prompt templates and field labels, supporting multi-language switching.
"""

import logging
import yaml
from typing import Dict, Optional

logger = logging.getLogger("fastme_rag")


class PromptAdapter:
    """
    Prompt 适配器
    Prompt Adapter

    管理 Prompt 模板和字段标签，支持多语言切换。
    Manages Prompt templates and field labels, supporting multi-language switching.

    Args:
        path: Prompt 模板文件路径 / Prompt template file path
        field_labels_path: 字段标签文件路径（支持多语言） / Field labels file path (multi-language support)
        language: 初始语言，默认 "zh"（中文） / Initial language, default "zh" (Chinese)

    Example:
        >>> adapter = PromptAdapter(
        ...     path="prompt_templates.yaml",
        ...     field_labels_path="field_labels.yaml",
        ...     language="zh"
        ... )
        >>> adapter.set_language("en")  # 切换为英文 / Switch to English
    """

    def __init__(self, path: str, field_labels_path: str = None, language: str = "zh"):
        with open(path, "r", encoding="utf-8") as f:
            self.templates = yaml.safe_load(f)

        # 加载字段标签配置（支持多语言）
        self._all_field_labels: Dict[str, Dict] = {}
        self._current_language = language

        if field_labels_path:
            with open(field_labels_path, "r", encoding="utf-8") as f:
                self._all_field_labels = yaml.safe_load(f)

        # 设置当前语言的字段标签
        self.field_labels = self._get_labels_for_language(language)

    def _get_labels_for_language(self, language: str) -> Dict[str, str]:
        """
        获取指定语言的字段标签
        Get field labels for the specified language

        Args:
            language: 语言代码 ("zh" | "en") / Language code ("zh" | "en")

        Returns:
            字段标签字典 / Field labels dictionary
        """
        if not self._all_field_labels:
            return {}

        # 优先返回指定语言的标签，如果没有则返回中文，最后返回空字典
        return self._all_field_labels.get(language, self._all_field_labels.get("zh", {}))

    def set_language(self, language: str):
        """
        切换语言
        Switch language

        Args:
            language: 语言代码 ("zh" | "en") / Language code ("zh" | "en")

        Raises:
            ValueError: 当不支持该语言时 / When the language is not supported
        """
        if language not in ["zh", "en"]:
            raise ValueError(f"Unsupported language: {language}. Supported: zh, en")

        self._current_language = language
        self.field_labels = self._get_labels_for_language(language)

    def get_language(self) -> str:
        """
        获取当前语言设置
        Get current language setting

        Returns:
            当前语言代码 ("zh" 或 "en") / Current language code ("zh" or "en")
        """
        return self._current_language

    def get_system_prompt(self, name: str) -> str:
        """
        获取系统 Prompt 模板
        Get system Prompt template

        Args:
            name: 模板名称 / Template name

        Returns:
            系统 Prompt 文本 / System Prompt text
        """
        template = self.templates.get(name) or self.templates.get("default")
        if template is None:
            logger.warning(f"[PromptAdapter] 未找到模板 '{name}' 和默认模板，使用兜底 Prompt")
            return "你是一个有用的制造业智能助手，请基于检索到的上下文信息准确回答用户问题。"
        system_prompt = template.get("system")
        if system_prompt is None:
            logger.warning(f"[PromptAdapter] 模板 '{name}' 无 system 字段，使用兜底 Prompt")
            return "你是一个有用的制造业智能助手，请基于检索到的上下文信息准确回答用户问题。"
        return system_prompt

    def build_user_prompt(self, question: str, contexts: list, source_fields: list = None) -> str:
        """
        构建用户 Prompt
        Build user Prompt

        Args:
            question: 用户问题 / User question
            contexts: 检索结果列表 / Retrieval result list
            source_fields: 需要显示的字段列表（从场景配置获取） / Fields to display (from scenario config)

        Returns:
            用户 Prompt 文本 / User Prompt text
        """
        context_text = self._format_context(contexts, source_fields)
        return f"""
用户问题：{question}

检索到的上下文信息：{context_text}

基于以上内容回答
""".strip()

    def _format_context(self, contexts: list, source_fields: list = None) -> str:
        """
        格式化检索结果为上下文字符串
        Format retrieval results as context string

        Args:
            contexts: 检索结果列表 / Retrieval result list
            source_fields: 需要显示的字段列表（从场景配置获取） / Fields to display (from scenario config)
                           例如 / For example:
                           - fault_diagnosis: ['device_id', 'fault_code', 'timestamp']
                           - manual_query: ['chapter_num', 'device_model']
                           - work_order_trace: ['work_order_id', 'quality_result']

        Returns:
            格式化的上下文字符串 / Formatted context string
        """
        if not contexts:
            # 根据当前语言返回不同的无结果提示
            no_results_map = {
                "zh": "没有检索到相关上下文信息",
                "en": "No relevant context found"
            }
            return self.field_labels.get("no_results", no_results_map.get(self._current_language, "No relevant context found"))

        parts = []

        for index, item in enumerate(contexts):
            metadata = item.metadata
            field_lines = []

            # 只显示 source_fields 配置的字段
            if source_fields:
                for field in source_fields:
                    value = metadata.get(field)
                    if value is not None:
                        # 从 field_labels 获取标签，没有则用字段名
                        label = self.field_labels.get(field, field)
                        field_lines.append(f"{label}: {value}")
            else:
                # 没有配置时，显示所有非空字段
                for key, value in metadata.items():
                    if value is not None and key not in ["chunk_id", "doc_id"]:
                        label = self.field_labels.get(key, key)
                        field_lines.append(f"{label}: {value}")

            # 组装片段
            if field_lines:
                fields_text = "\n".join(field_lines)
                parts.append(f"""
[片段 {index + 1}]
{fields_text}

内容：
{item.text}
""".strip())
            else:
                parts.append(f"""
[片段 {index + 1}]
内容：
{item.text}
""".strip())

        return "\n\n".join(parts)
            

    
