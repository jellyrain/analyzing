from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urljoin
from uuid import uuid4

import httpx
from analyzing.plugin.errors import PluginInvokeError, PluginLoadError
from analyzing.plugin.manifest import PluginManifest
from analyzing.plugin.remote import PluginInvokeRequest, PluginInvokeResponse
from analyzing.runtime.config import RemoteExposeSpec

from src.utils.time import get_curr_time


def _utcnow() -> datetime:
    """
    统一生成带时区的时间，避免租约比较时混入 naive datetime
    """

    return get_curr_time()


@dataclass(slots=True)
class RemotePluginHandle:
    """
    引擎内维护的 remote 插件句柄
    """

    # 插件 ID
    plugin_id: str

    # 远程实例 ID
    instance_id: str

    # 宿主分配的会话 ID
    session_id: str

    # 插件 manifest
    manifest: PluginManifest

    # 远程实例暴露的服务信息
    endpoint: RemoteExposeSpec

    # 插件侧当前使用的 SDK 版本
    sdk_version: str

    # 当前租约 TTL，单位秒
    lease_ttl_seconds: int

    # 调用超时时间，单位秒
    invoke_timeout_seconds: int

    # 注册时间
    registered_at: datetime = field(default_factory=_utcnow)

    # 最近一次心跳时间
    last_heartbeat_at: datetime = field(default_factory=_utcnow)

    # 租约到期时间
    lease_expires_at: datetime = field(default_factory=_utcnow)

    # 复用的 HTTP client，便于单测注入假对象
    client: Any = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self.refresh_lease(self.lease_ttl_seconds)

    def refresh_lease(self, lease_ttl_seconds: int | None = None) -> None:
        """
        刷新当前会话租约
        """

        ttl = lease_ttl_seconds or self.lease_ttl_seconds
        now = _utcnow()

        self.lease_ttl_seconds = ttl
        self.last_heartbeat_at = now
        self.lease_expires_at = now + timedelta(seconds=ttl)

    def is_alive(self) -> bool:
        """
        当前 remote 会话是否仍在租约期内
        """

        return _utcnow() < self.lease_expires_at

    def invoke(self, request: PluginInvokeRequest) -> PluginInvokeResponse:
        """
        通过 HTTP 调用 remote 插件实例
        """

        if not self.is_alive():
            raise PluginInvokeError(
                f"remote 插件租约已过期，无法调用: {self.plugin_id}"
            )

        client = self._ensure_client()

        try:
            response = client.post(
                self._build_invoke_url(),
                json=request.model_dump(mode="json"),
                headers=self._build_headers(),
            )
        except Exception as exc:
            raise PluginInvokeError(
                f"remote 插件调用失败: {self.plugin_id}, endpoint={self.endpoint.base_url}"
            ) from exc

        if response.status_code >= 400:
            raise PluginInvokeError(
                "remote 插件返回错误状态码: "
                f"{self.plugin_id}, status_code={response.status_code}, body={response.text}"
            )

        try:
            return PluginInvokeResponse.model_validate_json(response.text)
        except Exception as exc:
            raise PluginInvokeError(
                f"remote 插件响应无法解析: {self.plugin_id}, endpoint={self.endpoint.base_url}"
            ) from exc

    def close(self) -> None:
        """
        关闭底层 HTTP client
        """

        close = getattr(self.client, "close", None)
        if callable(close):
            close()

    def _ensure_client(self) -> Any:
        """
        惰性创建 HTTP client
        """

        if self.client is None:
            self.client = httpx.Client(timeout=self.invoke_timeout_seconds)

        return self.client

    def _build_invoke_url(self) -> str:
        return urljoin(
            f"{self.endpoint.base_url.rstrip('/')}/",
            self.endpoint.invoke_path.lstrip("/"),
        )

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        headers.update(self.endpoint.headers)
        return headers


@dataclass(slots=True)
class RemoteSessionRegistry:
    """
    保存 remote 插件会话索引
    """

    # 按 session_id 建立的会话索引
    sessions_by_id: dict[str, RemotePluginHandle] = field(default_factory=dict)

    # 按 plugin_id 建立的活跃会话索引
    session_ids_by_plugin_id: dict[str, str] = field(default_factory=dict)

    def add(self, handle: RemotePluginHandle) -> RemotePluginHandle | None:
        """
        注册或替换某个 plugin_id 当前活跃的 remote 会话
        """

        previous = self.get_by_plugin_id(handle.plugin_id)
        if previous is not None:
            self.remove_session(previous.session_id)

        self.sessions_by_id[handle.session_id] = handle
        self.session_ids_by_plugin_id[handle.plugin_id] = handle.session_id
        return previous

    def get_by_session_id(self, session_id: str) -> RemotePluginHandle | None:
        """
        按 session_id 获取会话
        """

        return self.sessions_by_id.get(session_id)

    def get_by_plugin_id(self, plugin_id: str) -> RemotePluginHandle | None:
        """
        按 plugin_id 获取当前活跃会话
        """

        session_id = self.session_ids_by_plugin_id.get(plugin_id)
        if session_id is None:
            return None

        return self.sessions_by_id.get(session_id)

    def remove_session(self, session_id: str) -> RemotePluginHandle | None:
        """
        删除一个会话索引
        """

        handle = self.sessions_by_id.pop(session_id, None)
        if handle is None:
            return None

        current_session_id = self.session_ids_by_plugin_id.get(handle.plugin_id)
        if current_session_id == session_id:
            self.session_ids_by_plugin_id.pop(handle.plugin_id, None)

        return handle


def build_remote_plugin_handle(
    *,
    manifest: PluginManifest,
    instance_id: str,
    endpoint: RemoteExposeSpec,
    sdk_version: str,
    lease_ttl_seconds: int,
    invoke_timeout_seconds: int,
) -> RemotePluginHandle:
    """
    基于注册请求构造 remote 插件句柄
    """

    if manifest.runtime is None:
        raise PluginLoadError("remote 插件缺少 runtime 配置")

    return RemotePluginHandle(
        plugin_id=manifest.plugin_id,
        instance_id=instance_id,
        session_id=str(uuid4()),
        manifest=manifest,
        endpoint=endpoint,
        sdk_version=sdk_version,
        lease_ttl_seconds=lease_ttl_seconds,
        invoke_timeout_seconds=invoke_timeout_seconds,
    )


__all__ = [
    "RemotePluginHandle",
    "RemoteSessionRegistry",
    "build_remote_plugin_handle",
]
