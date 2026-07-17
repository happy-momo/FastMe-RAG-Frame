"""
场景路由模块
Scene Router Module

根据查询场景路由到对应配置，构建 FilterCondition 过滤条件列表。
Routes queries to corresponding scene configurations and builds FilterCondition lists.
"""

import yaml
from pathlib import Path
from typing import List, Optional

from core.retriever import FilterCondition


class SceneRouter:
    """
    查询场景路由器
    Query Scene Router

    支持场景：
    Supported scenes:
    - fault_diagnosis: 故障诊断（基于运维日志、故障记录）
      Fault diagnosis (based on operation logs and fault records)
    - manual_query: 设备手册查询
      Equipment manual query
    - work_order_trace: 工单追溯
      Work order tracing
    - default: 默认问答
      Default Q&A

    配置来源：config/scenes.yaml
    Configuration source: config/scenes.yaml

    输出格式：FilterCondition 列表（框架内部标准格式）
    Output format: FilterCondition list (framework internal standard format)
    """

    def __init__(self, config_path: str | None = None):
        """
        初始化场景路由器
        Initialize scene router

        Args:
            config_path: 配置文件路径，为 None 时使用默认路径 / Config file path, uses default path when None
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "scenes.yaml"

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self.scene_config = config.get("scenes", {})

    def route(self, scene: str) -> dict:
        """
        路由到指定场景配置
        Route to the specified scene configuration

        Args:
            scene: 场景名称 / Scene name

        Returns:
            场景配置字典 / Scene configuration dict
        """
        return self.scene_config.get(scene, self.scene_config.get("default", {}))

    def build_filter(
        self,
        scene: str,
        user_filter: dict | None = None
    ) -> Optional[List[FilterCondition]]:
        """
        构建 FilterCondition 过滤条件列表
        Build FilterCondition list

        直接输出框架内部标准格式，避免中间转换层。
        Directly outputs framework internal standard format, avoiding intermediate conversion.

        Args:
            scene: 场景名称 / Scene name
            user_filter: 用户自定义过滤条件（简单键值对） / User-defined filter conditions (simple key-value pairs)

        Returns:
            FilterCondition 列表，None 表示不过滤 / FilterCondition list, None means no filtering

        Example:
            >>> router = SceneRouter()
            >>> conditions = router.build_filter("comprehensive_search")
            >>> # 返回: [FilterCondition(field="doc_type", operator="$in", value=["log", "manual"])]
        """
        route = self.route(scene)
        conditions = []

        # 1. 处理 doc_type 过滤
        # Handle doc_type filter
        doc_type = route.get("doc_type")

        if doc_type:
            if isinstance(doc_type, list):
                # 列表格式 → $in 操作符
                # List format → $in operator
                conditions.append(FilterCondition(
                    field="doc_type",
                    operator="$in",
                    value=doc_type
                ))
            elif isinstance(doc_type, dict):
                # 字典格式 → 提取操作符和值
                # Dict format → extract operator and value
                for op, value in doc_type.items():
                    conditions.append(FilterCondition(
                        field="doc_type",
                        operator=op,
                        value=value
                    ))
            else:
                # 单值字符串 → $eq 操作符
                # Single string → $eq operator
                conditions.append(FilterCondition(
                    field="doc_type",
                    operator="$eq",
                    value=doc_type
                ))

        # 2. 处理用户自定义过滤条件
        # Handle user-defined filter conditions
        if user_filter:
            for field, value in user_filter.items():
                conditions.append(FilterCondition(
                    field=field,
                    operator="$eq",
                    value=value
                ))

        return conditions if conditions else None

    def get_source_fields(self, scene: str) -> list:
        """
        获取指定场景的溯源字段配置
        Get source field configuration for the specified scene

        Args:
            scene: 场景名称 / Scene name

        Returns:
            溯源字段列表 / List of source fields
        """
        route = self.route(scene)
        return route.get("source_fields", ["chunk_id", "doc_id", "doc_type", "source"])
