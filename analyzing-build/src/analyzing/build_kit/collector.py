from __future__ import annotations

import fnmatch
from pathlib import Path, PurePosixPath

from analyzing.runtime.config import InprocRuntimeConfig, SubprocessRuntimeConfig

from .models import (
    BUILD_CONFIG_FILE_NAME,
    DEFAULT_EXCLUDED_NAMES,
    PLUGIN_MANIFEST_FILE_NAME,
    BuildError,
    BuildProject,
    PackageEntry,
)


def _to_archive_path(relative_path: Path) -> str:
    return PurePosixPath(relative_path.as_posix()).as_posix()


def _matches_pattern(relative_path: Path, pattern: str) -> bool:
    normalized_path = _to_archive_path(relative_path)
    normalized_pattern = pattern.replace("\\", "/").strip("/")

    if not normalized_pattern:
        return False

    if fnmatch.fnmatch(normalized_path, normalized_pattern):
        return True

    if normalized_path == normalized_pattern:
        return True

    return normalized_path.startswith(normalized_pattern + "/")


def _is_excluded(
    relative_path: Path,
    project: BuildProject,
) -> bool:
    if relative_path.name == BUILD_CONFIG_FILE_NAME:
        return True

    if any(part in DEFAULT_EXCLUDED_NAMES for part in relative_path.parts):
        return True

    return any(
        _matches_pattern(relative_path, pattern)
        for pattern in project.build_config.exclude
    )


def _resolve_form_schema_source_path(project: BuildProject) -> Path | None:
    """
    解析插件声明的表单 schema 文件路径。
    """

    form_schema_file = project.manifest.form_schema_file
    if not form_schema_file:
        return None

    relative_path = Path(form_schema_file)
    if relative_path.is_absolute():
        raise BuildError(f"form_schema_file 必须是相对路径: {form_schema_file}")

    resolved_path = (project.project_dir / relative_path).resolve(strict=False)
    if not resolved_path.is_file():
        raise BuildError(f"form schema 文件不存在: {form_schema_file}")

    return resolved_path


def _iter_included_paths(project: BuildProject) -> list[Path]:
    if project.build_config.include:
        included_paths: list[Path] = []
        for item in project.build_config.include:
            candidate = (project.project_dir / item).resolve(strict=False)
            try:
                relative_path = candidate.relative_to(project.project_dir)
            except ValueError as exc:
                raise BuildError(
                    f"build.toml include 超出插件目录范围: {item}"
                ) from exc

            if not candidate.exists():
                raise BuildError(f"build.toml include 指向的路径不存在: {item}")

            if _is_excluded(relative_path, project):
                raise BuildError(f"build.toml include 指向的路径被排除规则拦截: {item}")

            included_paths.append(candidate)

        return included_paths

    default_paths = [project.manifest_file_path]
    form_schema_source_path = _resolve_form_schema_source_path(project)
    if form_schema_source_path is not None:
        default_paths.append(form_schema_source_path)

    plugin_py = project.project_dir / "plugin.py"
    if plugin_py.is_file():
        default_paths.append(plugin_py)

    src_dir = project.project_dir / "src"
    if src_dir.is_dir():
        default_paths.append(src_dir)

    return default_paths


def _collect_from_path(project: BuildProject, source_path: Path) -> list[PackageEntry]:
    if source_path.is_file():
        relative_path = source_path.relative_to(project.project_dir)
        if _is_excluded(relative_path, project):
            return []

        return [
            PackageEntry(
                source_path=source_path,
                archive_path=_to_archive_path(relative_path),
            )
        ]

    entries: list[PackageEntry] = []
    for file_path in sorted(path for path in source_path.rglob("*") if path.is_file()):
        relative_path = file_path.relative_to(project.project_dir)
        if _is_excluded(relative_path, project):
            continue

        entries.append(
            PackageEntry(
                source_path=file_path,
                archive_path=_to_archive_path(relative_path),
            )
        )

    return entries


def _validate_inproc_entrypoint(project: BuildProject, archive_paths: set[str]) -> None:
    runtime = project.manifest.runtime
    if not isinstance(runtime, InprocRuntimeConfig):
        return

    if project.build_config.variant == "native":
        return

    module_relative_path = Path(*runtime.entrypoint.module.split(".")).with_suffix(
        ".py"
    )

    candidate_paths: list[Path] = [module_relative_path]
    for search_path in runtime.search_paths:
        candidate_paths.append(Path(search_path) / module_relative_path)

    if any(_to_archive_path(path) in archive_paths for path in candidate_paths):
        return

    raise BuildError(
        "inproc 插件入口模块未被打包，请检查默认规则或 build.toml include: "
        f"{runtime.entrypoint.module}"
    )


def _validate_subprocess_launcher(
    project: BuildProject, archive_paths: set[str]
) -> None:
    runtime = project.manifest.runtime
    if not isinstance(runtime, SubprocessRuntimeConfig):
        return

    launcher = runtime.launcher
    if launcher.cwd is not None:
        cwd_path = (project.project_dir / launcher.cwd).resolve(strict=False)
        if not cwd_path.exists():
            raise BuildError(f"subprocess launcher.cwd 不存在: {launcher.cwd}")

    args = launcher.args
    if len(args) >= 2 and args[0] == "-m":
        module_relative_path = Path(*args[1].split(".")).with_suffix(".py")

        candidate_paths: list[Path] = [module_relative_path]
        if launcher.cwd:
            candidate_paths.append(Path(launcher.cwd) / module_relative_path)

        if any(_to_archive_path(path) in archive_paths for path in candidate_paths):
            return

        raise BuildError(
            "subprocess 插件入口模块未被打包，请检查默认规则或 build.toml include: "
            f"{args[1]}"
        )


def _validate_form_schema_file(project: BuildProject, archive_paths: set[str]) -> None:
    """
    如果插件声明了 form_schema_file，则要求对应文件被打包。
    """

    form_schema_file = project.manifest.form_schema_file
    if not form_schema_file:
        return

    archive_path = _to_archive_path(Path(form_schema_file))
    if archive_path in archive_paths:
        return

    raise BuildError(
        "插件声明了 form_schema_file，但对应文件未被打包，请检查默认规则或 build.toml include: "
        f"{form_schema_file}"
    )


def collect_package_entries(
    project: BuildProject,
    replaced_archive_paths: set[str] | None = None,
) -> list[PackageEntry]:
    """
    根据默认规则或 build.toml 收集待打包文件。
    """

    entries_by_archive_path: dict[str, PackageEntry] = {}
    replaced_archive_paths = replaced_archive_paths or set()

    for included_path in _iter_included_paths(project):
        for entry in _collect_from_path(project, included_path):
            if entry.archive_path in replaced_archive_paths:
                continue
            entries_by_archive_path[entry.archive_path] = entry

    manifest_archive_path = PLUGIN_MANIFEST_FILE_NAME
    if manifest_archive_path not in entries_by_archive_path:
        entries_by_archive_path[manifest_archive_path] = PackageEntry(
            source_path=project.manifest_file_path,
            archive_path=manifest_archive_path,
        )

    archive_paths = set(entries_by_archive_path)
    _validate_inproc_entrypoint(project, archive_paths)
    _validate_subprocess_launcher(project, archive_paths)
    _validate_form_schema_file(project, archive_paths)

    return sorted(entries_by_archive_path.values(), key=lambda item: item.archive_path)
