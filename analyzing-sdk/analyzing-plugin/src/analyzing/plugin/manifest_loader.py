from __future__ import annotations

import json
import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any

from analyzing.plugin.manifest import PluginManifest

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
    解析 form schema 文件路径, 这里强制要求使用相对路径，避免把开发机上的绝对路径写进 manifest
    """

    if not form_schema_file:
        return None

    relative_path = Path(form_schema_file)
    if relative_path.is_absolute():
        raise ValueError(f"form_schema_file 必须是相对路径: {manifest_file_path}")

    return (manifest_file_path.parent / relative_path).resolve(strict=False)


def _validate_form_schema(
    form_schema: dict[str, Any],
    *,
    form_schema_file_path: Path,
) -> None:
    """
    先做一层最小结构校验
    """

    raw_fields = form_schema.get("fields")
    if raw_fields is None:
        return

    if not isinstance(raw_fields, dict):
        raise ValueError(f"form schema 的 fields 必须是对象: {form_schema_file_path}")

    for field_name, field_schema in raw_fields.items():
        if not isinstance(field_name, str) or not field_name.strip():
            raise ValueError(f"form schema 存在非法字段名: {form_schema_file_path}")

        if not isinstance(field_schema, dict):
            raise ValueError(
                f"form schema 字段定义必须是对象: "
                f"{form_schema_file_path}, field={field_name}"
            )


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
        form_schema_file_path=form_schema_file_path,
    )

    raw_manifest_data["form_schema"] = form_schema
    return raw_manifest_data


def load_plugin_manifest_file(
    manifest_file_path: str | Path,
) -> PluginManifest:
    """
    从 plugin.toml 加载最终插件 manifest
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

    return PluginManifest.model_validate(raw_manifest_data)


__all__ = ["load_plugin_manifest_file"]
