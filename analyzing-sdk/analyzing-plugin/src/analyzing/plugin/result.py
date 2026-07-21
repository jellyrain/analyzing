from __future__ import annotations

from typing import Any, Literal

from pydantic import Field
from analyzing.contracts.model import AnalyzingModel

from analyzing.plugin.base import PluginResultPayload


class SplitterPluginResultPayload(PluginResultPayload):
    """
    拆分器插件标准结果体
    """

    # 插件类型
    plugin_type: Literal["splitter"] = "splitter"

    # 兼容 pipeline 的统一输出
    pipeline_output: list[str] = Field(default_factory=list)


class ParserPluginResultPayload(PluginResultPayload):
    """
    解析器插件标准结果体
    """

    # 插件类型
    plugin_type: Literal["parser"] = "parser"

    # 兼容 pipeline 的统一输出
    pipeline_output: dict[str, list[Any]] = Field(default_factory=dict)


# 全部插件 pipeline ResultPayload
AllPluginResultPayload = SplitterPluginResultPayload | ParserPluginResultPayload | None


class PluginExecutionOutput(AnalyzingModel):
    """
    插件标准执行输出

    - raw_output: 插件自己的原始输出
    """

    # 插件自己的原始输出
    raw_output: list[dict[str, Any]] | dict[str, Any] = Field(default_factory=list)

    # 兼容 pipeline 的统一输出
    pipeline_result: AllPluginResultPayload = None


__all__ = [
    "SplitterPluginResultPayload",
    "ParserPluginResultPayload",
    "AllPluginResultPayload",
    "PluginExecutionOutput",
]
