from analyzing.monitor.namespaces import (
    EXECUTIONS_NAMESPACE,
    HOST_SNAPSHOTS_NAMESPACE,
    PLUGIN_EVENTS_NAMESPACE,
    PLUGIN_INVOCATIONS_NAMESPACE,
    PLUGIN_STATUS_NAMESPACE,
    SYSTEM_SNAPSHOTS_NAMESPACE,
    ACCESS_LOGS_NAMESPACE,
)
from analyzing.persistence.schema import (
    IndexedField,
    NamespaceSchema,
    SchemaIndex,
    StorageFieldType,
)

PLUGIN_EVENTS_SCHEMA = NamespaceSchema(
    namespace=PLUGIN_EVENTS_NAMESPACE,
    target_name="monitor_plugin_events",
    description="插件事件记录",
    indexed_fields=[
        # 插件唯一标识，便于按插件查询事件
        IndexedField(name="plugin_id", field_type=StorageFieldType.STRING),
        # 事件类型，便于按事件类型筛选
        IndexedField(name="event_type", field_type=StorageFieldType.STRING),
        # 事件时间，便于按时间范围查询
        IndexedField(name="created_at", field_type=StorageFieldType.DATETIME),
    ],
    indexes=[
        SchemaIndex(fields=["plugin_id"]),
        SchemaIndex(fields=["event_type", "created_at"]),
    ],
)

PLUGIN_INVOCATIONS_SCHEMA = NamespaceSchema(
    namespace=PLUGIN_INVOCATIONS_NAMESPACE,
    target_name="monitor_plugin_invocations",
    description="插件调用记录",
    indexed_fields=[
        # 所属执行唯一标识
        IndexedField(name="execution_id", field_type=StorageFieldType.STRING),
        # 插件唯一标识
        IndexedField(name="plugin_id", field_type=StorageFieldType.STRING),
        # 插件运行模式
        IndexedField(name="runtime_mode", field_type=StorageFieldType.STRING),
        # 调用状态
        IndexedField(name="status", field_type=StorageFieldType.STRING),
        # 调用开始时间
        IndexedField(name="started_at", field_type=StorageFieldType.DATETIME),
    ],
    indexes=[
        SchemaIndex(fields=["execution_id"]),
        SchemaIndex(fields=["plugin_id", "started_at"]),
        SchemaIndex(fields=["status", "started_at"]),
    ],
)

PLUGIN_STATUS_SCHEMA = NamespaceSchema(
    namespace=PLUGIN_STATUS_NAMESPACE,
    target_name="monitor_plugin_status",
    description="插件当前状态记录",
    indexed_fields=[
        # 插件唯一标识
        IndexedField(
            name="plugin_id", field_type=StorageFieldType.STRING, required=True
        ),
        # 安装状态
        IndexedField(name="install_status", field_type=StorageFieldType.STRING),
        # 运行状态
        IndexedField(name="runtime_status", field_type=StorageFieldType.STRING),
        # 状态更新时间
        IndexedField(name="updated_at", field_type=StorageFieldType.DATETIME),
    ],
    indexes=[
        SchemaIndex(fields=["plugin_id"], unique=True),
        SchemaIndex(fields=["runtime_status"]),
    ],
)

ACCESS_LOGS_SCHEMA = NamespaceSchema(
    namespace=ACCESS_LOGS_NAMESPACE,
    target_name="monitor_access_logs",
    description="API 访问日志记录",
    indexed_fields=[
        # 请求方法
        IndexedField(name="method", field_type=StorageFieldType.STRING),
        # 请求路径
        IndexedField(name="path", field_type=StorageFieldType.STRING),
        # 响应状态码
        IndexedField(name="status_code", field_type=StorageFieldType.INTEGER),
        # 客户端 IP
        IndexedField(name="client_ip", field_type=StorageFieldType.STRING),
        # 链路追踪标识
        IndexedField(name="trace_id", field_type=StorageFieldType.STRING),
        # 访问时间
        IndexedField(name="created_at", field_type=StorageFieldType.DATETIME),
    ],
    indexes=[
        SchemaIndex(fields=["method", "created_at"]),
        SchemaIndex(fields=["path", "created_at"]),
        SchemaIndex(fields=["status_code", "created_at"]),
        SchemaIndex(fields=["client_ip", "created_at"]),
        SchemaIndex(fields=["trace_id"]),
    ],
)

