from __future__ import annotations

import inspect
import tomllib
from pathlib import Path

from analyzing.plugin.base import AbstractPlugin
from analyzing.plugin.errors import PluginLoadError
from analyzing.plugin.manifest import PluginManifest
from analyzing.runtime.config import InprocRuntimeConfig, SubprocessRuntimeConfig, RemoteRuntimeConfig
from analyzing.runtime.inproc import build_inproc_plugin
from analyzing.runtime.mode import RuntimeMode

from analyzing.test.models import LoadedPlugin


def _resolve_project_dir(project_dir: str | Path | None = None) -> Path:
    """
    解析插件项目根目录

    - project_dir 为 None 时，默认使用当前工作目录
    - 当前工作目录约定为插件项目根目录
    """

    if project_dir is None:
        return Path.cwd().resolve()

    return Path(project_dir).resolve()


def load_plugin_manifest_from_project(
    project_dir: str | Path | None = None,
) -> PluginManifest:
    """
    从插件项目根目录读取 manifest
    """

    normalized_project_dir = _resolve_project_dir(project_dir)
    manifest_file_path = normalized_project_dir / "plugin.toml"

    if not manifest_file_path.is_file():
        raise PluginLoadError(
            f"未找到 plugin.toml，请确认当前目录是插件项目根目录: {normalized_project_dir}"
        )

    with manifest_file_path.open("rb") as fp:
        raw_data = tomllib.load(fp)

    return PluginManifest.model_validate(raw_data)


def _build_inproc_loaded_plugin(
    project_dir: Path,
    manifest: PluginManifest,
    runtime: InprocRuntimeConfig,
) -> LoadedPlugin:
    """
    构造 inproc 插件实例
    """

    # 把 search_paths 映射为基于插件项目根目录的绝对路径，避免依赖当前 shell 目录。
    extra_search_paths = [
        str((project_dir / search_path).resolve())
        for search_path in runtime.search_paths
    ]

    instance = build_inproc_plugin(
        config=runtime,
        extra_search_paths=extra_search_paths,
    )

    if not isinstance(instance, AbstractPlugin):
        raise PluginLoadError("inproc 插件实例必须实现 AbstractPlugin")

    return LoadedPlugin(
        project_dir=project_dir,
        manifest=manifest,
        instance=instance,
    )


def _build_subprocess_loaded_plugin(
    project_dir: Path,
    manifest: PluginManifest,
    runtime: SubprocessRuntimeConfig,
) -> LoadedPlugin:
    """
    构造 subprocess 插件加载结果

    这里不提前拉起子进程：
    - 开发期测试通常只需要在 invoke 时临时拉起
    - 可以避免额外的生命周期管理复杂度
    """

    return LoadedPlugin(
        project_dir=project_dir,
        manifest=manifest,
        instance=None,
    )


def load_plugin(project_dir: str | Path | None = None) -> LoadedPlugin:
    """
    从当前插件项目加载插件实例

    当前版本实现：
    - inproc: 直接构造本地插件实例
    - subprocess: 先只加载 manifest，实际调用时临时拉起子进程
    - remote: 暂未实现
    """

    normalized_project_dir = _resolve_project_dir(project_dir)
    manifest = load_plugin_manifest_from_project(normalized_project_dir)
    runtime = manifest.runtime

    if runtime is None:
        raise PluginLoadError("plugin.toml 缺少 runtime 配置")

    if manifest.runtime_mode == RuntimeMode.INPROC:
        if not isinstance(runtime, InprocRuntimeConfig):
            raise PluginLoadError("manifest.runtime_mode 与 runtime 配置类型不一致")

        return _build_inproc_loaded_plugin(
            project_dir=normalized_project_dir,
            manifest=manifest,
            runtime=runtime,
        )

    if manifest.runtime_mode == RuntimeMode.SUBPROCESS:
        if not isinstance(runtime, SubprocessRuntimeConfig):
            raise PluginLoadError("manifest.runtime_mode 与 runtime 配置类型不一致")

        return _build_subprocess_loaded_plugin(
            project_dir=normalized_project_dir,
            manifest=manifest,
            runtime=runtime,
        )

    if manifest.runtime_mode == RuntimeMode.REMOTE:
        if not isinstance(runtime, RemoteRuntimeConfig):
            raise PluginLoadError("manifest.runtime_mode 与 runtime 配置类型不一致")

        raise PluginLoadError("当前版本尚未实现 remote 插件加载")

    raise PluginLoadError(f"不支持的 runtime_mode: {manifest.runtime_mode}")


def ensure_manifest_matches_instance(loaded: LoadedPlugin) -> None:
    """
    校验实例自身 manifest 与项目根目录中的 plugin.toml 是否一致
    """

    if loaded.instance is None:
        return

    instance_manifest = loaded.instance.manifest

    if instance_manifest.plugin_id != loaded.manifest.plugin_id:
        raise PluginLoadError(
            "插件实例 manifest.plugin_id 与项目根目录 plugin.toml 不一致"
        )

    if instance_manifest.runtime_mode != loaded.manifest.runtime_mode:
        raise PluginLoadError(
            "插件实例 manifest.runtime_mode 与项目根目录 plugin.toml 不一致"
        )


def get_plugin_module_file(loaded: LoadedPlugin) -> Path:
    """
    返回插件实例类定义所在文件
    """

    if loaded.instance is None:
        raise PluginLoadError("当前插件没有本地实例，无法定位模块文件")

    return Path(inspect.getfile(loaded.instance.__class__)).resolve()


__all__ = [
    "load_plugin_manifest_from_project",
    "load_plugin",
    "ensure_manifest_matches_instance",
    "get_plugin_module_file",
]
