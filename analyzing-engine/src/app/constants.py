import sys
from pathlib import Path


def _resolve_project_root_dir() -> Path:
    """
    优先按启动入口定位项目根目录，兼容源码运行和打包运行。
    """

    argv_root_dir = Path(sys.argv[0]).expanduser().resolve(strict=False).parent
    if (argv_root_dir / "config").is_dir():
        return argv_root_dir

    return Path(__file__).resolve().parents[2]


# 当前项目根目录
PROJECT_ROOT_DIR = _resolve_project_root_dir()

# 默认引擎配置文件位置
DEFAULT_ENGINE_CONFIG_FILE = PROJECT_ROOT_DIR / "config" / "engine.toml"

__all__ = ["PROJECT_ROOT_DIR", "DEFAULT_ENGINE_CONFIG_FILE"]
