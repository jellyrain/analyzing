from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import tomllib
from pathlib import Path
from typing import Any

from analyzing.compat.host import HostFeatures, SDKDistribution
from analyzing.runtime.mode import RuntimeMode

from .engine_models import EngineBuildProject, EngineBuildResult
from .host_profile import (
    build_host_profile,
    HOST_PROFILE_FILE_NAME,
    dump_host_profile_data,
)
from .models import BuildError
from .progress import ProgressCallback, emit_progress


def _is_relative_to(path: Path, base_dir: Path) -> bool:
    try:
        path.relative_to(base_dir)
        return True
    except ValueError:
        return False


def _remove_tree_within_base(target_dir: Path, base_dir: Path) -> None:
    normalized_target_dir = target_dir.resolve(strict=False)
    normalized_base_dir = base_dir.resolve(strict=False)

    if not _is_relative_to(normalized_target_dir, normalized_base_dir):
        raise BuildError(f"构建输出目录超出允许范围: {normalized_target_dir}")

    if normalized_target_dir.exists():
        shutil.rmtree(normalized_target_dir)


def _load_engine_project(
    project_dir: str | Path | None,
) -> EngineBuildProject:
    resolved_project_dir = (
        Path.cwd().resolve(strict=False)
        if project_dir is None
        else Path(project_dir).expanduser().resolve(strict=False)
    )
    if not resolved_project_dir.is_dir():
        raise BuildError(f"engine 项目目录不存在: {resolved_project_dir}")

    main_file_path = resolved_project_dir / "main.py"
    if not main_file_path.is_file():
        raise BuildError(f"engine 项目缺少 main.py: {resolved_project_dir}")

    pyproject_file_path = resolved_project_dir / "pyproject.toml"
    if not pyproject_file_path.is_file():
        raise BuildError(f"engine 项目缺少 pyproject.toml: {resolved_project_dir}")

    src_dir_path = resolved_project_dir / "src"
    if not src_dir_path.is_dir():
        raise BuildError(f"engine 项目缺少 src 目录: {resolved_project_dir}")

    config_dir_path = resolved_project_dir / "config"
    if not config_dir_path.is_dir():
        raise BuildError(f"engine 项目缺少 config 目录: {resolved_project_dir}")

    default_config_file_path = config_dir_path / "engine.toml"
    if not default_config_file_path.is_file():
        raise BuildError(f"engine 项目缺少默认配置文件: {default_config_file_path}")

    with pyproject_file_path.open("rb") as fp:
        pyproject_data = tomllib.load(fp)

    project_section = pyproject_data.get("project")
    if not isinstance(project_section, dict):
        raise BuildError(
            f"engine 项目 pyproject.toml 缺少 [project]: {pyproject_file_path}"
        )

    raw_project_name = project_section.get("name")
    if not isinstance(raw_project_name, str) or not raw_project_name.strip():
        raise BuildError(
            f"engine 项目 pyproject.toml 缺少有效的 project.name: {pyproject_file_path}"
        )

    external_dir_paths = _load_external_dir_paths(default_config_file_path)

    return EngineBuildProject(
        project_dir=resolved_project_dir,
        main_file_path=main_file_path,
        pyproject_file_path=pyproject_file_path,
        config_dir_path=config_dir_path,
        default_config_file_path=default_config_file_path,
        project_name=raw_project_name.strip(),
        external_dir_paths=external_dir_paths,
    )


