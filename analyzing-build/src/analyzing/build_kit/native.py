from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

from analyzing.runtime.config import InprocRuntimeConfig

from .models import BuildError, BuildProject, PackageEntry
from .progress import ProgressCallback, emit_progress


def _to_archive_path(relative_path: Path) -> str:
    return PurePosixPath(relative_path.as_posix()).as_posix()


def _resolve_inproc_package_context(
    project: BuildProject,
) -> tuple[Path, Path, Path | None]:
    runtime = project.manifest.runtime
    if not isinstance(runtime, InprocRuntimeConfig):
        raise BuildError("native 仅支持 inproc 插件")

    module_relative_path = Path(*runtime.entrypoint.module.split(".")).with_suffix(
        ".py"
    )
    package_parts = runtime.entrypoint.module.split(".")[:-1]

    search_roots = runtime.search_paths or ["."]
    for search_path in search_roots:
        search_root = (project.project_dir / search_path).resolve(strict=False)
        module_file_path = search_root / module_relative_path
        if not module_file_path.is_file():
            continue

        package_dir_path = (
            search_root.joinpath(*package_parts) if package_parts else None
        )
        if package_dir_path is not None and not package_dir_path.is_dir():
            raise BuildError(f"native 构建入口包目录不存在: {package_dir_path}")

        return search_root, module_file_path, package_dir_path

    raise BuildError(
        f"native 构建未找到 inproc 入口模块源码: {runtime.entrypoint.module}"
    )


def _collect_compile_targets(
    module_file_path: Path,
    package_dir_path: Path | None,
) -> list[Path]:
    if package_dir_path is None:
        return [module_file_path]

    return sorted(
        path
        for path in package_dir_path.rglob("*.py")
        if path.is_file() and path.name != "__init__.py"
    )


def _run_nuitka_for_module(
    *,
    project: BuildProject,
    search_root: Path,
    module_file_path: Path,
    output_dir: Path,
    cache_dir: Path,
    progress_callback: ProgressCallback | None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    existing_python_path = env.get("PYTHONPATH", "")
    python_path_parts = [str(search_root)]
    if existing_python_path:
        python_path_parts.append(existing_python_path)

    env["PYTHONPATH"] = os.pathsep.join(python_path_parts)
    env["NUITKA_CACHE_DIR"] = str(cache_dir)

    command = [
        sys.executable,
        "-m",
        "nuitka",
        "--mode=module",
        "--nofollow-imports",
        "--assume-yes-for-downloads",
        f"--output-dir={output_dir}",
        str(module_file_path),
    ]

    emit_progress(
        progress_callback,
        "[plugin-build] 开始执行 Nuitka native 构建: "
        f"{module_file_path.relative_to(project.project_dir).as_posix()}",
    )

    completed = subprocess.Popen(
        command,
        cwd=project.project_dir,
        env=env,
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
        raise BuildError(
            "Nuitka native 构建失败: "
            f"{module_file_path.relative_to(project.project_dir)}"
            + (f"\n{details}" if details else "")
        )

    pyd_files = sorted(output_dir.glob(f"{module_file_path.stem}*.pyd"))
    if not pyd_files:
        raise BuildError(
            "Nuitka 构建完成但未产出 .pyd: "
            f"{module_file_path.relative_to(project.project_dir)}"
        )

    return pyd_files[0]


def build_native_package_entries(
    project: BuildProject,
    work_dir: Path,
    progress_callback: ProgressCallback | None = None,
) -> tuple[list[PackageEntry], set[str]]:
    """
    使用 Nuitka 生成 native 产物，并返回应替换掉的源码路径。
    """

    search_root, module_file_path, package_dir_path = _resolve_inproc_package_context(
        project
    )
    compile_targets = _collect_compile_targets(module_file_path, package_dir_path)
    if not compile_targets:
        raise BuildError("native 构建未找到可编译的 Python 模块")

    package_entries: list[PackageEntry] = []
    replaced_archive_paths: set[str] = set()

    build_output_root = work_dir / "nuitka-dist"
    cache_root = work_dir / "nuitka-cache"

    for target in compile_targets:
        relative_to_search_root = target.relative_to(search_root)
        target_output_dir = build_output_root / relative_to_search_root.parent
        target_cache_dir = cache_root / relative_to_search_root.with_suffix("")

        built_file_path = _run_nuitka_for_module(
            project=project,
            search_root=search_root,
            module_file_path=target,
            output_dir=target_output_dir,
            cache_dir=target_cache_dir,
            progress_callback=progress_callback,
        )

        package_entries.append(
            PackageEntry(
                source_path=built_file_path,
                archive_path=_to_archive_path(
                    relative_to_search_root.with_name(built_file_path.name)
                ),
            )
        )
        replaced_archive_paths.add(_to_archive_path(relative_to_search_root))

    return package_entries, replaced_archive_paths
