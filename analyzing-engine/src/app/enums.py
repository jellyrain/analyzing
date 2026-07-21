from enum import StrEnum


class PluginLoadStrategy(StrEnum):
    """
    插件加载策略
    """

    # 启动时立即加载
    STARTUP = "startup"

    # 首次使用时再加载
    LAZY = "lazy"


__all__ = ["PluginLoadStrategy"]
