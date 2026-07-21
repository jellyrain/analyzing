from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar

from analyzing.contracts.model import AnalyzingModel

from analyzing.plugin.manifest import PluginManifest
from analyzing.plugin.manifest_loader import load_plugin_manifest_file


class AbstractPlugin(ABC):
    """
    所有插件接口的基础抽象
    """

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """
        返回插件自己的 manifest
        """

        ...

    @abstractmethod
    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        校验并返回规范化后的参数
        """

        ...


class PluginResultPayload(AnalyzingModel):
    """
    插件标准结果体基类
    """

    # 插件类型
    plugin_type: str


class ManifestBackedPluginMixin:
    """
    为插件提供默认 manifest 实现
    """

    manifest_levels_up: ClassVar[int] = 2
    manifest_file_name: ClassVar[str] = "plugin.toml"
    _manifest_cache: ClassVar[PluginManifest | None] = None

    @classmethod
    def _resolve_manifest_file_path(cls) -> Path:
        """
        基于插件类所在模块路径，反推出 plugin.toml 的路径。
        """

        module_file_path = Path(inspect.getfile(cls)).resolve(strict=False)
        plugin_dir_path = module_file_path.parents[cls.manifest_levels_up]
        return plugin_dir_path / cls.manifest_file_name

    @property
    def manifest(self) -> PluginManifest:
        cls = self.__class__

        if cls._manifest_cache is None:
            cls._manifest_cache = load_plugin_manifest_file(
                cls._resolve_manifest_file_path()
            )

        return cls._manifest_cache


__all__ = ["AbstractPlugin", "PluginResultPayload", "ManifestBackedPluginMixin"]
