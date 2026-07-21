from __future__ import annotations

from datetime import datetime

from pydantic import Field

from analyzing.contracts.model import AnalyzingModel
from analyzing.monitor.records import ExecutionStatus
from analyzing.plugin.enums.plugin import (
    InstallStatus,
    InvocationStatus,
    PluginEventType,
    RuntimeStatus,
)


class ListQuery(AnalyzingModel):
    """
    列表查询基类
    """

    # 分页偏移量
    offset: int = Field(default=0, ge=0)

    # 分页数量限制
    limit: int = Field(default=50, ge=1)


class PluginEventQuery(ListQuery):
    """
    插件事件查询条件
    """

    # 插件唯一标识
    plugin_id: str | None = None

    # 事件类型
    event_type: PluginEventType | None = None

    # 开始时间
    created_from: datetime | None = None

    # 结束时间
    created_to: datetime | None = None


class PluginInvocationQuery(ListQuery):
    """
    插件调用查询条件
    """

    # 所属执行唯一标识
    execution_id: str | None = None

    # 插件唯一标识
    plugin_id: str | None = None

    # 调用状态
    status: InvocationStatus | None = None

    # 插件运行模式
    runtime_mode: str | None = None

    # 开始时间
    started_from: datetime | None = None

    # 结束时间
    started_to: datetime | None = None


class PluginStatusQuery(ListQuery):
    """
    插件状态查询条件
    """

    # 插件唯一标识
    plugin_id: str | None = None

    # 安装状态
    install_status: InstallStatus | None = None

    # 运行状态
    runtime_status: RuntimeStatus | None = None


class ExecutionQuery(ListQuery):
    """
    执行记录查询条件
    """

    # 链路追踪标识
    trace_id: str | None = None

    # 执行状态
    status: ExecutionStatus | None = None

    # 开始时间
    started_from: datetime | None = None

    # 结束时间
    started_to: datetime | None = None


class AccessLogQuery(ListQuery):
    """
    API 访问日志查询条件
    """

    # 请求方法
    method: str | None = None

    # 请求路径
    path: str | None = None

    # 响应状态码
    status_code: int | None = None

    # 客户端 IP
    client_ip: str | None = None

    # 链路追踪标识
    trace_id: str | None = None

    # 开始时间
    created_from: datetime | None = None

    # 结束时间
    created_to: datetime | None = None


class SystemSnapshotQuery(ListQuery):
    """
    系统快照查询条件
    """

    # 开始时间
    created_from: datetime | None = None

    # 结束时间
    created_to: datetime | None = None


class HostSnapshotQuery(ListQuery):
    """
    主机快照查询条件
    """

    # 开始时间
    created_from: datetime | None = None

    # 结束时间
    created_to: datetime | None = None


__all__ = [
    "ExecutionQuery",
    "HostSnapshotQuery",
    "AccessLogQuery",
    "PluginEventQuery",
    "PluginInvocationQuery",
    "PluginStatusQuery",
    "SystemSnapshotQuery",
]
