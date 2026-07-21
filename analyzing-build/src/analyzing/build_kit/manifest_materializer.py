from __future__ import annotations

import json
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any

from analyzing.plugin.manifest import PluginManifest
from analyzing.plugin.ui import UISchema
from pydantic import ValidationError

from .models import BuildError
from .project import collect_project_baseline_dependencies

PLUGIN_MANIFEST_FILE_NAME = "plugin.toml"
PYPROJECT_FILE_NAME = "pyproject.toml"


def _load_toml_file(file_path: Path) -> dict[str, Any]:
    """
    读取 TOML 文件，并确保顶层结构是表对象
    """

    with file_path.open("rb") as fp:
        raw_data = tomllib.load(fp)

    if not isinstance(raw_data, dict):
        raise ValueError(f"TOML 顶层必须是表对象: {file_path}")

    return raw_data


def _load_json_file(file_path: Path) -> dict[str, Any]:
    """
    读取 JSON 文件，并确保顶层结构是对象
    """

    raw_data = json.loads(file_path.read_text(encoding="utf-8"))

    if not isinstance(raw_data, dict):
        raise ValueError(f"JSON 顶层必须是对象: {file_path}")

    return raw_data


def _resolve_form_schema_file_path(
    manifest_file_path: Path,
    form_schema_file: str | None,
) -> Path | None:
    """
    解析 form schema 文件路径
    """

    if not form_schema_file:
        return None

    relative_path = Path(form_schema_file)
    if relative_path.is_absolute():
        raise ValueError(f"form_schema_file 必须是相对路径: {manifest_file_path}")

    return (manifest_file_path.parent / relative_path).resolve(strict=False)


def _validate_form_schema(
    form_schema: dict[str, Any],
    form_schema_file_path: Path,
) -> dict[str, Any]:
    try:
        schema = UISchema.model_validate(form_schema)
    except ValidationError as exc:
        raise BuildError(
            f"form schema 校验失败: {form_schema_file_path}\n{exc}"
        ) from exc

    return schema.model_dump(mode="json")


def _resolve_pyproject_file_path(
    manifest_file_path: Path,
    pyproject_file_path: str | Path | None,
) -> Path:
    """
    解析插件项目 pyproject.toml 路径

    默认优先级：
    1. 显式传入的 pyproject_file_path
    2. manifest 同级目录
    3. 向上逐级查找最近的 pyproject.toml
    """

    if pyproject_file_path is not None:
        return Path(pyproject_file_path).expanduser().resolve(strict=False)

    direct_candidate = (manifest_file_path.parent / PYPROJECT_FILE_NAME).resolve(
        strict=False
    )
    if direct_candidate.is_file():
        return direct_candidate

    for parent_dir in manifest_file_path.parents[1:]:
        candidate = (parent_dir / PYPROJECT_FILE_NAME).resolve(strict=False)
        if candidate.is_file():
            return candidate

    return direct_candidate


def _inject_form_schema(
    raw_manifest_data: dict[str, Any],
    *,
    manifest_file_path: Path,
) -> dict[str, Any]:
    """
    根据 form_schema_file 读取 JSON，并注入到最终 manifest 数据里
    """

    raw_form_schema_file = raw_manifest_data.get("form_schema_file")
    if raw_form_schema_file is not None and not isinstance(raw_form_schema_file, str):
        raise ValueError(f"form_schema_file 必须是字符串: {manifest_file_path}")

    form_schema_file_path = _resolve_form_schema_file_path(
        manifest_file_path,
        raw_form_schema_file,
    )

    if form_schema_file_path is None:
        raw_manifest_data["form_schema"] = {}
        return raw_manifest_data

    if not form_schema_file_path.is_file():
        raise FileNotFoundError(f"未找到 form schema 文件: {form_schema_file_path}")

    form_schema = _load_json_file(form_schema_file_path)
    _validate_form_schema(
        form_schema,
        form_schema_file_path,
    )

    raw_manifest_data["form_schema"] = form_schema
    return raw_manifest_data


def _inject_generated_baseline_dependencies(
    raw_manifest_data: dict[str, Any],
    *,
    pyproject_file_path: Path,
) -> dict[str, Any]:
    """
    用 pyproject.toml 的直接依赖覆盖 manifest 里的 baseline_dependencies
    """

    baseline_dependencies = collect_project_baseline_dependencies(pyproject_file_path)

    raw_host_requirements = raw_manifest_data.setdefault("host_requirements", {})
    if not isinstance(raw_host_requirements, dict):
        raise ValueError(f"host_requirements 必须是表对象: {pyproject_file_path}")

    raw_host_requirements["baseline_dependencies"] = baseline_dependencies
    return raw_manifest_data


def materialize_plugin_manifest(
    manifest_file_path: str | Path,
    *,
    pyproject_file_path: str | Path | None = None,
) -> PluginManifest:
    """
    物化插件 manifest
    """

    resolved_manifest_file_path = (
        Path(manifest_file_path).expanduser().resolve(strict=False)
    )
    if not resolved_manifest_file_path.is_file():
        raise FileNotFoundError(
            f"未找到 plugin manifest: {resolved_manifest_file_path}"
        )

    raw_manifest_data = deepcopy(_load_toml_file(resolved_manifest_file_path))
    raw_manifest_data = _inject_form_schema(
        raw_manifest_data,
        manifest_file_path=resolved_manifest_file_path,
    )
    raw_manifest_data = _inject_generated_baseline_dependencies(
        raw_manifest_data,
        pyproject_file_path=_resolve_pyproject_file_path(
            resolved_manifest_file_path,
            pyproject_file_path,
        ),
    )

    return PluginManifest.model_validate(raw_manifest_data)


def dump_materialized_plugin_manifest_data(
    manifest_file_path: str | Path,
    *,
    pyproject_file_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    返回可写回 plugin.toml 的最终 manifest 数据
    """

    manifest = materialize_plugin_manifest(
        manifest_file_path,
        pyproject_file_path=pyproject_file_path,
    )

    return manifest.model_dump(
        mode="json",
        exclude={"form_schema"},
    )


__all__ = [
    "dump_materialized_plugin_manifest_data",
    "materialize_plugin_manifest",
]
