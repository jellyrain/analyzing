from __future__ import annotations

from typing import Any

from analyzing.monitor.errors import MonitorSchemaError, MonitorTrackingError
from analyzing.monitor.namespaces import (
    EXECUTIONS_NAMESPACE,
    HOST_SNAPSHOTS_NAMESPACE,
    PLUGIN_EVENTS_NAMESPACE,
    PLUGIN_INVOCATIONS_NAMESPACE,
    PLUGIN_STATUS_NAMESPACE,
    SYSTEM_SNAPSHOTS_NAMESPACE,
    ACCESS_LOGS_NAMESPACE,
)
from analyzing.monitor.records import (
    ExecutionRecord,
    HostSnapshotRecord,
    PluginEventRecord,
    PluginInvocationRecord,
    PluginStatusRecord,
    SystemSnapshotRecord,
    AccessLogRecord,
)
from analyzing.monitor.schemas import MONITOR_SCHEMAS
from analyzing.persistence.protocols import PersistenceService
from analyzing.persistence.records import PersistenceRecord


class MonitorTracker:
    """
    monitor 埋点入口

    它只负责把 monitor 领域记录转换成 persistence 通用记录，
    不直接依赖具体数据库实现。
    """

    def __init__(self, persistence: PersistenceService) -> None:
        # monitor 依赖的统一存储服务
        self._persistence = persistence

    def ensure_ready(self) -> None:
        """
        确保 monitor 需要的 schema 已登记
        """

        try:
            for schema in MONITOR_SCHEMAS:
                self._persistence.ensure_schema(schema)
        except Exception as exc:
            raise MonitorSchemaError("monitor schema 初始化失败") from exc

    def record_plugin_event(self, record: PluginEventRecord) -> None:
        """
        记录一条插件事件
        """

        self._upsert(
            namespace=PLUGIN_EVENTS_NAMESPACE,
            record_id=record.event_id,
            payload=record.model_dump(mode="json"),
            indexed_values={
                "plugin_id": record.plugin_id,
                "event_type": record.event_type,
                "created_at": record.created_at,
            },
            created_at=record.created_at,
            updated_at=record.created_at,
        )

    def record_plugin_invocation(self, record: PluginInvocationRecord) -> None:
        """
        记录一条插件调用
        """

        self._upsert(
            namespace=PLUGIN_INVOCATIONS_NAMESPACE,
            record_id=record.invocation_id,
            payload=record.model_dump(mode="json"),
            indexed_values={
                "execution_id": record.execution_id,
                "plugin_id": record.plugin_id,
                "runtime_mode": record.runtime_mode,
                "status": record.status,
                "started_at": record.started_at,
            },
            created_at=record.started_at,
            updated_at=record.finished_at or record.started_at,
        )

    def record_plugin_status(self, record: PluginStatusRecord) -> None:
        """
        记录插件当前状态快照
        """

        self._upsert(
            namespace=PLUGIN_STATUS_NAMESPACE,
            record_id=record.plugin_id,
            payload=record.model_dump(mode="json"),
            indexed_values={
                "plugin_id": record.plugin_id,
                "install_status": record.install_status,
                "runtime_status": record.runtime_status,
                "updated_at": record.updated_at,
            },
            created_at=record.updated_at,
            updated_at=record.updated_at,
        )

    def record_access_log(self, record: AccessLogRecord) -> None:
        """
        记录一条 API 访问日志
        """

        self._upsert(
            namespace=ACCESS_LOGS_NAMESPACE,
            record_id=record.access_id,
            payload=record.model_dump(mode="json"),
            indexed_values={
                "method": record.method,
                "path": record.path,
                "status_code": record.status_code,
                "client_ip": record.client_ip,
                "trace_id": record.trace_id,
                "created_at": record.created_at,
            },
            created_at=record.created_at,
            updated_at=record.created_at,
        )

    def record_execution(self, record: ExecutionRecord) -> None:
        """
        记录一条宿主执行
        """

        self._upsert(
            namespace=EXECUTIONS_NAMESPACE,
            record_id=record.execution_id,
            payload=record.model_dump(mode="json"),
            indexed_values={
                "trace_id": record.trace_id,
                "status": record.status,
                "started_at": record.started_at,
            },
            created_at=record.started_at,
            updated_at=record.finished_at or record.started_at,
        )

    def record_system_snapshot(self, record: SystemSnapshotRecord) -> None:
        """
        记录一条系统快照
        """

        self._upsert(
            namespace=SYSTEM_SNAPSHOTS_NAMESPACE,
            record_id=record.snapshot_id,
            payload=record.model_dump(mode="json"),
            indexed_values={
                "created_at": record.created_at,
            },
            created_at=record.created_at,
            updated_at=record.created_at,
        )

    def record_host_snapshot(self, record: HostSnapshotRecord) -> None:
        """
        记录一条主机快照
        """

        self._upsert(
            namespace=HOST_SNAPSHOTS_NAMESPACE,
            record_id=record.snapshot_id,
            payload=record.model_dump(mode="json"),
            indexed_values={
                "created_at": record.created_at,
            },
            created_at=record.created_at,
            updated_at=record.created_at,
        )

    def _upsert(
        self,
        *,
        namespace: str,
        record_id: str,
        payload: dict[str, Any],
        indexed_values: dict[str, Any],
        created_at: Any,
        updated_at: Any,
    ) -> None:
        """
        将 monitor 记录统一转换为 persistence 通用记录
        """

        try:
            self._persistence.upsert(
                PersistenceRecord(
                    namespace=namespace,
                    record_id=record_id,
                    payload=payload,
                    indexed_values=indexed_values,
                    created_at=created_at,
                    updated_at=updated_at,
                    version=1,
                )
            )
        except Exception as exc:
            raise MonitorTrackingError(
                f"monitor 记录写入失败: namespace={namespace}, record_id={record_id}"
            ) from exc


__all__ = ["MonitorTracker"]
