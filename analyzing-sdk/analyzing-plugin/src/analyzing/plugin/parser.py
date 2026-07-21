from abc import abstractmethod, ABC
from typing import Any

from analyzing.plugin.base import (
    AbstractPlugin,
    ManifestBackedPluginMixin,
)
from analyzing.plugin.result import PluginExecutionOutput, ParserPluginResultPayload


class ParserPluginExecutionOutput(PluginExecutionOutput):
    """
    解析器插件标准执行输出
    """

    # 兼容 pipeline 的统一输出
    pipeline_result: ParserPluginResultPayload


class ParserPlugin(AbstractPlugin):
    """
    解析器插件抽象接口
    """

    @abstractmethod
    def parse(self, text: str, params: dict[str, Any]) -> ParserPluginExecutionOutput:
        """
        执行解析逻辑并返回结构化结果
        """

        ...


class BaseManifestParserPlugin(ManifestBackedPluginMixin, ParserPlugin, ABC):
    """
    带默认 manifest 实现的解析器基类
    """

    ...


__all__ = ["ParserPluginExecutionOutput", "ParserPlugin", "BaseManifestParserPlugin"]
