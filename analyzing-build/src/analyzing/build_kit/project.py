from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement


def load_pyproject_file(
    pyproject_file_path: str | Path,
) -> dict[str, Any]:
    """
    读取 pyproject.toml，并确保顶层结构合法
    """

    resolved_file_path = Path(pyproject_file_path).expanduser().resolve(strict=False)
    if not resolved_file_path.is_file():
        raise FileNotFoundError(f"未找到 pyproject.toml: {resolved_file_path}")

    with resolved_file_path.open("rb") as fp:
        raw_data = tomllib.load(fp)

    if not isinstance(raw_data, dict):
        raise ValueError(f"pyproject.toml 顶层必须是表对象: {resolved_file_path}")

    return raw_data


def load_project_section(
    pyproject_file_path: str | Path,
) -> dict[str, Any]:
    """
    读取 pyproject.toml 中的 [project] 段
    """

    pyproject_data = load_pyproject_file(pyproject_file_path)
    project_section = pyproject_data.get("project")

    if not isinstance(project_section, dict):
        raise ValueError(f"pyproject.toml 缺少 [project]: {Path(pyproject_file_path)}")

    return project_section


def load_project_version(
    pyproject_file_path: str | Path,
) -> str:
    """
    读取 pyproject.toml 中的 project.version
    """

    project_section = load_project_section(pyproject_file_path)
    raw_version = project_section.get("version")

    if not isinstance(raw_version, str) or not raw_version.strip():
        raise ValueError(
            f"pyproject.toml 的 project.version 必须是非空字符串: "
            f"{Path(pyproject_file_path)}"
        )

    return raw_version.strip()


def _normalize_dependency_requirement(
    raw_dependency: str,
) -> tuple[str, str]:
    """
    将 PEP 508 依赖字符串规范化
    """

    requirement = Requirement(raw_dependency)
    package_name = requirement.name.lower()
    version_specifier = str(requirement.specifier).strip()

    if not version_specifier:
        version_specifier = "*"

    return package_name, version_specifier


def collect_project_baseline_dependencies(
    pyproject_file_path: str | Path,
) -> dict[str, str]:
    """
    从 pyproject.toml 的 [project.dependencies] 收集直接依赖契约
    """

    project_section = load_project_section(pyproject_file_path)
    raw_dependencies = project_section.get("dependencies", [])

    if raw_dependencies is None:
        raw_dependencies = []

    if not isinstance(raw_dependencies, list):
        raise ValueError(
            f"pyproject.toml 的 project.dependencies 必须是数组: "
            f"{Path(pyproject_file_path)}"
        )

    baseline_dependencies: dict[str, str] = {}

    for raw_dependency in raw_dependencies:
        if not isinstance(raw_dependency, str) or not raw_dependency.strip():
            raise ValueError(
                f"pyproject.toml 中存在非法依赖声明: {Path(pyproject_file_path)}"
            )

        package_name, version_specifier = _normalize_dependency_requirement(
            raw_dependency.strip()
        )

        if package_name in baseline_dependencies:
            raise ValueError(
                f"pyproject.toml 中存在重复依赖声明: "
                f"{Path(pyproject_file_path)}, package={package_name}"
            )

        baseline_dependencies[package_name] = version_specifier

    return baseline_dependencies


__all__ = [
    "collect_project_baseline_dependencies",
    "load_project_section",
    "load_project_version",
    "load_pyproject_file",
]
