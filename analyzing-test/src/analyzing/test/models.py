from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from analyzing.plugin.base import AbstractPlugin
from analyzing.plugin.manifest import PluginManifest
from analyzing.plugin.result import PluginExecutionOutput


@dataclass(slots=True)
class LoadedPlugin:
    """
    已加载插件
    """

    # 当前插件项目根目录
    project_dir: Path

    # 插件 manifest
    manifest: PluginManifest

    # 本地插件实例；当前只有 inproc 会持有实例
    instance: AbstractPlugin | None = None


@dataclass(slots=True)
class SampleTestResult:
    """
    插件样例测试结果
    """

    # 是否通过
    ok: bool

    # 错误列表
    errors: list[str]

    # 插件输出
    output: PluginExecutionOutput | None = None


__all__ = ["LoadedPlugin", "SampleTestResult"]
