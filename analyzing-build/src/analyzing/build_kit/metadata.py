from __future__ import annotations

from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Any
from zoneinfo import ZoneInfo

from analyzing.runtime.mode import RuntimeMode

from .models import BuildProject


def _safe_builder_version() -> str:
    for package_name in (
        "build_kit",
        "build-kit",
        "analyzing-build-kit",
        "analyzing-build",
    ):
        try:
            return version(package_name)
        except PackageNotFoundError:
            continue

    return "0.1.0"


def _resolve_build_variant(project: BuildProject) -> str | None:
    if project.build_config.variant:
        return project.build_config.variant

    if project.manifest.runtime_mode == RuntimeMode.INPROC:
        return "plain"

    return None


def build_rain_metadata(project: BuildProject) -> dict[str, Any]:
    """
    生成 __rain__/package.json 对应的元数据。
    """

    return {
        "package_format_version": 1,
        "package_type": "plugin",
        "plugin": {
            "id": project.manifest.plugin_id,
            "version": project.manifest.version,
        },
        "build_kit": {
            "builder": "build_kit",
            "builder_version": _safe_builder_version(),
            "built_at": datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S"),
            "runtime_mode": getattr(
                project.manifest.runtime_mode,
                "value",
                str(project.manifest.runtime_mode),
            ),
            "variant": _resolve_build_variant(project),
        },
        "install": {
            "role": getattr(
                project.manifest.plugin_role,
                "value",
                str(project.manifest.plugin_role),
            ),
            "plugin_dir_name": project.manifest.plugin_id,
        },
    }
