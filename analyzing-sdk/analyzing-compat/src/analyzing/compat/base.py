from __future__ import annotations

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from analyzing.compat.host import HostProfile
from analyzing.plugin.enums.plugin import PluginRole
from analyzing.plugin.errors import CompatibilityError, ManifestValidationError
from analyzing.plugin.manifest import PluginManifest


def ensure_manifest_compatible(
    manifest: PluginManifest,
    host_profile: HostProfile,
) -> None:
    """
    校验插件 manifest 与宿主是否兼容。

    这里只放全局通用规则，不放领域规则。
    """

    ensure_manifest_role_valid(manifest)
    ensure_manifest_sdk_compatible(manifest, host_profile)
    ensure_manifest_python_compatible(manifest, host_profile)
    ensure_manifest_runtime_supported(manifest, host_profile)


def ensure_manifest_role_valid(manifest: PluginManifest) -> None:
    """
    校验插件角色字段是否合法。
    """

    if manifest.plugin_role == PluginRole.BIZ:
        if manifest.plugin_type is None:
            raise ManifestValidationError("业务插件必须声明 plugin_type")

        if manifest.infra_slot is not None:
            raise ManifestValidationError("业务插件不能声明 infra_slot")

    if manifest.plugin_role == PluginRole.INFRA:
        if manifest.plugin_type is not None:
            raise ManifestValidationError("基础插件不能声明 plugin_type")

        if manifest.infra_slot is None:
            raise ManifestValidationError("基础插件必须声明 infra_slot")


def ensure_manifest_sdk_compatible(
    manifest: PluginManifest,
    host_profile: HostProfile,
) -> None:
    """
    校验 SDK 版本兼容性
    """

    try:
        spec = SpecifierSet(manifest.sdk_version)
    except InvalidSpecifier as exc:
        raise ManifestValidationError(
            f"插件 sdk_version 不是合法版本约束: {manifest.sdk_version}"
        ) from exc

    try:
        host_sdk_version = Version(host_profile.sdk_version)
    except InvalidVersion as exc:
        raise CompatibilityError(
            f"宿主 sdk_version 不是可比较版本号: {host_profile.sdk_version}"
        ) from exc

    if host_sdk_version not in spec:
        raise ManifestValidationError(
            f"插件 SDK 版本不兼容: host={host_profile.sdk_version}, required={manifest.sdk_version}"
        )


def ensure_manifest_python_compatible(
    manifest: PluginManifest,
    host_profile: HostProfile,
) -> None:
    """
    校验 Python 版本兼容性
    """

    if not manifest.python_version:
        return

    try:
        spec = SpecifierSet(manifest.python_version)
    except InvalidSpecifier as exc:
        raise ManifestValidationError(
            f"插件 python_version 不是合法版本约束: {manifest.python_version}"
        ) from exc

    try:
        host_python_version = Version(host_profile.python_version)
    except InvalidVersion as exc:
        raise CompatibilityError(
            f"宿主 python_version 不是可比较版本号: {host_profile.python_version}"
        ) from exc

    if host_python_version not in spec:
        raise ManifestValidationError(
            f"插件 Python 版本不兼容: host={host_profile.python_version}, required={manifest.python_version}"
        )


def ensure_manifest_runtime_supported(
    manifest: PluginManifest,
    host_profile: HostProfile,
) -> None:
    """
    校验运行模式是否被宿主支持。
    """

    if manifest.runtime_mode not in host_profile.supported_runtime_modes:
        raise CompatibilityError(f"宿主不支持该运行模式: {manifest.runtime_mode}")


__all__ = [
    "ensure_manifest_compatible",
    "ensure_manifest_role_valid",
    "ensure_manifest_sdk_compatible",
    "ensure_manifest_python_compatible",
    "ensure_manifest_runtime_supported",
]