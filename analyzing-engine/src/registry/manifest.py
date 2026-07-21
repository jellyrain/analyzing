from pathlib import Path

from analyzing.compat.base import ensure_manifest_compatible
from analyzing.compat.host import HostProfile
from analyzing.plugin.manifest import PluginManifest
from analyzing.plugin.manifest_loader import load_plugin_manifest_file

from src.registry.constants import PLUGIN_MANIFEST_FILE_NAME


def find_manifest_file(plugin_dir_path: Path) -> Path:
    """
    在插件目录中查找 plugin.toml
    """

    manifest_file_path = plugin_dir_path / PLUGIN_MANIFEST_FILE_NAME

    if not manifest_file_path.is_file():
        raise FileNotFoundError(
            f"插件目录中未找到 {PLUGIN_MANIFEST_FILE_NAME}: {plugin_dir_path}"
        )

    return manifest_file_path


def load_manifest(manifest_file_path: Path) -> PluginManifest:
    """
    从 plugin.toml 加载插件 manifest
    """

    return load_plugin_manifest_file(manifest_file_path)


def load_manifest_from_dir(plugin_dir_path: Path) -> tuple[Path, PluginManifest]:
    """
    从插件目录中查找并加载 plugin.toml
    """

    manifest_file_path = find_manifest_file(plugin_dir_path)
    manifest = load_manifest(manifest_file_path)

    return manifest_file_path, manifest


def validate_manifest(
    manifest: PluginManifest,
    host_profile: HostProfile,
) -> None:
    """
    校验插件 manifest 与引擎是否兼容
    """

    ensure_manifest_compatible(manifest, host_profile)


__all__ = [
    "find_manifest_file",
    "load_manifest",
    "load_manifest_from_dir",
    "validate_manifest",
]