def _load_external_dir_paths(config_file_path: Path) -> list[Path]:
    with config_file_path.open("rb") as fp:
        config_data = tomllib.load(fp)

    paths_section = config_data.get("paths")
    if paths_section is None:
        paths_section = {}

    if not isinstance(paths_section, dict):
        raise BuildError(f"engine.toml 的 [paths] 必须是表对象: {config_file_path}")

    resolved_paths: list[Path] = []
    for key, default_value in (
        ("plugins_dir", "plugins"),
        ("data_dir", "data"),
        ("logs_dir", "data/logs"),
        ("runtime_plugins_dir", "data/plugins"),
    ):
        raw_value = paths_section.get(key, default_value)
        if not isinstance(raw_value, str) or not raw_value.strip():
            raise BuildError(f"engine.toml 的 paths.{key} 必须是非空字符串")

        relative_path = Path(raw_value.strip())
        if relative_path.is_absolute():
            raise BuildError(f"engine 打包不支持绝对路径配置: paths.{key}={raw_value}")

        resolved_paths.append(relative_path)

    deduplicated_paths: list[Path] = []
    seen_paths: set[str] = set()
    for path in resolved_paths:
        normalized = path.as_posix()
        if normalized in seen_paths:
            continue
        deduplicated_paths.append(path)
        seen_paths.add(normalized)

    return deduplicated_paths


