from __future__ import annotations

import json
import shutil
import tomllib
import zipfile
from pathlib import Path, PurePosixPath

from analyzing.plugin.manifest import PluginManifest

from src.install.schemas import RainSyncResult, RainPackageSpec
from src.app.schemas import EngineConfig
from src.registry.constants import PLUGIN_MANIFEST_FILE_NAME

RAIN_PACKAGE_SUFFIX = ".rain"
RAIN_METADATA_FILE_NAME = "__rain__/package.json"
PLUGIN_ROLE_DIR_NAMES = {"biz", "infra"}


def _enum_value(raw: object) -> str:
    return str(getattr(raw, "value", raw))


def _read_manifest_from_zip(zip_file: zipfile.ZipFile) -> PluginManifest:
    try:
        manifest_bytes = zip_file.read(PLUGIN_MANIFEST_FILE_NAME)
    except KeyError as exc:
        raise FileNotFoundError(f".rain 缺少 {PLUGIN_MANIFEST_FILE_NAME}") from exc

    raw_text = manifest_bytes.decode("utf-8")
    raw_data = tomllib.loads(raw_text)
    return PluginManifest.model_validate(raw_data)


def _read_metadata_from_zip(zip_file: zipfile.ZipFile) -> dict | None:
    try:
        metadata_bytes = zip_file.read(RAIN_METADATA_FILE_NAME)
    except KeyError:
        return None

    return json.loads(metadata_bytes.decode("utf-8"))


def _resolve_role_dir_name(
    manifest: PluginManifest,
    metadata: dict | None,
) -> str:
    if metadata is not None:
        install = metadata.get("install")
        if isinstance(install, dict):
            raw_role = install.get("role")
            if isinstance(raw_role, str) and raw_role in PLUGIN_ROLE_DIR_NAMES:
                return raw_role

    role_dir_name = _enum_value(manifest.plugin_role)
    if role_dir_name not in PLUGIN_ROLE_DIR_NAMES:
        raise ValueError(f"不支持的 plugin_role: {role_dir_name}")

    return role_dir_name


def _resolve_target_dir_name(
    manifest: PluginManifest,
) -> str:
    return f"{manifest.plugin_id}-{manifest.version}"


def _read_rain_package_spec(package_file_path: Path) -> RainPackageSpec:
    with zipfile.ZipFile(package_file_path) as zip_file:
        manifest = _read_manifest_from_zip(zip_file)
        metadata = _read_metadata_from_zip(zip_file)

    return RainPackageSpec(
        package_file_path=package_file_path,
        manifest=manifest,
        role_dir_name=_resolve_role_dir_name(manifest, metadata),
        target_dir_name=_resolve_target_dir_name(manifest),
        modified_at_ns=package_file_path.stat().st_mtime_ns,
    )


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
        raise ValueError(f"目标目录超出允许范围: {normalized_target_dir}")

    if normalized_target_dir.exists():
        shutil.rmtree(normalized_target_dir)


def _safe_extract(zip_file: zipfile.ZipFile, target_dir: Path) -> None:
    normalized_target_dir = target_dir.resolve(strict=False)

    for member in zip_file.infolist():
        member_path = PurePosixPath(member.filename)

        if member_path.is_absolute():
            raise ValueError(f".rain 中存在非法绝对路径: {member.filename}")

        if ".." in member_path.parts:
            raise ValueError(f".rain 中存在非法相对路径: {member.filename}")

        destination_path = (normalized_target_dir / Path(*member_path.parts)).resolve(
            strict=False
        )
        if not _is_relative_to(destination_path, normalized_target_dir):
            raise ValueError(f".rain 解包目标越界: {member.filename}")

    zip_file.extractall(normalized_target_dir)


def _managed_plugin_dirs(runtime_plugins_dir_path: Path) -> dict[str, list[Path]]:
    managed_dirs_by_plugin_id: dict[str, list[Path]] = {}

    for role_dir_name in sorted(PLUGIN_ROLE_DIR_NAMES):
        role_dir_path = runtime_plugins_dir_path / role_dir_name
        if not role_dir_path.is_dir():
            continue

        for plugin_dir_path in sorted(
            path for path in role_dir_path.iterdir() if path.is_dir()
        ):
            manifest_file_path = plugin_dir_path / PLUGIN_MANIFEST_FILE_NAME
            metadata_file_path = plugin_dir_path / RAIN_METADATA_FILE_NAME
            if not manifest_file_path.is_file() or not metadata_file_path.is_file():
                continue

            try:
                raw_data = tomllib.loads(manifest_file_path.read_text(encoding="utf-8"))
                manifest = PluginManifest.model_validate(raw_data)
            except Exception:
                continue

            managed_dirs_by_plugin_id.setdefault(manifest.plugin_id, []).append(
                plugin_dir_path
            )

    return managed_dirs_by_plugin_id


