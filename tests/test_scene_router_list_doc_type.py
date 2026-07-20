"""
测试 SceneRouter 对列表格式 doc_type 的支持
Test SceneRouter support for list-format doc_type
"""

import pytest
from pathlib import Path

from routers.scene_router import SceneRouter
from core.retriever import FilterCondition


class TestSceneRouterListDocType:
    """
    测试 SceneRouter 的 doc_type 列表支持
    Test SceneRouter's doc_type list support
    """

    def test_single_string_doc_type(self, tmp_path):
        """
        测试单值字符串 doc_type（向后兼容）
        Test single string doc_type (backward compatibility)
        """
        config_file = tmp_path / "test_scenes.yaml"
        config_file.write_text("""
scenes:
  fault_diagnosis:
    doc_type: log
    prompt_template: fault_diagnosis
    top_k: 5
  default:
    doc_type: null
    top_k: 5
""")
        router = SceneRouter(config_path=str(config_file))

        # 构建过滤器
        conditions = router.build_filter("fault_diagnosis")

        # 验证：单值字符串转换为 $eq
        assert conditions is not None
        assert len(conditions) == 1
        assert conditions[0].field == "doc_type"
        assert conditions[0].operator == "$eq"
        assert conditions[0].value == "log"

    def test_list_doc_type(self, tmp_path):
        """
        测试列表格式 doc_type
        Test list-format doc_type
        """
        config_file = tmp_path / "test_scenes.yaml"
        config_file.write_text("""
scenes:
  comprehensive_search:
    doc_type:
      - log
      - manual
    prompt_template: comprehensive
    top_k: 10
  default:
    doc_type: null
    top_k: 5
""")
        router = SceneRouter(config_path=str(config_file))

        # 构建过滤器
        conditions = router.build_filter("comprehensive_search")

        # 验证：列表转换为 $in 操作符
        assert conditions is not None
        assert len(conditions) == 1
        assert conditions[0].field == "doc_type"
        assert conditions[0].operator == "$in"
        assert conditions[0].value == ["log", "manual"]

    def test_list_doc_type_with_three_types(self, tmp_path):
        """
        测试包含三个类型的列表
        Test list with three types
        """
        config_file = tmp_path / "test_scenes.yaml"
        config_file.write_text("""
scenes:
  knowledge_base:
    doc_type:
      - log
      - manual
      - business
    prompt_template: default
    top_k: 5
  default:
    doc_type: null
    top_k: 5
""")
        router = SceneRouter(config_path=str(config_file))

        conditions = router.build_filter("knowledge_base")

        assert conditions is not None
        assert len(conditions) == 1
        assert conditions[0].field == "doc_type"
        assert conditions[0].operator == "$in"
        assert conditions[0].value == ["log", "manual", "business"]

    def test_null_doc_type(self, tmp_path):
        """
        测试 null doc_type（不过滤）
        Test null doc_type (no filtering)
        """
        config_file = tmp_path / "test_scenes.yaml"
        config_file.write_text("""
scenes:
  default:
    doc_type: null
    prompt_template: default
    top_k: 5
""")
        router = SceneRouter(config_path=str(config_file))

        conditions = router.build_filter("default")

        # 验证：null 不过滤
        assert conditions is None

    def test_list_doc_type_with_user_filter(self, tmp_path):
        """
        测试列表 doc_type 结合用户过滤条件
        Test list doc_type combined with user filter
        """
        config_file = tmp_path / "test_scenes.yaml"
        config_file.write_text("""
scenes:
  comprehensive_search:
    doc_type:
      - log
      - manual
    prompt_template: comprehensive
    top_k: 10
  default:
    doc_type: null
    top_k: 5
""")
        router = SceneRouter(config_path=str(config_file))

        # 添加用户过滤条件
        conditions = router.build_filter(
            "comprehensive_search",
            user_filter={"device_id": "EQ001"}
        )

        # 验证：两个条件都存在
        assert conditions is not None
        assert len(conditions) == 2

        # 检查 doc_type 条件
        doc_type_condition = [c for c in conditions if c.field == "doc_type"][0]
        assert doc_type_condition.operator == "$in"
        assert doc_type_condition.value == ["log", "manual"]

        # 检查 device_id 条件
        device_condition = [c for c in conditions if c.field == "device_id"][0]
        assert device_condition.operator == "$eq"
        assert device_condition.value == "EQ001"

    def test_single_item_list_doc_type(self, tmp_path):
        """
        测试单元素列表（转换为 $in）
        Test single-item list (converted to $in)
        """
        config_file = tmp_path / "test_scenes.yaml"
        config_file.write_text("""
scenes:
  log_only:
    doc_type:
      - log
    prompt_template: default
    top_k: 5
  default:
    doc_type: null
    top_k: 5
""")
        router = SceneRouter(config_path=str(config_file))

        conditions = router.build_filter("log_only")

        # 验证：单元素列表转换为 $in
        assert conditions is not None
        assert len(conditions) == 1
        assert conditions[0].operator == "$in"
        assert conditions[0].value == ["log"]

    def test_empty_doc_type_field(self, tmp_path):
        """
        测试没有 doc_type 字段的场景
        Test scene without doc_type field
        """
        config_file = tmp_path / "test_scenes.yaml"
        config_file.write_text("""
scenes:
  no_filter:
    prompt_template: default
    top_k: 5
  default:
    doc_type: null
    top_k: 5
""")
        router = SceneRouter(config_path=str(config_file))

        conditions = router.build_filter("no_filter")

        # 验证：无 doc_type 字段时不过滤
        assert conditions is None

    def test_mixed_scenes(self, tmp_path):
        """
        测试混合场景配置
        Test mixed scene configuration
        """
        config_file = tmp_path / "test_scenes.yaml"
        config_file.write_text("""
scenes:
  fault_diagnosis:
    doc_type: log
    top_k: 5

  comprehensive_search:
    doc_type:
      - log
      - manual
      - business
    top_k: 10

  default:
    doc_type: null
    top_k: 5
""")
        router = SceneRouter(config_path=str(config_file))

        # 测试单值场景
        conditions = router.build_filter("fault_diagnosis")
        assert conditions is not None
        assert conditions[0].operator == "$eq"
        assert conditions[0].value == "log"

        # 测试列表场景
        conditions = router.build_filter("comprehensive_search")
        assert conditions is not None
        assert conditions[0].operator == "$in"
        assert conditions[0].value == ["log", "manual", "business"]

        # 测试默认场景
        conditions = router.build_filter("default")
        assert conditions is None


