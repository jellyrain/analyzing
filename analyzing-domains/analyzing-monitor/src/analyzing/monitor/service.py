from __future__ import annotations

from typing import TypeVar

from analyzing.monitor.errors import MonitorQueryError
from analyzing.monitor.namespaces import (
    EXECUTIONS_NAMESPACE,
    HOST_SNAPSHOTS_NAMESPACE,
    PLUGIN_EVENTS_NAMESPACE,
    PLUGIN_INVOCATIONS_NAMESPACE,
    PLUGIN_STATUS_NAMESPACE,
    SYSTEM_SNAPSHOTS_NAMESPACE,
    ACCESS_LOGS_NAMESPACE,
)
from analyzing.monitor.queries import (
    ExecutionQuery,
    HostSnapshotQuery,
    PluginEventQuery,
    PluginInvocationQuery,
    PluginStatusQuery,
    SystemSnapshotQuery,
    AccessLogQuery,
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
from analyzing.persistence.builder import (
    build_page,
    indexed_eq,
    indexed_gte,
    indexed_lte,
    indexed_sort,
)
from analyzing.persistence.protocols import PersistenceService
from analyzing.persistence.queries import PageRequest, QueryRequest, SortDirection
from analyzing.persistence.records import PersistenceRecord

_RecordModelT = TypeVar(
    "_RecordModelT",
    PluginEventRecord,
    PluginInvocationRecord,
    PluginStatusRecord,
    ExecutionRecord,
    SystemSnapshotRecord,
    HostSnapshotRecord,
    AccessLogRecord,
)


class MonitorService:
    """
    monitor 读取服务

    它负责把 monitor 领域查询翻译成 persistence 查询，
    并把 persistence 记录还原为 monitor 领域对象。
    """

    def __init__(self, persistence: PersistenceService) -> None:
        # monitor 依赖的统一存储服务
        self._persistence = persistence

    def list_plugin_events(
        self,
        query: PluginEventQuery,
    ) -> list[PluginEventRecord]:
        """
        查询插件事件记录
        """

        records = self._query_namespace(
            namespace=PLUGIN_EVENTS_NAMESPACE,
            filters=[
                indexed_eq("plugin_id", query.plugin_id),
                indexed_eq("event_type", query.event_type),
                indexed_gte("created_at", query.created_from),
                indexed_lte("created_at", query.created_to),
            ],
            sorts=[
                indexed_sort("created_at", SortDirection.DESC),
            ],
            page=build_page(query.offset, query.limit),
        )
        return self._decode_records(records, PluginEventRecord)

    def list_plugin_invocations(
        self,
        query: PluginInvocationQuery,
    ) -> list[PluginInvocationRecord]:
        """
        查询插件调用记录
        """

        records = self._query_namespace(
            namespace=PLUGIN_INVOCATIONS_NAMESPACE,
            filters=[
                indexed_eq("execution_id", query.execution_id),
                indexed_eq("plugin_id", query.plugin_id),
                indexed_eq("status", query.status),
                indexed_eq("runtime_mode", query.runtime_mode),
                indexed_gte("started_at", query.started_from),
                indexed_lte("started_at", query.started_to),
            ],
            sorts=[
                indexed_sort("started_at", SortDirection.DESC),
            ],
            page=build_page(query.offset, query.limit),
        )
        return self._decode_records(records, PluginInvocationRecord)

    def list_plugin_status(
        self,
        query: PluginStatusQuery,
    ) -> list[PluginStatusRecord]:
        """
        查询插件当前状态记录
        """

        records = self._query_namespace(
            namespace=PLUGIN_STATUS_NAMESPACE,
            filters=[
                indexed_eq("plugin_id", query.plugin_id),
                indexed_eq("install_status", query.install_status),
                indexed_eq("runtime_status", query.runtime_status),
            ],
            sorts=[
                indexed_sort("updated_at", SortDirection.DESC),
            ],
            page=build_page(query.offset, query.limit),
        )
        return self._decode_records(records, PluginStatusRecord)

    def list_access_logs(
        self,
        query: AccessLogQuery,
    ) -> list[AccessLogRecord]:
        """
        查询 API 访问日志
        """

        records = self._query_namespace(
            namespace=ACCESS_LOGS_NAMESPACE,
            filters=[
                indexed_eq("method", query.method),
                indexed_eq("path", query.path),
                indexed_eq("status_code", query.status_code),
                indexed_eq("client_ip", query.client_ip),
                indexed_eq("trace_id", query.trace_id),
                indexed_gte("created_at", query.created_from),
                indexed_lte("created_at", query.created_to),
            ],
            sorts=[
                indexed_sort("created_at", SortDirection.DESC),
            ],
            page=build_page(query.offset, query.limit),
        )
        return self._decode_records(records, AccessLogRecord)

    def list_executions(
        self,
        query: ExecutionQuery,
    ) -> list[ExecutionRecord]:
        """
        查询宿主执行记录
        """

        records = self._query_namespace(
            namespace=EXECUTIONS_NAMESPACE,
            filters=[
                indexed_eq("trace_id", query.trace_id),
                indexed_eq("status", query.status),
                indexed_gte("started_at", query.started_from),
                indexed_lte("started_at", query.started_to),
            ],
            sorts=[
                indexed_sort("started_at", SortDirection.DESC),
            ],
            page=build_page(query.offset, query.limit),
        )
        return self._decode_records(records, ExecutionRecord)

    def list_system_snapshots(
        self,
        query: SystemSnapshotQuery,
    ) -> list[SystemSnapshotRecord]:
        """
        查询系统快照记录
        """

        records = self._query_namespace(
            namespace=SYSTEM_SNAPSHOTS_NAMESPACE,
            filters=[
                indexed_gte("created_at", query.created_from),
                indexed_lte("created_at", query.created_to),
            ],
            sorts=[
                indexed_sort("created_at", SortDirection.DESC),
            ],
            page=build_page(query.offset, query.limit),
        )
        return self._decode_records(records, SystemSnapshotRecord)

    def list_host_snapshots(
        self,
        query: HostSnapshotQuery,
    ) -> list[HostSnapshotRecord]:
        """
        查询主机快照记录
        """

        records = self._query_namespace(
            namespace=HOST_SNAPSHOTS_NAMESPACE,
            filters=[
                indexed_gte("created_at", query.created_from),
                indexed_lte("created_at", query.created_to),
            ],
            sorts=[
                indexed_sort("created_at", SortDirection.DESC),
            ],
            page=build_page(query.offset, query.limit),
        )
        return self._decode_records(records, HostSnapshotRecord)

    def latest_system_snapshot(self) -> SystemSnapshotRecord | None:
        """
        返回最近一条系统快照
        """

        records = self._query_namespace(
            namespace=SYSTEM_SNAPSHOTS_NAMESPACE,
            filters=[],
            sorts=[
                indexed_sort("created_at", SortDirection.DESC),
            ],
            page=PageRequest(offset=0, limit=1),
        )
        decoded = self._decode_records(records, SystemSnapshotRecord)
        return decoded[0] if decoded else None

    def latest_host_snapshot(self) -> HostSnapshotRecord | None:
        """
        返回最近一条主机快照
        """

        records = self._query_namespace(
            namespace=HOST_SNAPSHOTS_NAMESPACE,
            filters=[],
            sorts=[
                indexed_sort("created_at", SortDirection.DESC),
            ],
            page=PageRequest(offset=0, limit=1),
        )
        decoded = self._decode_records(records, HostSnapshotRecord)
        return decoded[0] if decoded else None

    def _query_namespace(
        self,
        *,
        namespace: str,
        filters: list,
        sorts: list,
        page: PageRequest | None,
    ) -> list[PersistenceRecord]:
        """
        执行一次 monitor 到 persistence 的查询翻译
        """

        request = QueryRequest(
            namespace=namespace,
            filters=[item for item in filters if item is not None],
            sorts=[item for item in sorts if item is not None],
            page=page,
        )

        try:
            result = self._persistence.query(request)
        except Exception as exc:
            raise MonitorQueryError(f"monitor 查询失败: namespace={namespace}") from exc

        return result.items

    def _decode_records(
        self,
        records: list[PersistenceRecord],
        model_type: type[_RecordModelT],
    ) -> list[_RecordModelT]:
        """
        将 persistence 记录列表还原为 monitor 领域记录列表
        """

        decoded: list[_RecordModelT] = []

        for record in records:
            try:
                decoded.append(model_type.model_validate(record.payload))
            except Exception as exc:
                raise MonitorQueryError(
                    f"monitor 记录反序列化失败: namespace={record.namespace}, record_id={record.record_id}"
                ) from exc

        return decoded


__all__ = ["MonitorService"]
