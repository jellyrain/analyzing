from __future__ import annotations

import os
import shutil
import tomllib
from collections import deque
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Iterable

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from .models import BuildError


@dataclass(slots=True)
class RuntimeDependencyResult:
    """
    运行时依赖物化结果。
    """

    source_site_packages_dir: Path
    target_site_packages_dir: Path
    root_dependency_names: list[str]
    resolved_distribution_names: list[str]
    copied_files: list[str]


def _read_project_dependency_names(
    pyproject_file_path: Path,
    include_dev_dependencies: bool = False,
) -> list[str]:
    """
    从 pyproject.toml 读取依赖名。

    这里只返回“根依赖名”，例如：
    - analyzing-plugin
    - numpy
    - onnxruntime
    - transformers
    """

    if not pyproject_file_path.is_file():
        raise BuildError(f"未找到 pyproject.toml: {pyproject_file_path}")

    with pyproject_file_path.open("rb") as fp:
        raw_data = tomllib.load(fp)

    project = raw_data.get("project")
    if not isinstance(project, dict):
        raise BuildError("pyproject.toml 缺少 [project] 配置")

    raw_dependencies = project.get("dependencies", [])
    if not isinstance(raw_dependencies, list):
        raise BuildError("[project].dependencies 必须是列表")

    raw_items: list[str] = []
    raw_items.extend(item for item in raw_dependencies if isinstance(item, str))

    if include_dev_dependencies:
        dependency_groups = raw_data.get("dependency-groups", {})
        if isinstance(dependency_groups, dict):
            for group_items in dependency_groups.values():
                if isinstance(group_items, list):
                    raw_items.extend(
                        item for item in group_items if isinstance(item, str)
                    )

    names: list[str] = []
    seen: set[str] = set()

    for raw_item in raw_items:
        try:
            requirement = Requirement(raw_item)
        except Exception as exc:
            raise BuildError(f"无法解析依赖声明: {raw_item}") from exc

        normalized_name = canonicalize_name(requirement.name)
        if normalized_name in seen:
            continue

        seen.add(normalized_name)
        names.append(normalized_name)

    return names


def _build_distribution_index(
    source_site_packages_dir: Path,
) -> dict[str, metadata.Distribution]:
    """
    从指定 site-packages 构建 distribution 索引。
    """

    if not source_site_packages_dir.is_dir():
        raise BuildError(f"source_site_packages_dir 不存在: {source_site_packages_dir}")

    distributions = metadata.distributions(path=[str(source_site_packages_dir)])
    index: dict[str, metadata.Distribution] = {}

    for dist in distributions:
        dist_name = dist.metadata.get("Name")
        if not dist_name:
            continue
        index[canonicalize_name(dist_name)] = dist

    return index


def _should_include_requirement(requirement: Requirement) -> bool:
    """
    判断一个依赖声明在当前环境下是否生效。
    """

    if requirement.marker is None:
        return True

    try:
        return requirement.marker.evaluate(default_environment())
    except Exception:
        # marker 解析异常时，宁可保守地带上
        return True


def _resolve_distribution_closure(
    root_dependency_names: list[str],
    distribution_index: dict[str, metadata.Distribution],
) -> list[metadata.Distribution]:
    """
    从根依赖递归求出完整运行时依赖闭包。
    """

    resolved: list[metadata.Distribution] = []
    visited: set[str] = set()
    queue = deque(root_dependency_names)

    while queue:
        dependency_name = queue.popleft()
        normalized_name = canonicalize_name(dependency_name)

        if normalized_name in visited:
            continue
        visited.add(normalized_name)

        dist = distribution_index.get(normalized_name)
        if dist is None:
            raise BuildError(
                f"source_site_packages_dir 中未找到依赖: {dependency_name}"
            )

        resolved.append(dist)

        for raw_requirement in dist.requires or []:
            try:
                requirement = Requirement(raw_requirement)
            except Exception:
                # 单条依赖元数据坏了时，跳过这一条，避免整个流程被卡死
                continue

            if not _should_include_requirement(requirement):
                continue

            queue.append(requirement.name)

    return resolved


