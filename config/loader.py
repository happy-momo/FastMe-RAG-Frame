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
            3. vector_store.config 必须包含对应类型的必要字段
               vector_store.config must contain required fields for the type
            4. embedding 和 embedding.model_name 必须存在
               embedding and embedding.model_name must exist
            5. llm 和 llm.model_name 必须存在
               llm and llm.model_name must exist

        Example:
            >>> ConfigLoader._validate_config({
            ...     "vector_store": {"type": "chroma", "config": {"persist_directory": "./data/chroma"}},
            ...     "embedding": {"model_name": "BAAI/bge-m3"},
            ...     "llm": {"model_name": "qwen-plus"}
            ... })  # No exception raised
        """
        # 验证 vector_store / Validate vector_store
        cls._validate_vector_store_config(config.get("vector_store", {}))

        # 验证 embedding / Validate embedding
        cls._validate_embedding_config(config.get("embedding", {}))

        # 验证 llm / Validate llm
        cls._validate_llm_config(config.get("llm", {}))

        # 验证 chunking 配置（可选） / Validate chunking config (optional)
        cls._validate_chunking_config(config.get("chunking", {}))

    @classmethod
    def _validate_vector_store_config(cls, vs_config: Dict[str, Any]) -> None:
        """
        验证向量库配置
        Validate vector store configuration

        Args:
            vs_config: 向量库配置字典 / Vector store configuration dictionary

        Raises:
            ValueError: 配置无效 / Configuration invalid
        """
        if not vs_config:
            raise ValueError("Missing required config: 'vector_store'")

        if 'type' not in vs_config:
            raise ValueError("Missing required config: 'vector_store.type'")

        valid_types = ['chroma', 'faiss', 'milvus', 'qdrant', 'weaviate']
        if vs_config['type'] not in valid_types:
            raise ValueError(
                f"Invalid vector_store.type: {vs_config['type']}. "
                f"Valid types: {valid_types}"
            )

        # 验证向量库特定配置 / Validate vector store specific config
        vs_specific_config = vs_config.get("config", {})
        vs_type = vs_config['type']

        if vs_type == 'chroma':
            if 'persist_directory' not in vs_specific_config:
                raise ValueError(
                    "Chroma vector store requires 'persist_directory' in vector_store.config. "
                    "Example: {\"persist_directory\": \"./data/chroma\"}"
                )
        elif vs_type == 'faiss':
            if 'index_path' not in vs_specific_config:
                raise ValueError(
                    "FAISS vector store requires 'index_path' in vector_store.config. "
                    "Example: {\"index_path\": \"./data/faiss_index\"}"
                )
        # milvus, qdrant, weaviate 未来扩展时添加验证
        # Add validation for milvus, qdrant, weaviate when extended

    @classmethod
    def _validate_embedding_config(cls, emb_config: Dict[str, Any]) -> None:
        """
        验证 Embedding 配置
        Validate embedding configuration

        Args:
            emb_config: Embedding 配置字典 / Embedding configuration dictionary

        Raises:
            ValueError: 配置无效 / Configuration invalid
        """
        if not emb_config:
            raise ValueError("Missing required config: 'embedding'")

        if 'model_name' not in emb_config:
            raise ValueError(
                "Missing required config: 'embedding.model_name'. "
                "Example: {\"model_name\": \"BAAI/bge-m3\"}"
            )

        # 验证 model_name 不为空
        if not emb_config['model_name']:
            raise ValueError("'embedding.model_name' cannot be empty")

    @classmethod
    def _validate_llm_config(cls, llm_config: Dict[str, Any]) -> None:
        """
        验证 LLM 配置
        Validate LLM configuration

        Args:
            llm_config: LLM 配置字典 / LLM configuration dictionary

        Raises:
            ValueError: 配置无效 / Configuration invalid
        """
        if not llm_config:
            raise ValueError("Missing required config: 'llm'")

        if 'model_name' not in llm_config:
            raise ValueError(
                "Missing required config: 'llm.model_name'. "
                "Example: {\"model_name\": \"qwen-plus\"}"
            )

        # 验证 model_name 不为空
        if not llm_config['model_name']:
            raise ValueError("'llm.model_name' cannot be empty")

        # 验证 base_url 格式（如果存在）
        base_url = llm_config.get('base_url')
        if base_url and not base_url.startswith(('http://', 'https://')):
            raise ValueError(
                f"Invalid 'llm.base_url' format: {base_url}. "
                "Must start with http:// or https://"
            )

        # 验证 temperature 范围（如果存在）
        temperature = llm_config.get('temperature')
        if temperature is not None:
            if not (0 <= temperature <= 2):
                raise ValueError(
                    f"Invalid 'llm.temperature': {temperature}. "
                    "Must be between 0 and 2"
                )

    @classmethod
    def _validate_chunking_config(cls, chunking_config: Dict[str, Any]) -> None:
        """
        验证 Chunking 配置
        Validate chunking configuration

        Args:
            chunking_config: Chunking 配置字典 / Chunking configuration dictionary

        Raises:
            ValueError: 配置无效 / Configuration invalid
        """
        if not chunking_config:
            return  # chunking 是可选配置 / chunking is optional

        default_max_size = chunking_config.get('default_max_size')
        if default_max_size is not None:
            if not isinstance(default_max_size, int) or default_max_size <= 0:
                raise ValueError(
                    f"Invalid 'chunking.default_max_size': {default_max_size}. "
                    "Must be a positive integer"
                )

        by_type = chunking_config.get('by_type')
        if by_type is not None:
            if not isinstance(by_type, dict):
                raise ValueError(
                    f"Invalid 'chunking.by_type': {by_type}. "
                    "Must be a dictionary"
                )
            for doc_type, size in by_type.items():
                if not isinstance(size, int) or size <= 0:
                    raise ValueError(
                        f"Invalid chunk size for '{doc_type}': {size}. "
                        "Must be a positive integer"
                    )