def _is_installed_plugin_dir_complete(plugin_dir_path: Path) -> bool:
    """
    判断目标插件目录是否已经是一个完整安装结果
    """

    manifest_file_path = plugin_dir_path / PLUGIN_MANIFEST_FILE_NAME
    metadata_file_path = plugin_dir_path / RAIN_METADATA_FILE_NAME
    return manifest_file_path.is_file() and metadata_file_path.is_file()


def _deduplicate_specs(
    specs: list[RainPackageSpec], result: RainSyncResult
) -> list[RainPackageSpec]:
    selected_by_plugin_id: dict[str, RainPackageSpec] = {}

    for spec in specs:
        existing = selected_by_plugin_id.get(spec.plugin_id)
        if existing is None:
            selected_by_plugin_id[spec.plugin_id] = spec
            continue

        if spec.modified_at_ns >= existing.modified_at_ns:
            selected_by_plugin_id[spec.plugin_id] = spec
            kept = spec.package_file_path.name
            skipped = existing.package_file_path.name
        else:
            kept = existing.package_file_path.name
            skipped = spec.package_file_path.name

        result.warnings.append(
            f"发现重复的 .rain 插件包，保留较新的一个: plugin_id={spec.plugin_id}, kept={kept}, skipped={skipped}"
        )

    return sorted(
        selected_by_plugin_id.values(),
        key=lambda item: (item.role_dir_name, item.target_dir_name),
    )


def sync_rain_plugins(config: EngineConfig) -> RainSyncResult:
    """
    将 plugins/*.rain 同步解包到 data/plugins/<role>/<plugin-dir>/
    """

    result = RainSyncResult()
    packages_dir_path = config.paths.plugins_dir_path
    runtime_plugins_dir_path = config.paths.runtime_plugins_dir_path

    if packages_dir_path is None or runtime_plugins_dir_path is None:
        return result

    package_file_paths = sorted(
        path
        for path in packages_dir_path.glob(f"*{RAIN_PACKAGE_SUFFIX}")
        if path.is_file()
    )

    raw_specs: list[RainPackageSpec] = []
    for package_file_path in package_file_paths:
        try:
            raw_specs.append(_read_rain_package_spec(package_file_path))
        except Exception as exc:
            result.warnings.append(
                f".rain 包读取失败，已跳过: {package_file_path.name}, reason={exc}"
            )

    specs = _deduplicate_specs(raw_specs, result)
    desired_dirs_by_plugin_id = {
        spec.plugin_id: runtime_plugins_dir_path / spec.target_relative_dir
        for spec in specs
    }

    managed_dirs_by_plugin_id = _managed_plugin_dirs(runtime_plugins_dir_path)

    # 先清理当前不该存在的旧版本目录。
    for plugin_id, managed_dirs in managed_dirs_by_plugin_id.items():
        desired_dir = desired_dirs_by_plugin_id.get(plugin_id)

        for managed_dir in managed_dirs:
            if desired_dir is not None and managed_dir == desired_dir:
                continue

            _remove_tree_within_base(managed_dir, runtime_plugins_dir_path)
            result.removed_dirs.append(str(managed_dir))

    # 再处理当前应该保留的目标版本。
    for spec in specs:
        role_dir_path = runtime_plugins_dir_path / spec.role_dir_name
        target_dir_path = role_dir_path / spec.target_dir_name
        role_dir_path.mkdir(parents=True, exist_ok=True)

        # 目标版本目录已经完整存在，说明已经装过，直接跳过。
        if target_dir_path.is_dir() and _is_installed_plugin_dir_complete(
            target_dir_path
        ):
            continue

        # 目标目录存在但不完整，说明可能是上次中断或残留脏目录，先删再装。
        if target_dir_path.exists():
            _remove_tree_within_base(target_dir_path, runtime_plugins_dir_path)

        target_dir_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(spec.package_file_path) as zip_file:
            _safe_extract(zip_file, target_dir_path)

        result.installed_plugins.append(f"{spec.plugin_id} -> {target_dir_path}")

    return result


__all__ = ["sync_rain_plugins"]
