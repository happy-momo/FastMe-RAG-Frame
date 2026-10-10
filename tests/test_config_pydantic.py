"""config/types.py Pydantic 校验测试"""
import pytest
from config.types import FastMeRAGConfig


def _base():
    return {
        "vector_store": {"type": "chroma",
                         "config": {"persist_directory": "./d", "collection_name": "c"}},
        "embedding": {"model_name": "BAAI/bge-m3"},
        "llm": {"model_name": "qwen", "base_url": "http://x", "temperature": 0.2},
    }


def test_valid_config_roundtrip():
    m = FastMeRAGConfig.model_validate(_base())
    assert m.vector_store.type == "chroma"
    assert m.llm.temperature == 0.2


def test_invalid_llm_base_url():
    cfg = _base(); cfg["llm"]["base_url"] = "ftp://x"
    with pytest.raises(Exception):
        FastMeRAGConfig.model_validate(cfg)


def test_invalid_temperature_range():
    cfg = _base(); cfg["llm"]["temperature"] = 5
    with pytest.raises(Exception):
        FastMeRAGConfig.model_validate(cfg)


def test_chroma_requires_persist_dir():
    cfg = _base(); cfg["vector_store"]["config"] = {}
    with pytest.raises(ValueError):
        FastMeRAGConfig.model_validate(cfg)