EXECUTIONS_SCHEMA = NamespaceSchema(
    namespace=EXECUTIONS_NAMESPACE,
    target_name="monitor_executions",
    description="宿主执行记录",
    indexed_fields=[
        # 链路追踪标识
        IndexedField(name="trace_id", field_type=StorageFieldType.STRING),
        # 执行状态
        IndexedField(name="status", field_type=StorageFieldType.STRING),
        # 执行开始时间
        IndexedField(name="started_at", field_type=StorageFieldType.DATETIME),
    ],
    indexes=[
        SchemaIndex(fields=["trace_id"]),
        SchemaIndex(fields=["status", "started_at"]),
    ],
)

SYSTEM_SNAPSHOTS_SCHEMA = NamespaceSchema(
    namespace=SYSTEM_SNAPSHOTS_NAMESPACE,
    target_name="monitor_system_snapshots",
    description="系统运行快照",
    indexed_fields=[
        # 快照时间
        IndexedField(name="created_at", field_type=StorageFieldType.DATETIME),
        # 当前已注册插件数量
        IndexedField(name="plugin_count", field_type=StorageFieldType.INTEGER),
        # 当前可用插件数量
        IndexedField(name="ready_plugin_count", field_type=StorageFieldType.INTEGER),
        # 当前异常插件数量
        IndexedField(name="error_plugin_count", field_type=StorageFieldType.INTEGER),
        # 当前运行中的执行数量
        IndexedField(
            name="running_execution_count", field_type=StorageFieldType.INTEGER
        ),
    ],
    indexes=[
        SchemaIndex(fields=["created_at"]),
    ],
)

HOST_SNAPSHOTS_SCHEMA = NamespaceSchema(
    namespace=HOST_SNAPSHOTS_NAMESPACE,
    target_name="monitor_host_snapshots",
    description="主机运行快照",
    indexed_fields=[
        # 快照时间
        IndexedField(name="created_at", field_type=StorageFieldType.DATETIME),
        # CPU 使用率
        IndexedField(name="cpu_percent", field_type=StorageFieldType.FLOAT),
        # 内存使用率
        IndexedField(name="memory_percent", field_type=StorageFieldType.FLOAT),
        # 磁盘使用率
        IndexedField(name="disk_percent", field_type=StorageFieldType.FLOAT),
    ],
    indexes=[
        SchemaIndex(fields=["created_at"]),
        SchemaIndex(fields=["cpu_percent"]),
        SchemaIndex(fields=["memory_percent"]),
        SchemaIndex(fields=["disk_percent"]),
    ],
)

MONITOR_SCHEMAS = [
    PLUGIN_EVENTS_SCHEMA,
    PLUGIN_INVOCATIONS_SCHEMA,
    PLUGIN_STATUS_SCHEMA,
    ACCESS_LOGS_SCHEMA,
    EXECUTIONS_SCHEMA,
    SYSTEM_SNAPSHOTS_SCHEMA,
    HOST_SNAPSHOTS_SCHEMA,
]

__all__ = [
    "EXECUTIONS_SCHEMA",
    "HOST_SNAPSHOTS_SCHEMA",
    "MONITOR_SCHEMAS",
    "ACCESS_LOGS_SCHEMA",
    "PLUGIN_EVENTS_SCHEMA",
    "PLUGIN_INVOCATIONS_SCHEMA",
    "PLUGIN_STATUS_SCHEMA",
    "SYSTEM_SNAPSHOTS_SCHEMA",
]