def _run_nuitka_build(
    project: EngineBuildProject,
    output_root: Path,
    progress_callback: ProgressCallback | None,
) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--assume-yes-for-downloads",
        "--remove-output",
        f"--output-dir={output_root}",
        f"--output-filename={project.build_name}",
        str(project.main_file_path),
    ]

    emit_progress(
        progress_callback,
        "[engine-build] 开始执行 Nuitka standalone 构建",
    )

    completed = subprocess.Popen(
        command,
        cwd=project.project_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    output_lines: list[str] = []
    assert completed.stdout is not None

    for line in completed.stdout:
        normalized_line = line.rstrip()
        if not normalized_line:
            continue
        output_lines.append(normalized_line)
        emit_progress(progress_callback, f"[nuitka] {normalized_line}")

    return_code = completed.wait()
    if return_code != 0:
        details = "\n".join(output_lines[-40:]).strip()
        raise BuildError("Nuitka engine 构建失败" + (f"\n{details}" if details else ""))

    expected_dist_dir = output_root / f"{project.build_name}.dist"
    if expected_dist_dir.is_dir():
        return expected_dist_dir

    dist_dir_candidates = sorted(
        path for path in output_root.glob("*.dist") if path.is_dir()
    )
    if len(dist_dir_candidates) == 1:
        return dist_dir_candidates[0]

    raise BuildError("Nuitka 构建完成但未找到 engine 发布目录")


def _copy_release_files(
    project: EngineBuildProject,
    dist_dir_path: Path,
    release_dir: Path,
) -> None:
    shutil.copytree(dist_dir_path, release_dir)
    shutil.copytree(
        project.config_dir_path,
        release_dir / project.config_dir_path.name,
        dirs_exist_ok=True,
    )

    for relative_dir_path in project.external_dir_paths:
        (release_dir / relative_dir_path).mkdir(parents=True, exist_ok=True)


def _write_host_profile_snapshot(
    project: EngineBuildProject,
    release_dir: Path,
) -> str:
    """
    生成并写入宿主快照文件，供打包后的 engine 优先读取。
    """

    host_profile = build_host_profile(
        pyproject_file_path=project.pyproject_file_path,
        python_version=platform.python_version(),
        supported_runtime_modes=[
            RuntimeMode.INPROC,
            RuntimeMode.SUBPROCESS,
            RuntimeMode.REMOTE,
        ],
        plugin_package_suffix=".rain",
        features=HostFeatures(
            field_mapping=True,
            plugin_rescan=True,
            supports_output_flatten=True,
            service_mode=True,
        ),
        sdk_distribution=SDKDistribution(
            channel="private",
            public_pypi=False,
            format="wheel",
        ),
    )

    snapshot_file_path = release_dir / HOST_PROFILE_FILE_NAME
    snapshot_file_path.write_text(
        json.dumps(
            dump_host_profile_data(host_profile),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return snapshot_file_path.name


def _iter_dist_info_dirs() -> list[Path]:
    candidate_roots = [
        sysconfig.get_paths().get("purelib"),
        sysconfig.get_paths().get("platlib"),
    ]

    dist_info_dirs: list[Path] = []
    seen_paths: set[Path] = set()

    for raw_root in candidate_roots:
        if not raw_root:
            continue

        root_dir_path = Path(raw_root).resolve(strict=False)
        if not root_dir_path.is_dir():
            continue

        for dist_info_dir_path in sorted(root_dir_path.glob("*.dist-info")):
            normalized_path = dist_info_dir_path.resolve(strict=False)
            if not dist_info_dir_path.is_dir() or normalized_path in seen_paths:
                continue

            dist_info_dirs.append(dist_info_dir_path)
            seen_paths.add(normalized_path)

    return dist_info_dirs


def _copy_dist_info_dirs(
    release_dir: Path,
    progress_callback: ProgressCallback | None,
) -> list[str]:
    copied_dir_names: list[str] = []

    for dist_info_dir_path in _iter_dist_info_dirs():
        target_dir_path = release_dir / dist_info_dir_path.name
        shutil.copytree(
            dist_info_dir_path,
            target_dir_path,
            dirs_exist_ok=True,
        )
        copied_dir_names.append(dist_info_dir_path.name)

    emit_progress(
        progress_callback,
        f"[engine-build] 已复制 {len(copied_dir_names)} 个 dist-info 目录",
    )

    return copied_dir_names


def _resolve_executable_file_path(
    release_dir: Path,
    build_name: str,
) -> Path:
    expected_file_path = release_dir / f"{build_name}.exe"
    if expected_file_path.is_file():
        return expected_file_path

    executable_candidates = sorted(
        path
        for path in release_dir.iterdir()
        if path.is_file() and path.suffix.lower() == ".exe"
    )
    if len(executable_candidates) == 1:
        return executable_candidates[0]

    raise BuildError("engine 发布目录中未找到可执行文件")


def _collect_included_files(release_dir: Path) -> list[str]:
    return sorted(
        path.relative_to(release_dir).as_posix()
        for path in release_dir.rglob("*")
        if path.is_file()
    )


def _build_result_metadata(
    project: EngineBuildProject,
    copied_dist_info_dir_names: list[str],
    host_profile_file_name: str,
) -> dict[str, Any]:
    return {
        "package_type": "engine",
        "build_tool": "nuitka",
        "build_mode": "standalone",
        "project_name": project.project_name,
        "build_name": project.build_name,
        "entry": project.main_file_path.name,
        "dist_info_dirs": copied_dist_info_dir_names,
        "host_profile_file": host_profile_file_name,
    }


def build_engine_package(
    output_dir: str | Path = "dist",
    *,
    project_dir: str | Path | None = None,
    progress_callback: ProgressCallback | None = None,
    is_copy_engine_dist_info: bool = False,
) -> EngineBuildResult:
    """
    将当前 engine 项目构建为 Nuitka standalone 发布目录。
    """

    emit_progress(progress_callback, "[engine-build] 开始加载 engine 项目")
    project = _load_engine_project(project_dir)
    resolved_output_dir = Path(output_dir).expanduser().resolve(strict=False)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    release_dir = resolved_output_dir / project.build_name
    emit_progress(progress_callback, f"[engine-build] 输出目录: {release_dir}")
    _remove_tree_within_base(release_dir, resolved_output_dir)

    with tempfile.TemporaryDirectory(prefix="build_kit-engine-") as tmp_dir:
        build_root = Path(tmp_dir)
        emit_progress(progress_callback, "[engine-build] 准备临时构建目录")
        dist_dir_path = _run_nuitka_build(
            project=project,
            output_root=build_root / "nuitka-output",
            progress_callback=progress_callback,
        )
        emit_progress(progress_callback, "[engine-build] 开始整理发布目录")
        _copy_release_files(
            project=project,
            dist_dir_path=dist_dir_path,
            release_dir=release_dir,
        )
        emit_progress(progress_callback, "[engine-build] 开始写入宿主快照")
        host_profile_file_name = _write_host_profile_snapshot(
            project=project,
            release_dir=release_dir,
        )

        copied_dist_info_dir_names: list[str] = []
        if is_copy_engine_dist_info:
            emit_progress(progress_callback, "[engine-build] 开始复制 dist-info 目录")
            copied_dist_info_dir_names = _copy_dist_info_dirs(
                release_dir=release_dir,
                progress_callback=progress_callback,
            )

    executable_file_path = _resolve_executable_file_path(
        release_dir=release_dir,
        build_name=project.build_name,
    )
    emit_progress(progress_callback, f"[engine-build] 构建完成: {executable_file_path}")

    return EngineBuildResult(
        release_dir=release_dir,
        executable_file_path=executable_file_path,
        included_files=_collect_included_files(release_dir),
        external_dirs=[path.as_posix() for path in project.external_dir_paths],
        metadata=_build_result_metadata(
            project,
            copied_dist_info_dir_names,
            host_profile_file_name,
        ),
    )


def copy_engine_dist_info(
    release_dir: str | Path,
    *,
    progress_callback: ProgressCallback | None = None,
) -> list[str]:
    """
    给现有 engine 发布目录补拷当前环境中的 dist-info
    """

    resolved_release_dir = Path(release_dir).expanduser().resolve(strict=False)
    if not resolved_release_dir.is_dir():
        raise BuildError(f"engine 发布目录不存在: {resolved_release_dir}")

    emit_progress(
        progress_callback,
        f"[engine-build] 开始补拷 dist-info: {resolved_release_dir}",
    )
    copied_dir_names = _copy_dist_info_dirs(
        release_dir=resolved_release_dir,
        progress_callback=progress_callback,
    )
    emit_progress(
        progress_callback,
        f"[engine-build] dist-info 补拷完成: {resolved_release_dir}",
    )
    return copied_dir_names


def copy_release_resource(
    source: str | Path,
    release_dir: str | Path,
    target_name: str,
    target_dir: str | Path = ".",
) -> None:
    resolved_source_path = Path(source).expanduser().resolve(strict=False)
    resolved_release_dir = Path(release_dir).expanduser().resolve(strict=False)

    if not resolved_source_path.exists():
        raise BuildError(f"待复制资源不存在: {resolved_source_path}")

    # 目标名称只能是单个名称，不能借此传入额外路径。
    target_name_path = Path(target_name)
    if (
        not target_name.strip()
        or target_name in {".", ".."}
        or target_name_path.name != target_name
    ):
        raise BuildError(f"target_name 必须是单个文件名或目录名: {target_name!r}")

    # 目标目录只能位于发布根目录内。
    relative_target_dir = Path(target_dir)
    if relative_target_dir.is_absolute() or ".." in relative_target_dir.parts:
        raise BuildError(f"target_dir 必须是发布目录下的相对路径: {target_dir!r}")

    target_parent_dir = (resolved_release_dir / relative_target_dir).resolve(
        strict=False
    )
    if (
        target_parent_dir != resolved_release_dir
        and resolved_release_dir not in target_parent_dir.parents
    ):
        raise BuildError(f"目标目录不在发布目录内: {target_parent_dir}")

    target_path = target_parent_dir / target_name
    target_parent_dir.mkdir(parents=True, exist_ok=True)

    if resolved_source_path.is_dir():
        if target_path.exists() and not target_path.is_dir():
            raise BuildError(f"目录不能覆盖文件: {target_path}")

        shutil.copytree(
            resolved_source_path,
            target_path,
            dirs_exist_ok=True,
        )
        return target_path

    if resolved_source_path.is_file():
        if target_path.exists() and target_path.is_dir():
            raise BuildError(f"文件不能覆盖目录: {target_path}")

        shutil.copy2(resolved_source_path, target_path)
        return target_path

    raise BuildError(f"待复制资源不是普通文件或目录: {resolved_source_path}")


__all__ = ["build_engine_package", "copy_engine_dist_info", "copy_release_resource"]
