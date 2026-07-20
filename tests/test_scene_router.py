"""
SceneRouter 单元测试
"""

import pytest
from pathlib import Path

from routers.scene_router import SceneRouter
from core.retriever import FilterCondition


class TestSceneRouter:
    """SceneRouter 测试类"""

    @pytest.fixture
    def router(self):
        """创建 SceneRouter 实例"""
        config_path = Path(__file__).parent.parent / "config" / "scenes.yaml"
        return SceneRouter(config_path=str(config_path))

    def test_route_exists(self, router):
        """测试路由是否存在"""
        # 测试默认场景
        route = router.route("default")
        assert route is not None
        assert "doc_type" in route
        assert "prompt_template" in route
        assert "top_k" in route
        assert "source_fields" in route

    def test_fault_diagnosis_scene(self, router):
        """测试故障诊断场景"""
        route = router.route("fault_diagnosis")
        assert route["doc_type"] == "log"
        assert route["prompt_template"] == "fault_diagnosis"
        assert route["top_k"] == 5
        assert "device_id" in route["source_fields"]
        assert "fault_code" in route["source_fields"]

    def test_manual_query_scene(self, router):
        """测试设备手册查询场景"""
        route = router.route("manual_query")
        assert route["doc_type"] == "manual"
        assert route["prompt_template"] == "manual_query"
        assert "source" in route["source_fields"]
        assert "file_path" in route["source_fields"]

    def test_work_order_trace_scene(self, router):
        """测试工单追溯场景"""
        route = router.route("work_order_trace")
        assert route["doc_type"] == "business"
        assert route["prompt_template"] == "work_order_trace"
        assert "work_order_id" in route["source_fields"]
        assert "material_id" in route["source_fields"]

    def test_get_source_fields(self, router):
        """测试获取溯源字段"""
        fields = router.get_source_fields("fault_diagnosis")
        assert isinstance(fields, list)
        assert len(fields) > 0
        assert "chunk_id" in fields
        assert "device_id" in fields

    def test_build_filter(self, router):
        """测试构建过滤器"""
        # 测试故障诊断场景的过滤器
        conditions = router.build_filter("fault_diagnosis")

        # 验证返回 FilterCondition 列表
        assert conditions is not None
        assert isinstance(conditions, list)
        assert len(conditions) == 1

        # 验证 FilterCondition 内容
        condition = conditions[0]
        assert isinstance(condition, FilterCondition)
        assert condition.field == "doc_type"
        assert condition.operator == "$eq"
        assert condition.value == "log"

    def test_build_filter_with_user_filter(self, router):
        """测试带用户自定义过滤"""
        user_filter = {"device_id": "EQ001"}
        conditions = router.build_filter("fault_diagnosis", user_filter=user_filter)

        # 验证返回两个条件
        assert conditions is not None
        assert len(conditions) == 2

        # 验证 doc_type 条件
        doc_type_condition = [c for c in conditions if c.field == "doc_type"][0]
        assert doc_type_condition.operator == "$eq"
        assert doc_type_condition.value == "log"

        # 验证 device_id 条件
        device_condition = [c for c in conditions if c.field == "device_id"][0]
        assert device_condition.operator == "$eq"
        assert device_condition.value == "EQ001"

    def test_default_scene_fallback(self, router):
        """测试默认场景回退"""
        # 测试不存在的场景，应该回退到 default
        route = router.route("non_existent_scene")
        assert route is not None
        # default 场景的 doc_type 为 None
        assert route.get("doc_type") is None

    def test_get_source_fields_default(self, router):
        """测试默认场景的溯源字段"""
        fields = router.get_source_fields("default")
        assert isinstance(fields, list)
        assert "chunk_id" in fields
        assert "doc_id" in fields
        assert "source" in fields

    def test_build_filter_default_scene(self, router):
        """测试默认场景的过滤器（无过滤）"""
        conditions = router.build_filter("default")

        # default 场景的 doc_type 为 None，应该返回 None
        assert conditions is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
