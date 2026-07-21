from abc import abstractmethod, ABC
from typing import Any

from analyzing.plugin.base import (
    AbstractPlugin,
    ManifestBackedPluginMixin,
)
from analyzing.plugin.result import (
    PluginExecutionOutput,
    SplitterPluginResultPayload,
)


class SplitterPluginExecutionOutput(PluginExecutionOutput):
    """
    拆分器插件标准执行输出
    """

    # 兼容 pipeline 的统一输出
    pipeline_result: SplitterPluginResultPayload


class SplitterPlugin(AbstractPlugin):
    """
    拆分器插件抽象接口
    """

    @abstractmethod
    def split(self, text: str, params: dict[str, Any]) -> SplitterPluginExecutionOutput:
        """
        执行拆分逻辑并返回片段结果
        """

        ...


class BaseManifestSplitterPlugin(ManifestBackedPluginMixin, SplitterPlugin, ABC):
    """
    带默认 manifest 实现的拆分器基类
    """

    ...


__all__ = [
    "SplitterPluginExecutionOutput",
    "SplitterPlugin",
    "BaseManifestSplitterPlugin",
]
