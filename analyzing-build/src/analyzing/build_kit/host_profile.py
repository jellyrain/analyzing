from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from analyzing.compat.host import HostFeatures, HostProfile, SDKDistribution
from analyzing.runtime.mode import RuntimeMode

from .project import (
    collect_project_baseline_dependencies,
    load_project_version,
)

HOST_PROFILE_FILE_NAME = "host_profile.json"


def _resolve_sdk_version(
    *,
    sdk_version: str | None,
    sdk_package_name: str,
) -> str:
    """
    解析宿主绑定的 SDK 具体版本
    """

    if sdk_version is not None and sdk_version.strip():
        return sdk_version.strip()

    try:
        return version(sdk_package_name)
    except PackageNotFoundError as exc:
        raise ValueError(
            f"未找到已安装的 SDK 包，无法生成宿主快照: {sdk_package_name}"
        ) from exc


def build_host_profile(
    *,
    pyproject_file_path: str | Path,
    python_version: str,
    supported_runtime_modes: list[RuntimeMode],
    features: HostFeatures | None = None,
    plugin_package_suffix: str = ".rain",
    sdk_distribution: SDKDistribution | None = None,
    sdk_package_name: str = "analyzing-plugin",
    sdk_version: str | None = None,
) -> HostProfile:
    """
    基于 engine 项目的 pyproject.toml 构建宿主画像
    """

    host_version = load_project_version(pyproject_file_path)
    baseline_dependencies = collect_project_baseline_dependencies(pyproject_file_path)

    return HostProfile(
        host_version=host_version,
        sdk_version=_resolve_sdk_version(
            sdk_version=sdk_version,
            sdk_package_name=sdk_package_name,
        ),
        python_version=python_version,
        supported_runtime_modes=supported_runtime_modes,
        plugin_package_suffix=plugin_package_suffix,
        features=features or HostFeatures(),
        baseline_dependencies=baseline_dependencies,
        sdk_distribution=sdk_distribution or SDKDistribution(),
    )


def dump_host_profile_data(
    host_profile: HostProfile,
) -> dict[str, Any]:
    """
    将 HostProfile 转成可落盘的纯字典
    """

    return host_profile.model_dump(mode="json")


def load_host_profile_file(
    file_path: str | Path,
) -> HostProfile:
    """
    从宿主快照 JSON 文件读取 HostProfile
    """

    resolved_file_path = Path(file_path).expanduser().resolve(strict=False)
    if not resolved_file_path.is_file():
        raise FileNotFoundError(f"未找到宿主快照文件: {resolved_file_path}")

    raw_data = json.loads(resolved_file_path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        raise ValueError(f"宿主快照文件顶层必须是对象: {resolved_file_path}")

    return HostProfile.model_validate(raw_data)


__all__ = [
    "HOST_PROFILE_FILE_NAME",
    "build_host_profile",
    "dump_host_profile_data",
    "load_host_profile_file",
]
