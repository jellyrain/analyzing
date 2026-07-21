from __future__ import annotations

from typing import Any

from pydantic import Field
from analyzing.runtime.config import RemoteExposeSpec
from analyzing.contracts.model import AnalyzingModel

from analyzing.plugin.manifest import PluginManifest
from analyzing.plugin.result import AllPluginResultPayload, PluginExecutionOutput


class PluginInvokeRequest(AnalyzingModel):
    """
    通用插件调用请求
    """

    # 请求链路追踪 ID
    trace_id: str | None = None

    # 目标插件 ID
    plugin_id: str

    # 调用操作名，例如 parse 或 split
    operation: str

    # 调用载荷
    payload: dict[str, Any] = Field(default_factory=dict)


class PluginInvokeResponse(AnalyzingModel):
    """
    通用插件调用响应
    """

    # 是否调用成功
    ok: bool = True

    # 插件自己的原始输出
    raw_output: list[dict[str, Any]] | dict[str, Any] = Field(default_factory=list)

    # 兼容 pipeline 的统一输出
    pipeline_result: AllPluginResultPayload = None

    # 失败时的错误码
    error_code: str | None = None

    # 失败时的错误信息
    error_message: str | None = None

    @classmethod
    def success(
        cls,
        output: PluginExecutionOutput,
    ) -> PluginInvokeResponse:

        return cls(
            ok=True,
            raw_output=output.raw_output,
            pipeline_result=output.pipeline_result,
        )


class RemoteRegisterRequest(AnalyzingModel):
    """
    remote 插件注册请求
    """

    # 插件 manifest
    manifest: PluginManifest

    # 当前远程实例 ID
    instance_id: str

    # 当前实例对外暴露的服务信息
    endpoint: RemoteExposeSpec

    # 当前实例使用的 SDK 版本
    sdk_version: str


class RemoteRegisterResponse(AnalyzingModel):
    """
    remote 插件注册响应
    """

    # 是否接受本次注册
    accepted: bool = True

    # 宿主分配的会话 ID
    session_id: str | None = None

    # 本次租约有效期，单位秒
    lease_ttl_seconds: int = 45

    # 附加说明消息
    message: str = ""


class RemoteHeartbeatRequest(AnalyzingModel):
    """
    remote 插件心跳请求
    """

    # 注册成功后宿主返回的会话 ID
    session_id: str

    # 当前远程实例 ID
    instance_id: str


class RemoteHeartbeatResponse(AnalyzingModel):
    """
    remote 插件心跳响应
    """

    # 是否接受本次续租
    accepted: bool = True

    # 更新后的租约有效期，单位秒
    lease_ttl_seconds: int = 45

    # 附加说明消息
    message: str = ""


class RemoteUnregisterRequest(AnalyzingModel):
    """
    remote 插件注销请求
    """

    # 注册成功后宿主返回的会话 ID
    session_id: str

    # 当前远程实例 ID
    instance_id: str

    # 注销原因
    reason: str = "shutdown"


class RemoteHealthcheckResponse(AnalyzingModel):
    """
    remote 插件健康检查响应
    """

    # 当前实例是否健康
    ok: bool = True

    # 健康状态说明
    message: str = ""


__all__ = [
    "PluginInvokeRequest",
    "PluginInvokeResponse",
    "RemoteRegisterRequest",
    "RemoteRegisterResponse",
    "RemoteHeartbeatRequest",
    "RemoteHeartbeatResponse",
    "RemoteUnregisterRequest",
    "RemoteHealthcheckResponse",
]
