"""
配置加载器
Configuration Loader

负责加载和验证配置文件。
Responsible for loading and validating configuration files.
"""

import os
import re
import yaml
import json
from pathlib import Path
from typing import Union, Dict, Any, Optional, List


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

        Example:
            >>> base = {"a": 1, "b": {"c": 2}}
            >>> override = {"b": {"d": 3}}
            >>> ConfigLoader._deep_merge(base, override)
            {'a': 1, 'b': {'c': 2, 'd': 3}}
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = cls._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    @classmethod
    def _validate_config(cls, config: Dict[str, Any]) -> None:
        """
        验证配置的有效性
        Validate configuration correctness

        Args:
            config: 配置字典 / Configuration dictionary

        Raises:
            ValueError: 配置无效 / Configuration invalid

        Note:
            验证规则：
            Validation rules:
            1. vector_store 和 vector_store.type 必须存在
               vector_store and vector_store.type must exist
            2. vector_store.type 必须是支持的值
               vector_store.type must be a supported value
            3. embedding 和 embedding.model_name 必须存在
               embedding and embedding.model_name must exist
            4. llm 和 llm.model_name 必须存在
               llm and llm.model_name must exist

        Example:
            >>> ConfigLoader._validate_config({
            ...     "vector_store": {"type": "chroma"},
            ...     "embedding": {"model_name": "BAAI/bge-m3"},
            ...     "llm": {"model_name": "qwen-plus"}
            ... })  # No exception raised
        """
        # 验证 vector_store / Validate vector_store
        if 'vector_store' not in config:
            raise ValueError("Missing required config: 'vector_store'")

        vs_config = config['vector_store']
        if 'type' not in vs_config:
            raise ValueError("Missing required config: 'vector_store.type'")

        valid_types = ['chroma', 'faiss', 'milvus', 'qdrant', 'weaviate']
        if vs_config['type'] not in valid_types:
            raise ValueError(
                f"Invalid vector_store.type: {vs_config['type']}. "
                f"Valid types: {valid_types}"
            )

        # 验证 embedding / Validate embedding
        if 'embedding' not in config:
            raise ValueError("Missing required config: 'embedding'")

        if 'model_name' not in config['embedding']:
            raise ValueError("Missing required config: 'embedding.model_name'")

        # 验证 llm / Validate llm
        if 'llm' not in config:
            raise ValueError("Missing required config: 'llm'")

        if 'model_name' not in config['llm']:
            raise ValueError("Missing required config: 'llm.model_name'")
