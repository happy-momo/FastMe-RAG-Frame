"""
配置加载器测试
Configuration Loader Tests

测试 ConfigLoader 类的功能。
Tests for ConfigLoader class functionality.
"""

import os
import pytest
import tempfile
import json
from pathlib import Path

from config.loader import ConfigLoader


class TestConfigLoader:
    """
    ConfigLoader 测试类
    ConfigLoader test class
    """

    def test_load_yaml_config(self):
        """
        测试加载 YAML 配置
        Test loading YAML configuration
        """
        config_content = """
vector_store:
  type: chroma
  config:
    persist_directory: ./data/chroma_test
    collection_name: test_coll
embedding:
  model_name: BAAI/bge-m3
llm:
  model_name: qwen-plus
"""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w', encoding='utf-8') as f:
            f.write(config_content)
            f.flush()
            
            config = ConfigLoader.load(f.name)
            
            assert config['vector_store']['type'] == 'chroma'
            assert config['vector_store']['config']['collection_name'] == 'test_coll'
            assert config['embedding']['model_name'] == 'BAAI/bge-m3'
            assert config['llm']['model_name'] == 'qwen-plus'
            
            Path(f.name).unlink()

    def test_load_json_config(self):
        """
        测试加载 JSON 配置
        Test loading JSON configuration
        """
        config_content = {
            "vector_store": {
                "type": "faiss",
                "config": {"index_path": "./data/faiss_test"}
            },
            "embedding": {"model_name": "BAAI/bge-m3"},
            "llm": {"model_name": "qwen-plus"}
        }
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8') as f:
            json.dump(config_content, f)
            f.flush()
            
            config = ConfigLoader.load(f.name)
            
            assert config['vector_store']['type'] == 'faiss'
            assert config['embedding']['model_name'] == 'BAAI/bge-m3'
            
            Path(f.name).unlink()

    def test_expand_env_vars(self):
        """
        测试环境变量展开
        Test environment variable expansion
        """
        os.environ['TEST_API_KEY'] = 'secret123'
        
        config = {
            'llm': {
                'api_key': '${TEST_API_KEY}'
            }
        }
        
        expanded = ConfigLoader._expand_env_vars(config)
        
        assert expanded['llm']['api_key'] == 'secret123'
        
        # 清理 / Cleanup
        del os.environ['TEST_API_KEY']

    def test_expand_env_vars_not_found(self):
        """
        测试环境变量未找到时保持原样
        Test keeping original when env var not found
        """
        config = {
            'llm': {
                'api_key': '${NON_EXISTENT_VAR}'
            }
        }
        
        expanded = ConfigLoader._expand_env_vars(config)
        
        assert expanded['llm']['api_key'] == '${NON_EXISTENT_VAR}'

    def test_validate_config_missing_vector_store(self):
        """
        测试配置验证 - 缺少 vector_store
        Test configuration validation - missing vector_store
        """
        config = {
            'embedding': {'model_name': 'BAAI/bge-m3'},
            'llm': {'model_name': 'qwen-plus'}
        }
        
        with pytest.raises(ValueError, match="Missing required config: 'vector_store'"):
            ConfigLoader._validate_config(config)

    def test_validate_config_missing_type(self):
        """
        测试配置验证 - 缺少 type
        Test configuration validation - missing type
        """
        config = {
            'vector_store': {'config': {}},
            'embedding': {'model_name': 'BAAI/bge-m3'},
            'llm': {'model_name': 'qwen-plus'}
        }
        
        with pytest.raises(ValueError, match="Missing required config: 'vector_store.type'"):
            ConfigLoader._validate_config(config)

    def test_validate_config_invalid_type(self):
        """
        测试配置验证 - 无效的向量库类型
        Test configuration validation - invalid vector store type
        """
        config = {
            'vector_store': {
                'type': 'invalid_type',
                'config': {}
            },
            'embedding': {'model_name': 'BAAI/bge-m3'},
            'llm': {'model_name': 'qwen-plus'}
        }
        
        with pytest.raises(ValueError, match="Invalid vector_store.type"):
            ConfigLoader._validate_config(config)

    def test_validate_config_missing_embedding(self):
        """
        测试配置验证 - 缺少 embedding
        Test configuration validation - missing embedding
        """
        config = {
            'vector_store': {'type': 'chroma', 'config': {'persist_directory': './data/chroma'}},
            'llm': {'model_name': 'qwen-plus'}
        }

        with pytest.raises(ValueError, match="Missing required config: 'embedding'"):
            ConfigLoader._validate_config(config)

    def test_validate_config_missing_llm(self):
        """
        测试配置验证 - 缺少 llm
        Test configuration validation - missing llm
        """
        config = {
            'vector_store': {'type': 'chroma', 'config': {'persist_directory': './data/chroma'}},
            'embedding': {'model_name': 'BAAI/bge-m3'}
        }

        with pytest.raises(ValueError, match="Missing required config: 'llm'"):
            ConfigLoader._validate_config(config)

    def test_validate_vector_store_missing_config(self):
        """
        测试配置验证 - 向量库缺少必要配置
        Test configuration validation - vector store missing required config
        """
        # Chroma 缺少 persist_directory
        config = {
            'vector_store': {'type': 'chroma', 'config': {}},
            'embedding': {'model_name': 'BAAI/bge-m3'},
            'llm': {'model_name': 'qwen-plus'}
        }

        with pytest.raises(ValueError, match="Chroma vector store requires 'persist_directory'"):
            ConfigLoader._validate_config(config)

        # FAISS 缺少 index_path
        config = {
            'vector_store': {'type': 'faiss', 'config': {}},
            'embedding': {'model_name': 'BAAI/bge-m3'},
            'llm': {'model_name': 'qwen-plus'}
        }

        with pytest.raises(ValueError, match="FAISS vector store requires 'index_path'"):
            ConfigLoader._validate_config(config)

    def test_validate_llm_temperature_range(self):
        """
        测试配置验证 - LLM temperature 范围
        Test configuration validation - LLM temperature range
        """
        config = {
            'vector_store': {'type': 'chroma', 'config': {'persist_directory': './data/chroma'}},
            'embedding': {'model_name': 'BAAI/bge-m3'},
            'llm': {'model_name': 'qwen-plus', 'temperature': 2.5}  # 超出范围
        }

        with pytest.raises(ValueError, match="Invalid 'llm.temperature'"):
            ConfigLoader._validate_config(config)

    def test_validate_chunking_config(self):
        """
        测试配置验证 - Chunking 配置
        Test configuration validation - Chunking configuration
        """
        # 有效的 chunking 配置
        config = {
            'vector_store': {'type': 'chroma', 'config': {'persist_directory': './data/chroma'}},
            'embedding': {'model_name': 'BAAI/bge-m3'},
            'llm': {'model_name': 'qwen-plus'},
            'chunking': {
                'default_max_size': 1000,
                'by_type': {'log': 600, 'manual': 1500}
            }
        }
        ConfigLoader._validate_config(config)  # 不应抛出异常

        # 无效的 default_max_size
        config = {
            'vector_store': {'type': 'chroma', 'config': {'persist_directory': './data/chroma'}},
            'embedding': {'model_name': 'BAAI/bge-m3'},
            'llm': {'model_name': 'qwen-plus'},
            'chunking': {'default_max_size': -100}
        }

        with pytest.raises(ValueError, match="Invalid 'chunking.default_max_size'"):
            ConfigLoader._validate_config(config)

    def test_deep_merge(self):
        """
        测试深度合并
        Test deep merge
        """
        base = {
            'vector_store': {
                'type': 'chroma',
                'config': {
                    'persist_directory': './data/chroma'
                }
            },
            'embedding': {
                'model_name': 'BAAI/bge-m3'
            }
        }
        
        override = {
            'vector_store': {
                'config': {
                    'collection_name': 'new_coll'
                }
            },
            'embedding': {
                'batch_size': 64
            }
        }
        
        merged = ConfigLoader._deep_merge(base, override)
        
        assert merged['vector_store']['type'] == 'chroma'
        assert merged['vector_store']['config']['persist_directory'] == './data/chroma'
        assert merged['vector_store']['config']['collection_name'] == 'new_coll'
        assert merged['embedding']['model_name'] == 'BAAI/bge-m3'
        assert merged['embedding']['batch_size'] == 64

    def test_from_dict(self):
        """
        测试从字典加载配置
        Test loading configuration from dictionary
        """
        config_dict = {
            'vector_store': {'type': 'chroma', 'config': {'persist_directory': './data/chroma_test'}},
            'embedding': {'model_name': 'BAAI/bge-m3'},
            'llm': {'model_name': 'qwen-plus'}
        }

        config = ConfigLoader.from_dict(config_dict)

        assert config['vector_store']['type'] == 'chroma'
        assert config['vector_store']['config']['persist_directory'] == './data/chroma_test'
        assert config['embedding']['model_name'] == 'BAAI/bge-m3'

    def test_load_with_overrides(self):
        """
        测试加载配置并覆盖
        Test loading configuration with overrides
        """
        config_content = """
vector_store:
  type: chroma
  config:
    persist_directory: ./data/chroma_test
    collection_name: original_coll
embedding:
  model_name: BAAI/bge-m3
llm:
  model_name: qwen-plus
"""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False, mode='w', encoding='utf-8') as f:
            f.write(config_content)
            f.flush()
            
            config = ConfigLoader.load(
                f.name,
                overrides={'vector_store': {'config': {'collection_name': 'overridden_coll'}}}
            )
            
            assert config['vector_store']['config']['collection_name'] == 'overridden_coll'
            
            Path(f.name).unlink()

    def test_file_not_found(self):
        """
        测试文件不存在
        Test file not found
        """
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load('/non/existent/path/config.yaml')

    def test_unsupported_format(self):
        """
        测试不支持的文件格式
        Test unsupported file format
        """
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w', encoding='utf-8') as f:
            f.write("some content")
            f.flush()
            
            with pytest.raises(ValueError, match="Unsupported config file format"):
                ConfigLoader.load(f.name)
            
            Path(f.name).unlink()