def _copy_distribution_files(
    dist: metadata.Distribution,
    source_site_packages_dir: Path,
    target_site_packages_dir: Path,
    copied_relative_paths: set[str],
) -> list[str]:
    """
    按 distribution 文件清单复制文件。

    这一步非常关键：
    - 不能按目录名猜
    - 要按 distribution 自己声明的 files / RECORD 复制
    - 这样才能正确处理 analyzing-* 共享命名空间
    """

    files = dist.files
    if not files:
        dist_name = dist.metadata.get("Name", "<unknown>")
        raise BuildError(
            f"distribution 缺少 files 元数据，当前实现暂不支持: {dist_name}"
        )

    copied: list[str] = []

    for package_file in files:
        source_file_path = Path(dist.locate_file(package_file)).resolve(strict=False)

        try:
            source_file_path.relative_to(source_site_packages_dir)
        except ValueError:
            # 有些奇怪环境里，文件可能不在目标 site-packages 下。
            # 第一版保守跳过，避免把外部路径误带进来。
            continue

        relative_path = Path(*package_file.parts)
        target_file_path = target_site_packages_dir / relative_path
        relative_key = relative_path.as_posix()

        if source_file_path.is_dir():
            target_file_path.mkdir(parents=True, exist_ok=True)
            continue

        target_file_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file_path, target_file_path)

        if relative_key not in copied_relative_paths:
            copied_relative_paths.add(relative_key)
            copied.append(relative_key)

    return copied


def materialize_runtime_dependencies(
    project_dir: str | Path,
    source_site_packages_dir: str | Path,
    target_site_packages_dir: str | Path,
    include_dev_dependencies: bool = False,
    clean_target: bool = False,
) -> RuntimeDependencyResult:
    """
    从 source_site_packages_dir 中，按当前项目 pyproject.toml 的依赖闭包，
    复制运行时依赖到 target_site_packages_dir。

    推荐目标目录：
    runtime/python/Lib/site-packages
    """

    project_dir_path = Path(project_dir).resolve(strict=False)
    pyproject_file_path = project_dir_path / "pyproject.toml"
    source_site_packages_dir_path = Path(source_site_packages_dir).resolve(strict=False)
    target_site_packages_dir_path = Path(target_site_packages_dir).resolve(strict=False)

    root_dependency_names = _read_project_dependency_names(
        pyproject_file_path=pyproject_file_path,
        include_dev_dependencies=include_dev_dependencies,
    )

    distribution_index = _build_distribution_index(source_site_packages_dir_path)
    resolved_distributions = _resolve_distribution_closure(
        root_dependency_names=root_dependency_names,
        distribution_index=distribution_index,
    )

    if clean_target and target_site_packages_dir_path.exists():
        shutil.rmtree(target_site_packages_dir_path)

    target_site_packages_dir_path.mkdir(parents=True, exist_ok=True)

    copied_relative_paths: set[str] = set()
    copied_files: list[str] = []

    for dist in resolved_distributions:
        copied_files.extend(
            _copy_distribution_files(
                dist=dist,
                source_site_packages_dir=source_site_packages_dir_path,
                target_site_packages_dir=target_site_packages_dir_path,
                copied_relative_paths=copied_relative_paths,
            )
        )

    resolved_distribution_names = [
        canonicalize_name(dist.metadata["Name"])
        for dist in resolved_distributions
        if dist.metadata.get("Name")
    ]

    return RuntimeDependencyResult(
        source_site_packages_dir=source_site_packages_dir_path,
        target_site_packages_dir=target_site_packages_dir_path,
        root_dependency_names=root_dependency_names,
        resolved_distribution_names=resolved_distribution_names,
        copied_files=sorted(copied_files),
    )


__all__ = ["materialize_runtime_dependencies"]
