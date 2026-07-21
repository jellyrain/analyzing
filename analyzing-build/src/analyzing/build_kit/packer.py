from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

from .collector import collect_package_entries
from .loader import load_build_project
from .metadata import build_rain_metadata
from .native import build_native_package_entries
from .models import (
    PLUGIN_MANIFEST_FILE_NAME,
    RAIN_METADATA_FILE_NAME,
    BuildError,
    BuildResult,
)
from .progress import ProgressCallback, emit_progress


def _default_output_dir(project_dir: Path) -> Path:
    return project_dir / "dist"


def _rain_file_name(plugin_id: str, version: str) -> str:
    return f"{plugin_id}-{version}.rain"


def build_plugin_package(
    project_dir: str | Path,
    output_dir: str | Path | None = None,
    progress_callback: ProgressCallback | None = None,
) -> BuildResult:
    """
    将单插件源码目录构建为 .rain。
    """

    emit_progress(progress_callback, f"[plugin-build] 开始加载插件项目: {project_dir}")
    project = load_build_project(project_dir)
    if project.build_config.variant not in (None, "plain", "native"):
        raise BuildError(f"不支持的 build variant: {project.build_config.variant}")

    native_entries = []
    replaced_archive_paths: set[str] = set()
    if project.build_config.variant == "native":
        runtime_mode = getattr(
            project.manifest.runtime_mode,
            "value",
            project.manifest.runtime_mode,
        )
        if runtime_mode != "inproc":
            raise BuildError("native 仅支持 inproc 插件")

        with tempfile.TemporaryDirectory(prefix="build_kit-native-") as tmp_dir:
            emit_progress(
                progress_callback,
                f"[plugin-build] 使用 native 变体构建插件: {project.manifest.plugin_id}",
            )
            native_entries, replaced_archive_paths = build_native_package_entries(
                project=project,
                work_dir=Path(tmp_dir),
                progress_callback=progress_callback,
            )
            emit_progress(progress_callback, "[plugin-build] 开始收集源码文件")
            plain_entries = collect_package_entries(
                project,
                replaced_archive_paths=replaced_archive_paths,
            )
            entries = sorted(
                [*plain_entries, *native_entries],
                key=lambda item: item.archive_path,
            )
            emit_progress(progress_callback, "[plugin-build] 开始生成打包元数据")
            metadata = build_rain_metadata(project)
            return _write_rain_file(
                project=project,
                entries=entries,
                metadata=metadata,
                output_dir=output_dir,
                progress_callback=progress_callback,
            )

    emit_progress(progress_callback, "[plugin-build] 开始收集待打包文件")
    entries = collect_package_entries(project)
    emit_progress(progress_callback, "[plugin-build] 开始生成打包元数据")
    metadata = build_rain_metadata(project)

    return _write_rain_file(
        project=project,
        entries=entries,
        metadata=metadata,
        output_dir=output_dir,
        progress_callback=progress_callback,
    )


def _write_rain_file(
    *,
    project,
    entries,
    metadata,
    output_dir: str | Path | None,
    progress_callback: ProgressCallback | None,
) -> BuildResult:

    resolved_output_dir = (
        Path(output_dir).expanduser().resolve(strict=False)
        if output_dir is not None
        else _default_output_dir(project.project_dir)
    )
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    rain_file_path = resolved_output_dir / _rain_file_name(
        project.manifest.plugin_id,
        project.manifest.version,
    )
    emit_progress(
        progress_callback,
        f"[plugin-build] 开始写入 .rain 包: {rain_file_path}",
    )

    try:
        with zipfile.ZipFile(
            rain_file_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as zf:
            for entry in entries:
                if entry.archive_path == PLUGIN_MANIFEST_FILE_NAME:
                    # plugin.toml 使用 SDK 物化后的内容写入包内，
                    # 避免要求开发者手工维护 baseline_dependencies。
                    zf.writestr(entry.archive_path, project.packaged_manifest_text)
                    continue

                zf.write(entry.source_path, arcname=entry.archive_path)

            zf.writestr(
                RAIN_METADATA_FILE_NAME,
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            )
    except OSError as exc:
        raise BuildError(f".rain 打包失败: {exc}") from exc

    included_files = [entry.archive_path for entry in entries]
    included_files.append(RAIN_METADATA_FILE_NAME)
    emit_progress(progress_callback, f"[plugin-build] 构建完成: {rain_file_path}")

    return BuildResult(
        rain_file_path=rain_file_path,
        included_files=included_files,
        metadata=metadata,
    )
