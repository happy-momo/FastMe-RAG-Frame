"""
路由模块
Routers Module

提供场景路由和过滤构建功能。
Provides scene routing and filter building functionality.

可用组件：
Available components:
- SceneRouter: 场景路由器（管理场景配置和过滤构建）
  Scene router (manages scene configuration and filter building)

Example:
    >>> from routers import SceneRouter
    >>> router = SceneRouter()
    >>> scene_config = router.route("fault_diagnosis")
    >>> where_filter = router.build_filter(scene="fault_diagnosis", user_filter={"device_id": "EQ001"})
"""

from routers.scene_router import SceneRouter

__all__ = ["SceneRouter"]