class TestSceneRouterIntegration:
    """
    集成测试：测试完整的检索链路
    Integration tests: test complete retrieval chain
    """

    def test_filter_condition_usage(self, tmp_path):
        """
        测试 FilterCondition 的使用
        Test FilterCondition usage
        """
        config_file = tmp_path / "test_scenes.yaml"
        config_file.write_text("""
scenes:
  multi_doc_scene:
    doc_type:
      - log
      - manual
    top_k: 5
  default:
    doc_type: null
    top_k: 5
""")
        router = SceneRouter(config_path=str(config_file))

        # 构建 FilterCondition
        conditions = router.build_filter("multi_doc_scene")

        # 验证 FilterCondition 对象
        assert conditions is not None
        assert len(conditions) == 1

        condition = conditions[0]
        assert isinstance(condition, FilterCondition)
        assert condition.field == "doc_type"
        assert condition.operator == "$in"
        assert condition.value == ["log", "manual"]

        # 验证 FilterCondition 可以直接传给 Retriever
        # （这是优化后的设计目标）
        from vector_stores.chroma_retriever import ChromaRetriever

        # ChromaRetriever._to_chroma_filter() 接收 List[FilterCondition]
        chroma_filter = ChromaRetriever(None)._to_chroma_filter(conditions)

        # 最终转换为 Chroma 语法
        assert chroma_filter == {"doc_type": {"$in": ["log", "manual"]}}

    def test_faiss_filter_handling(self, tmp_path):
        """
        测试 FAISS 后过滤支持
        Test FAISS post-filter support
        """
        from vector_stores.faiss_retriever import FAISSRetriever

        # 直接创建 FilterCondition（模拟 SceneRouter 输出）
        conditions = [
            FilterCondition(field="doc_type", operator="$in", value=["log", "manual"])
        ]

        # 测试 _match_condition 方法
        retriever = FAISSRetriever(None)

        # 匹配的值
        assert retriever._match_condition("log", "$in", ["log", "manual"]) is True
        assert retriever._match_condition("manual", "$in", ["log", "manual"]) is True

        # 不匹配的值
        assert retriever._match_condition("business", "$in", ["log", "manual"]) is False
        assert retriever._match_condition("sop", "$in", ["log", "manual"]) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
