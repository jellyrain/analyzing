from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import psutil
from analyzing.compat.host import HostProfile
from analyzing.monitor.records import (
    HostSnapshotRecord,
    PluginStatusRecord,
    SystemSnapshotRecord,
)
from analyzing.monitor.tracker import MonitorTracker
from analyzing.plugin.enums.plugin import RuntimeStatus

from src.registry.schemas import PluginCatalog, PluginCatalogEntry
from src.utils.time import get_curr_time


def _get_monitor_disk_root() -> str:
    """
    解析当前引擎所在磁盘的根目录
    """

    current_path = Path.cwd().resolve()
    return current_path.anchor or str(current_path)


def build_plugin_status_record(
    entry: PluginCatalogEntry,
    *,
    updated_at: datetime | None = None,
) -> PluginStatusRecord | None:
    """
    将引擎内的插件登记项转换成 monitor 插件状态记录
    """

    manifest = entry.manifest
    if manifest is None:
        return None

    return PluginStatusRecord(
        plugin_id=manifest.plugin_id,
        version=manifest.version,
        install_status=entry.install_status,
        runtime_status=entry.runtime_status,
        updated_at=updated_at or get_curr_time(),
        detail={
            "plugin_dir": str(entry.plugin_dir_path),
            "is_compatible": entry.is_compatible,
            "error_message": entry.error_message or "",
            "plugin_role": getattr(manifest.plugin_role, "value", manifest.plugin_role),
            "runtime_mode": getattr(
                manifest.runtime_mode, "value", manifest.runtime_mode
            ),
        },
    )


def sync_plugin_catalog_statuses(
    tracker: MonitorTracker,
    plugin_catalog: PluginCatalog,
) -> None:
    """
    将当前插件注册表状态整批写入 monitor。
    """

    updated_at = get_curr_time()

    for entry in plugin_catalog.list_entries():
        record = build_plugin_status_record(entry, updated_at=updated_at)
        if record is None:
            continue

        tracker.record_plugin_status(record)


def record_system_snapshot(
    tracker: MonitorTracker,
    plugin_catalog: PluginCatalog,
    *,
    running_execution_count: int = 0,
) -> None:
    """
    记录一条当前引擎系统快照。
    """

    entries = plugin_catalog.list_entries()
    ready_statuses = {
        RuntimeStatus.READY,
        RuntimeStatus.LOADED,
        RuntimeStatus.REGISTERED,
    }

    tracker.record_system_snapshot(
        SystemSnapshotRecord(
            snapshot_id=uuid4().hex,
            plugin_count=len(entries),
            ready_plugin_count=sum(
                1 for entry in entries if entry.runtime_status in ready_statuses
            ),
            error_plugin_count=sum(
                1 for entry in entries if entry.runtime_status == RuntimeStatus.ERROR
            ),
            running_execution_count=running_execution_count,
            detail={},
            created_at=get_curr_time(),
        )
    )


def record_host_snapshot(
    tracker: MonitorTracker,
    host_profile: HostProfile,
    *,
    root_dir_path: Path | None = None,
) -> None:
    """
    记录一条当前宿主画像快照。
    """

    tracker.record_host_snapshot(
        HostSnapshotRecord(
            snapshot_id=uuid4().hex,
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
            disk_percent=psutil.disk_usage(_get_monitor_disk_root()).percent,
            detail={
                "root_dir": str(root_dir_path) if root_dir_path is not None else None,
                "host_profile": host_profile.model_dump(mode="json"),
            },
            created_at=get_curr_time(),
        )
    )


__all__ = [
    "build_plugin_status_record",
    "record_host_snapshot",
    "record_system_snapshot",
    "sync_plugin_catalog_statuses",
]
