"""
配置加载器
Configuration Loader

负责加载和验证配置文件。
Responsible for loading and validating configuration files.
"""

import os
import re
import copy
import yaml
import json
from pathlib import Path
from typing import Union, Dict, Any, Optional, List

from config.types import FastMeRAGConfig


class ConfigLoader:
    """
    配置加载器
    Configuration Loader

    支持 YAML 和 JSON 格式的配置文件加载。
    Supports YAML and JSON configuration file formats.

    支持 ${VAR_NAME} 语法引用环境变量。
    Supports ${VAR_NAME} syntax for environment variable references.

    Example:
        >>> loader = ConfigLoader()
        >>> config = loader.load("./config/fastme_chroma.yaml")
    """

    # 环境变量引用正则 / Environment variable reference regex
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')

    @classmethod
    def load(
        cls,
        config_path: Union[str, Path],
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        加载配置文件
        Load configuration file

        Args:
            config_path: 配置文件路径 (.yaml/.yml/.json)
                         / Configuration file path
            overrides: 覆盖配置（会合并到原配置）
                       / Override configuration (merged into original)

        Returns:
            配置字典 / Configuration dictionary

        Raises:
            FileNotFoundError: 配置文件不存在 / Config file not found
            ValueError: 配置文件格式错误 / Invalid config file format

        Example:
            >>> config = ConfigLoader.load("./config/fastme_chroma.yaml")
            >>> config = ConfigLoader.load(
            ...     "./config/fastme.yaml",
            ...     overrides={"vector_store": {"type": "faiss"}}
            ... )
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        # 根据扩展名加载 / Load based on file extension
        if path.suffix.lower() in ['.yaml', '.yml']:
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        elif path.suffix.lower() == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")

        # 展开环境变量引用 / Expand environment variable references
        config = cls._expand_env_vars(config)

        # 合并覆盖配置 / Merge override configuration
        if overrides:
            config = cls._deep_merge(config, overrides)

        # 验证配置 / Validate configuration
        cls._validate_config(config)

        return config

    @classmethod
    def from_dict(
        cls,
        config_dict: Dict[str, Any],
        expand_env: bool = True,
    ) -> Dict[str, Any]:
        """
        从字典加载配置
        Load configuration from dictionary

        Args:
            config_dict: 配置字典 / Configuration dictionary
            expand_env: 是否展开环境变量引用，默认 True
                        / Whether to expand environment variables, default True

        Returns:
            配置字典 / Configuration dictionary

        Example:
            >>> config = ConfigLoader.from_dict({
            ...     "vector_store": {"type": "chroma"},
            ...     "embedding": {"model_name": "BAAI/bge-m3"},
            ...     "llm": {"model_name": "qwen-plus"}
            ... })
        """
        config = config_dict.copy()

        if expand_env:
            config = cls._expand_env_vars(config)

        cls._validate_config(config)

        return config

    @classmethod
    def _expand_env_vars(cls, config: Any) -> Any:
        """
        展开配置中的环境变量引用 ${VAR_NAME}
        Expand environment variable references ${VAR_NAME} in configuration

        Args:
            config: 配置对象（可以是 dict/list/str）
                    / Configuration object (can be dict/list/str)

        Returns:
            展开后的配置 / Expanded configuration

        Note:
            如果环境变量不存在，保持原样（不报错）
            If environment variable doesn't exist, keep original (no error)

        Example:
            >>> os.environ['TEST_KEY'] = 'secret'
            >>> ConfigLoader._expand_env_vars({"api_key": "${TEST_KEY}"})
            {'api_key': 'secret'}
        """
        if isinstance(config, dict):
            return {k: cls._expand_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [cls._expand_env_vars(item) for item in config]
        elif isinstance(config, str):
            def replace_env(match):
                env_var = match.group(1)
                return os.getenv(env_var, match.group(0))

            return cls.ENV_VAR_PATTERN.sub(replace_env, config)
        else:
            return config

    @classmethod
    def _deep_merge(
        cls,
        base: Dict[str, Any],
        override: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        深度合并两个字典
        Deep merge two dictionaries

        Args:
            base: 基础字典 / Base dictionary
            override: 覆盖字典 / Override dictionary

        Returns:
            合并后的字典 / Merged dictionary

        Note:
            嵌套字典会递归合并，其他类型直接覆盖
            Nested dicts are recursively merged, other types are overwritten
            返回值为完全独立的深拷贝，修改结果不会影响 base / override
            The returned dict is a fully independent deepcopy; mutating it
            does not affect base or override

        Example:
            >>> base = {"a": 1, "b": {"c": 2}}
            >>> override = {"b": {"d": 3}}
            >>> ConfigLoader._deep_merge(base, override)
            {'a': 1, 'b': {'c': 2, 'd': 3}}
        """
        # 深拷贝 base，确保未覆盖的嵌套字典不与 base 共享引用
        # Deepcopy base so non-overridden nested dicts are not shared with base
        result = copy.deepcopy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # result[key] 已是独立拷贝，原地合并 override 即可
                # result[key] is already an independent copy; merge override in place
                cls._merge_inplace(result[key], value)
            else:
                result[key] = copy.deepcopy(value)

        return result

    @classmethod
    def _merge_inplace(
        cls,
        target: Dict[str, Any],
        override: Dict[str, Any],
    ) -> None:
        """
        将 override 原地合并到 target（target 由调用方独占）
        Merge override into target in place (target is owned by the caller)

        与 _deep_merge 配合使用，避免对已深拷贝的嵌套字典重复深拷贝。
        Used together with _deep_merge to avoid deepcopying already-copied nested dicts.

        Args:
            target: 目标字典（会被原地修改）/ Target dict (modified in place)
            override: 覆盖字典 / Override dict
        """
        for key, value in override.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                cls._merge_inplace(target[key], value)
            else:
                target[key] = copy.deepcopy(value)

    @classmethod
    def _validate_config(cls, config: Dict[str, Any]) -> None:
        """
        校验配置的有效性(委托 Pydantic)
        Validate configuration correctness (via Pydantic).

        Args:
            config: 配置字典 / Configuration dictionary

        Raises:
            ValueError: 配置无效 / Configuration invalid
        """
        try:
            FastMeRAGConfig.model_validate(config)
        except Exception as e:
            raise ValueError(str(e)) from e

