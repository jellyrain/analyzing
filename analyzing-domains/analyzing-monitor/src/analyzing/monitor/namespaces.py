# 插件生命周期事件命名空间
PLUGIN_EVENTS_NAMESPACE = "monitor.plugin_events"

# 插件调用记录命名空间
PLUGIN_INVOCATIONS_NAMESPACE = "monitor.plugin_invocations"

# 插件当前状态快照命名空间
PLUGIN_STATUS_NAMESPACE = "monitor.plugin_status"

# API 访问日志命名空间
ACCESS_LOGS_NAMESPACE = "monitor.access_logs"

# 宿主执行记录命名空间
EXECUTIONS_NAMESPACE = "monitor.executions"

# 系统运行快照命名空间
SYSTEM_SNAPSHOTS_NAMESPACE = "monitor.system_snapshots"

# 当前机器快照命名空间
HOST_SNAPSHOTS_NAMESPACE = "monitor.host_snapshots"


__all__ = [
    "EXECUTIONS_NAMESPACE",
    "HOST_SNAPSHOTS_NAMESPACE",
    "PLUGIN_EVENTS_NAMESPACE",
    "PLUGIN_INVOCATIONS_NAMESPACE",
    "PLUGIN_STATUS_NAMESPACE",
    "ACCESS_LOGS_NAMESPACE",
    "SYSTEM_SNAPSHOTS_NAMESPACE",
]
