"""打包与版本相关测试"""
import re

import app_factory


def test_version_exists_and_semver():
    assert hasattr(app_factory, "__version__"), "app_factory 必须暴露 __version__"
    assert re.match(r"^\d+\.\d+\.\d+", app_factory.__version__), \
        f"非法版本号: {app_factory.__version__!r}"
