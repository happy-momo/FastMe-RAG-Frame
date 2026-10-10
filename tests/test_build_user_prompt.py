"""build_user_prompt 接线测试"""
import os
import tempfile
import yaml

import pytest

from core.models import FastMeSearchResult


@pytest.fixture
def ctx():
    return FastMeSearchResult(
        chunk_id="c0", doc_id="d0", doc_type="manual",
        text="设备启动步骤", score=0.9,
        metadata={"source": "manual.pdf", "chapter_num": "1"},
    )


def test_build_user_prompt_contains_question_and_context(ctx):
    from adapters.prompt_adapter import PromptAdapter

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False,
                                     encoding="utf-8") as f:
        yaml.dump({"default": {"system": "sys"}}, f)
        prompt_path = f.name
    try:
        pa = PromptAdapter(path=prompt_path)
        out = pa.build_user_prompt("问题", [ctx], ["source", "chapter_num"])
        assert "问题" in out
        assert "设备启动步骤" in out
        assert "manual.pdf" in out
        assert "[片段 1]" in out
    finally:
        os.unlink(prompt_path)