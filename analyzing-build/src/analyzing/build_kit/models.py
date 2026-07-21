from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from analyzing.plugin.manifest import PluginManifest

PLUGIN_MANIFEST_FILE_NAME = "plugin.toml"
BUILD_CONFIG_FILE_NAME = "build.toml"
RAIN_METADATA_FILE_NAME = "__rain__/package.json"

DEFAULT_EXCLUDED_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".tox",
    "dist",
    "builds",
    "__rain__",
}


class BuildError(Exception):
    """
    插件构建失败。
    """


@dataclass(slots=True)
class BuildConfig:
    """
    build.toml 对应的最小构建配置。
    """

    variant: str | None = None
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BuildProject:
    """
    单插件源码项目的构建上下文。
    """

    project_dir: Path
    manifest_file_path: Path
    manifest: PluginManifest
    # 打包时写入 .rain 的最终 plugin.toml 文本。
    # 它可能和源码目录中的原始 plugin.toml 不同，因为这里会注入 SDK 物化结果。
    packaged_manifest_text: str
    build_config_file_path: Path | None = None
    build_config: BuildConfig = field(default_factory=BuildConfig)


@dataclass(slots=True)
class PackageEntry:
    """
    单个待写入 .rain 的文件项。
    """

    source_path: Path
    archive_path: str


@dataclass(slots=True)
class BuildResult:
    """
    插件构建结果。
    """

    rain_file_path: Path
    included_files: list[str]
    metadata: dict[str, Any]
