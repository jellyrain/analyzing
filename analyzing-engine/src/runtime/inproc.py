from pathlib import Path

from analyzing.plugin.errors import PluginLoadError
from analyzing.runtime.config import InprocRuntimeConfig
from analyzing.runtime.inproc import build_inproc_plugin

from src.registry.schemas import PluginCatalogEntry


def load_inproc_plugin(entry: PluginCatalogEntry) -> object:
    """
    根据登记项加载 inproc 插件实例
    """

    if entry.manifest is None:
        raise PluginLoadError("插件 manifest 不存在，无法加载 inproc 插件")

    runtime_config = entry.manifest.runtime
    if runtime_config is None:
        raise PluginLoadError("插件未声明 runtime 配置，无法加载 inproc 插件")

    if not isinstance(runtime_config, InprocRuntimeConfig):
        raise PluginLoadError("插件 runtime 配置不是 inproc，无法按 inproc 方式加载")

    resolved_search_paths = [
        str((Path(entry.plugin_dir_path) / raw_path).resolve())
        if not Path(raw_path).is_absolute()
        else str(Path(raw_path).resolve())
        for raw_path in runtime_config.search_paths
    ]

    resolved_runtime_config = runtime_config.model_copy(
        update={
            "search_paths": resolved_search_paths,
        }
    )

    return build_inproc_plugin(
        config=resolved_runtime_config,
        extra_search_paths=[str(entry.plugin_dir_path)],
    )


__all__ = ["load_inproc_plugin"]
