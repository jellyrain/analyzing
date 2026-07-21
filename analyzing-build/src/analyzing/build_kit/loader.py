from __future__ import annotations

import tomllib
from pathlib import Path

import tomli_w
from analyzing.plugin.manifest import PluginManifest

from .manifest_materializer import (
    materialize_plugin_manifest,
    dump_materialized_plugin_manifest_data,
)
from .models import (
    BUILD_CONFIG_FILE_NAME,
    PLUGIN_MANIFEST_FILE_NAME,
    BuildConfig,
    BuildError,
    BuildProject,
)


def _load_manifest(manifest_file_path: Path) -> PluginManifest:
    return materialize_plugin_manifest(manifest_file_path)


def _drop_none_values(value):
    """
    将 TOML 不支持的 None 递归剔除。
    """

    if isinstance(value, dict):
        return {
            key: _drop_none_values(item)
            for key, item in value.items()
            if item is not None
        }

    if isinstance(value, list):
        return [_drop_none_values(item) for item in value if item is not None]

    return value


def _render_packaged_manifest_text(manifest_file_path: Path) -> str:
    """
    渲染最终写入 .rain 的 plugin.toml 文本。
    """

    manifest_data = _drop_none_values(
        dump_materialized_plugin_manifest_data(manifest_file_path)
    )
    return tomli_w.dumps(manifest_data).rstrip() + "\n"


def _load_build_config(build_config_file_path: Path) -> BuildConfig:
    with build_config_file_path.open("rb") as fp:
        raw_data = tomllib.load(fp)

    variant = raw_data.get("variant")
    include = raw_data.get("include", [])
    exclude = raw_data.get("exclude", [])

    if variant is not None and not isinstance(variant, str):
        raise BuildError("build.toml 的 variant 必须是字符串")

    if not isinstance(include, list) or not all(
        isinstance(item, str) for item in include
    ):
        raise BuildError("build.toml 的 include 必须是字符串列表")

    if not isinstance(exclude, list) or not all(
        isinstance(item, str) for item in exclude
    ):
        raise BuildError("build.toml 的 exclude 必须是字符串列表")

    return BuildConfig(variant=variant, include=include, exclude=exclude)


def load_build_project(project_dir: str | Path) -> BuildProject:
    """
    从单插件源码目录加载构建上下文。
    """

    resolved_project_dir = Path(project_dir).expanduser().resolve(strict=False)
    if not resolved_project_dir.is_dir():
        raise BuildError(f"插件项目目录不存在: {resolved_project_dir}")

    manifest_file_path = resolved_project_dir / PLUGIN_MANIFEST_FILE_NAME
    if not manifest_file_path.is_file():
        raise BuildError(
            f"插件项目目录中未找到 {PLUGIN_MANIFEST_FILE_NAME}: {resolved_project_dir}"
        )

    manifest = _load_manifest(manifest_file_path)
    packaged_manifest_text = _render_packaged_manifest_text(manifest_file_path)

    build_config_file_path = resolved_project_dir / BUILD_CONFIG_FILE_NAME
    if build_config_file_path.is_file():
        build_config = _load_build_config(build_config_file_path)
        return BuildProject(
            project_dir=resolved_project_dir,
            manifest_file_path=manifest_file_path,
            manifest=manifest,
            packaged_manifest_text=packaged_manifest_text,
            build_config_file_path=build_config_file_path,
            build_config=build_config,
        )

    return BuildProject(
        project_dir=resolved_project_dir,
        manifest_file_path=manifest_file_path,
        manifest=manifest,
        packaged_manifest_text=packaged_manifest_text,
    )
