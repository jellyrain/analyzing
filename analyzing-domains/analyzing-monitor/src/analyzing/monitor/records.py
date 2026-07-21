from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field

from analyzing.contracts.model import AnalyzingModel
from analyzing.plugin.enums.plugin import (
    InstallStatus,
    InvocationStatus,
    PluginEventType,
    RuntimeStatus,
)


class ExecutionStatus(StrEnum):
    """
    执行状态
    """

    # 已创建
    CREATED = "created"

    # 执行中
    RUNNING = "running"

    # 执行成功
    SUCCEEDED = "succeeded"

    # 执行失败
    FAILED = "failed"

    # 执行超时
    TIMEOUT = "timeout"

    # 已取消
    CANCELLED = "cancelled"


class PluginEventRecord(AnalyzingModel):
    """
    插件事件记录
    """

    # 事件唯一标识
    event_id: str

    # 插件唯一标识
    plugin_id: str

    # 插件版本
    version: str | None = None

    # 事件类型
    event_type: PluginEventType

    # 事件消息
    message: str

    # 事件附加详情
    detail: dict[str, Any] = Field(default_factory=dict)

    # 事件创建时间
    created_at: datetime


class PluginInvocationRecord(AnalyzingModel):
    """
    插件调用记录
    """

    # 调用唯一标识
    invocation_id: str

    # 所属执行唯一标识
    execution_id: str

    # 插件唯一标识
    plugin_id: str

    # 插件版本
    version: str | None = None

    # 插件运行模式
    runtime_mode: Literal["inproc", "subprocess", "remote"]

    # 调用状态
    status: InvocationStatus

    # 调用开始时间
    started_at: datetime

    # 调用结束时间
    finished_at: datetime | None = None

    # 调用耗时，单位毫秒
    latency_ms: int | None = None

    # 输入大小
    input_size: int | None = None

    # 输出数量
    output_count: int | None = None

    # 错误信息
    error_message: str | None = None

    # 运行附加详情
    detail: dict[str, Any] = Field(default_factory=dict)


class PluginStatusRecord(AnalyzingModel):
    """
    插件当前状态记录

    这类记录更偏“当前状态快照”，适合用 upsert 维护。
    """

    # 插件唯一标识
    plugin_id: str

    # 插件版本
    version: str | None = None

    # 安装状态
    install_status: InstallStatus

    # 运行状态
    runtime_status: RuntimeStatus

    # 最近更新时间
    updated_at: datetime

    # 状态附加详情
    detail: dict[str, Any] = Field(default_factory=dict)


class AccessLogRecord(AnalyzingModel):
    """
    API 访问日志记录
    """

    # 访问日志唯一标识
    access_id: str

    # 链路追踪标识
    trace_id: str | None = None

    # 请求方法
    method: str

    # 请求路径
    path: str

    # 响应状态码
    status_code: int

    # 请求体大小
    request_size: int | None = None

    # 响应体大小
    response_size: int | None = None

    # 请求耗时，单位毫秒
    latency_ms: int | None = None

    # 客户端 IP
    client_ip: str | None = None

    # 访问附加详情
    detail: dict[str, Any] = Field(default_factory=dict)

    # 访问创建时间
    created_at: datetime


class ExecutionRecord(AnalyzingModel):
    """
    宿主执行记录
    """

    # 执行唯一标识
    execution_id: str

    # 链路追踪标识
    trace_id: str

    # 执行状态
    status: ExecutionStatus

    # 输入大小
    input_size: int | None = None

    # 输出数量
    output_count: int | None = None

    # 总耗时，单位毫秒
    latency_ms: int | None = None

    # 错误信息
    error_message: str | None = None

    # 执行开始时间
    started_at: datetime

    # 执行结束时间
    finished_at: datetime | None = None

    # 执行附加详情
    detail: dict[str, Any] = Field(default_factory=dict)


class SystemSnapshotRecord(AnalyzingModel):
    """
    系统运行快照
    """

    # 快照唯一标识
    snapshot_id: str

    # 当前已注册插件数量
    plugin_count: int | None = None

    # 当前可用插件数量
    ready_plugin_count: int | None = None

    # 当前异常插件数量
    error_plugin_count: int | None = None

    # 当前运行中的执行数量
    running_execution_count: int | None = None

    # 快照附加详情
    detail: dict[str, Any] = Field(default_factory=dict)

    # 快照创建时间
    created_at: datetime


class HostSnapshotRecord(AnalyzingModel):
    """
    当前机器快照
    """

    # 快照唯一标识
    snapshot_id: str

    # CPU 使用率
    cpu_percent: float | None = None

    # 内存使用率
    memory_percent: float | None = None

    # 磁盘使用率
    disk_percent: float | None = None

    # 机器附加详情
    detail: dict[str, Any] = Field(default_factory=dict)

    # 快照创建时间
    created_at: datetime


__all__ = [
    "ExecutionRecord",
    "ExecutionStatus",
    "AccessLogRecord",
    "HostSnapshotRecord",
    "PluginEventRecord",
    "PluginInvocationRecord",
    "PluginStatusRecord",
    "SystemSnapshotRecord",
]
