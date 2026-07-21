from pathlib import Path

from analyzing.compat.host import HostProfile
from analyzing.plugin.enums.plugin import PluginRole, InstallStatus, RuntimeStatus
from analyzing.plugin.errors import ManifestValidationError, CompatibilityError

from src.app.enums import PluginLoadStrategy
from src.app.schemas import EngineConfig
from src.registry.manifest import load_manifest_from_dir, validate_manifest
from src.registry.schemas import PluginCatalog, PluginCatalogEntry


def _enum_value(raw: object) -> object:
    """
    兼容枚举对象或已经被序列化成字符串的枚举值。
    """

    return getattr(raw, "value", raw)


def _resolve_load_strategy(
    plugin_id: str,
    config: EngineConfig,
) -> PluginLoadStrategy:
    """
    根据引擎配置解析插件加载策略
    """

    if plugin_id in set(config.plugins.startup.plugin_ids):
        return PluginLoadStrategy.STARTUP

    return config.plugins.load.default


def _iter_plugin_dirs(role_dir_path: Path) -> list[Path]:
    """
    返回角色目录下的一级插件目录
    """

    return sorted(path for path in role_dir_path.iterdir() if path.is_dir())


def _build_catalog_entry(
    plugin_dir_path: Path,
    expected_role: PluginRole,
    config: EngineConfig,
    host_profile: HostProfile,
) -> PluginCatalogEntry:
    """
    构建单个插件目录对应的登记项
    """

    try:
        manifest_file_path, manifest = load_manifest_from_dir(plugin_dir_path)

        if manifest.plugin_role != expected_role:
            raise ManifestValidationError(
                f"插件目录角色与 manifest 声明不一致: "
                f"dir={_enum_value(expected_role)}, manifest={_enum_value(manifest.plugin_role)}"
            )

        validate_manifest(manifest, host_profile)

        return PluginCatalogEntry(
            plugin_dir_path=plugin_dir_path,
            manifest_file_path=manifest_file_path,
            manifest=manifest,
            load_strategy=_resolve_load_strategy(manifest.plugin_id, config),
            is_compatible=True,
            install_status=InstallStatus.DISCOVERED,
            runtime_status=RuntimeStatus.UNAVAILABLE,
        )

    except (
        FileNotFoundError,
        ManifestValidationError,
        CompatibilityError,
        ValueError,
    ) as exc:
        return PluginCatalogEntry(
            plugin_dir_path=plugin_dir_path,
            manifest_file_path=None,
            manifest=None,
            load_strategy=PluginLoadStrategy.LAZY,
            is_compatible=False,
            install_status=InstallStatus.FAILED,
            runtime_status=RuntimeStatus.ERROR,
            error_message=str(exc),
        )


def build_plugin_catalog(
    config: EngineConfig,
    host_profile: HostProfile,
) -> PluginCatalog:
    """
    扫描插件目录并构建引擎注册表
    """

    catalog = PluginCatalog()
    runtime_plugins_dir_path = config.paths.runtime_plugins_dir_path

    if runtime_plugins_dir_path is None:
        return catalog

    for role_dir_name, expected_role in (
        ("biz", PluginRole.BIZ),
        ("infra", PluginRole.INFRA),
    ):
        role_dir_path = runtime_plugins_dir_path / role_dir_name
        if not role_dir_path.is_dir():
            continue

        for plugin_dir_path in _iter_plugin_dirs(role_dir_path):
            entry = _build_catalog_entry(
                plugin_dir_path=plugin_dir_path,
                expected_role=expected_role,
                config=config,
                host_profile=host_profile,
            )
            catalog.add_entry(entry)

    return catalog


def ensure_no_infra_slot_conflicts(catalog: PluginCatalog) -> None:
    """
    确保基础插件不存在 slot 冲突
    """

    conflicts = catalog.get_infra_slot_conflicts()
    if not conflicts:
        return

    messages: list[str] = []

    for slot, entries in conflicts.items():
        plugin_ids = [
            entry.manifest.plugin_id for entry in entries if entry.manifest is not None
        ]
        messages.append(f"{slot}: {', '.join(plugin_ids)}")

    raise RuntimeError("检测到基础插件 slot 冲突，引擎无法启动: " + "; ".join(messages))


__all__ = ["build_plugin_catalog", "ensure_no_infra_slot_conflicts"]
