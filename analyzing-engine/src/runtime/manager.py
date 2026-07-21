from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from threading import Lock, RLock
from typing import Any, TypeVar
from uuid import uuid4

from analyzing.compat.host import HostProfile
from analyzing.contracts.model import AnalyzingModel
from analyzing.monitor.records import (
    PluginEventRecord,
    PluginInvocationRecord,
    PluginStatusRecord,
)
from analyzing.monitor.tracker import MonitorTracker
from analyzing.plugin.base import AbstractPlugin
from analyzing.plugin.enums.plugin import InstallStatus, RuntimeStatus
from analyzing.plugin.enums.plugin import InvocationStatus, PluginEventType
from analyzing.plugin.errors import PluginLoadError, PluginInvokeError
from analyzing.plugin.manifest import PluginManifest
from analyzing.plugin.parser import ParserPlugin
from analyzing.plugin.remote import (
    PluginInvokeResponse,
    PluginInvokeRequest,
    RemoteRegisterRequest,
    RemoteRegisterResponse,
    RemoteHeartbeatRequest,
    RemoteHeartbeatResponse,
    RemoteUnregisterRequest,
)
from analyzing.plugin.result import (
    PluginExecutionOutput,
    ParserPluginResultPayload,
    SplitterPluginResultPayload,
)
from analyzing.plugin.splitter import SplitterPlugin
from analyzing.runtime.config import RemoteRuntimeConfig
from analyzing.runtime.mode import RuntimeMode

from src.app.enums import PluginLoadStrategy
from src.registry.schemas import PluginCatalog, PluginCatalogEntry
from src.registry.manifest import validate_manifest
from src.runtime.inproc import load_inproc_plugin
from src.runtime.subproc import load_subprocess_plugin
from src.runtime.remote import RemoteSessionRegistry, build_remote_plugin_handle
from src.utils.time import get_curr_time

T = TypeVar("T", bound=AnalyzingModel)


def _enum_value(raw: object) -> object:
    """
    兼容枚举对象或已经序列化后的枚举值。
    """

    return getattr(raw, "value", raw)


def _estimate_payload_size(payload: dict[str, Any]) -> int | None:
    """
    估算本次插件调用输入大小。
    """

    try:
        return len(json.dumps(payload, ensure_ascii=False, default=str))
    except Exception:
        return None


def _estimate_output_count(response: PluginInvokeResponse) -> int | None:
    """
    估算本次插件调用输出数量。
    """

    pipeline_result = response.pipeline_result

    if isinstance(pipeline_result, ParserPluginResultPayload):
        return sum(
            len(item)
            for item in pipeline_result.pipeline_output.values()
            if isinstance(item, list)
        )

    if isinstance(pipeline_result, SplitterPluginResultPayload):
        return len(pipeline_result.pipeline_output)

    return None


def _load_entry(entry: PluginCatalogEntry) -> Any:
    """
    根据登记项实际执行加载
    """

    manifest = entry.manifest
    if manifest is None:
        raise PluginLoadError("插件 manifest 不存在")

    if manifest.runtime_mode == RuntimeMode.INPROC:
        return load_inproc_plugin(entry)

    if manifest.runtime_mode == RuntimeMode.SUBPROCESS:
        return load_subprocess_plugin(entry)

    if manifest.runtime_mode == RuntimeMode.REMOTE:
        raise PluginLoadError(
            f"remote 插件不能通过本地加载流程获取实例，请远程注册: {manifest.plugin_id}"
        )

    raise PluginLoadError(
        f"当前版本尚未实现该运行模式的插件加载: {manifest.runtime_mode}"
    )


def _is_plugin_available(plugin: Any) -> bool:
    """
    判断已缓存插件当前是否仍可用
    """

    is_alive = getattr(plugin, "is_alive", None)
    if callable(is_alive):
        return bool(is_alive())

    return True


def _close_plugin(plugin: Any) -> None:
    """
    关闭已加载插件持有的运行时资源
    """

    close = getattr(plugin, "close", None)
    if callable(close):
        close()


def _build_error_response(
    *,
    error_code: str,
    error_message: str,
) -> PluginInvokeResponse:
    """
    构造统一错误响应
    """

    return PluginInvokeResponse(
        ok=False,
        error_code=error_code,
        error_message=error_message,
    )


def _normalize_local_params(
    plugin: AbstractPlugin,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    规范化 inproc 插件调用参数
    """

    raw_params = payload.get("params", {})
    if not isinstance(raw_params, dict):
        raise PluginInvokeError("payload.params 必须是对象类型")

    normalized_params = plugin.validate_params(raw_params)
    if not isinstance(normalized_params, dict):
        raise PluginInvokeError("plugin.validate_params 必须返回 dict")

    return normalized_params


def _require_text_payload(payload: dict[str, Any]) -> str:
    """
    提取文本输入
    """

    text = payload.get("text")
    if not isinstance(text, str):
        raise PluginInvokeError("payload.text 必须是字符串")

    return text


def _require_plugin_output(raw_output: object) -> PluginExecutionOutput:
    """
    要求本地插件必须返回标准输出对象
    """

    if not isinstance(raw_output, PluginExecutionOutput):
        raise PluginInvokeError(
            "本地插件必须返回 PluginExecutionOutput，当前返回值不符合 SDK 契约"
        )

    return raw_output


def _require_remote_runtime_config(
    manifest: PluginManifest,
) -> RemoteRuntimeConfig:
    """
    要求 manifest.runtime 必须是 remote 配置
    """

    runtime_config = manifest.runtime
    if not isinstance(runtime_config, RemoteRuntimeConfig):
        raise PluginLoadError("插件 runtime 配置不是 remote，无法按 remote 方式处理")

    return runtime_config


def _extract_bearer_token(authorization: str | None) -> str | None:
    """
    从 Authorization 头中提取 Bearer token
    """

    if not authorization:
        return None

    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return None

    token = authorization[len(prefix) :].strip()
    return token or None


def _build_remote_catalog_entry(
    manifest: PluginManifest,
    runtime_plugins_dir_path: Path | None,
) -> PluginCatalogEntry:
    """
    为动态注册的 remote 插件构造登记项
    """

    if runtime_plugins_dir_path is not None:
        plugin_dir_path = runtime_plugins_dir_path / ".remote" / manifest.plugin_id
    else:
        plugin_dir_path = Path(".remote") / manifest.plugin_id

    return PluginCatalogEntry(
        plugin_dir_path=plugin_dir_path,
        manifest_file_path=None,
        manifest=manifest,
        load_strategy=PluginLoadStrategy.LAZY,
        is_compatible=True,
        install_status=InstallStatus.INSTALLED,
        runtime_status=RuntimeStatus.REGISTERED,
    )


def _assert_remote_manifest_matches(
    expected_manifest: PluginManifest,
    actual_manifest: PluginManifest,
) -> None:
    """
    预声明 remote 插件注册时，只校验关键身份字段是否一致
    """

    for field_name in (
        "plugin_id",
        "plugin_role",
        "plugin_type",
        "runtime_mode",
    ):
        expected_value = getattr(expected_manifest, field_name)
        actual_value = getattr(actual_manifest, field_name)
        if expected_value != actual_value:
            raise PluginLoadError(
                f"remote 注册 manifest 字段不匹配: {field_name}, "
                f"expected={expected_value!r}, actual={actual_value!r}"
            )


def _require_parser_pipeline_output(
    response: PluginInvokeResponse,
) -> dict[str, list[Any]]:
    """
    从插件响应中提取 parser 的 pipeline_output。
    """

    pipeline_result = response.pipeline_result
    if not isinstance(pipeline_result, ParserPluginResultPayload):
        raise PluginInvokeError("解析器插件返回的 pipeline_result 类型不正确")

    pipeline_output = pipeline_result.pipeline_output
    if not isinstance(pipeline_output, dict):
        raise PluginInvokeError("解析器插件返回的 pipeline_output 不是对象")

    normalized: dict[str, list[Any]] = {}
    for key, value in pipeline_output.items():
        if not isinstance(key, str):
            raise PluginInvokeError("解析器插件返回的 pipeline_output key 必须是字符串")
        if not isinstance(value, list):
            raise PluginInvokeError(
                f"解析器插件返回的 pipeline_output[{key!r}] 不是列表"
            )
        normalized[key] = value

    return normalized


def _require_splitter_pipeline_output(
    response: PluginInvokeResponse,
) -> list[str]:
    """
    从插件响应中提取 splitter 的 pipeline_output。
    """

    pipeline_result = response.pipeline_result
    if not isinstance(pipeline_result, SplitterPluginResultPayload):
        raise PluginInvokeError("拆分器插件返回的 pipeline_result 类型不正确")

    pipeline_output = pipeline_result.pipeline_output
    if not isinstance(pipeline_output, list):
        raise PluginInvokeError("拆分器插件返回的 pipeline_output 不是列表")

    normalized: list[str] = []
    for index, item in enumerate(pipeline_output):
        if not isinstance(item, str):
            raise PluginInvokeError(
                f"拆分器插件返回的 pipeline_output[{index}] 不是字符串"
            )
        normalized.append(item)

    return normalized


def _invoke_local_plugin(
    plugin: Any,
    request: PluginInvokeRequest,
) -> PluginInvokeResponse:
    """
    调用 inproc 本地插件
    """

    if not isinstance(plugin, AbstractPlugin):
        raise PluginInvokeError("当前本地插件实例不符合 AbstractPlugin 约束")

    normalized_params = _normalize_local_params(plugin, request.payload)

    if request.operation == "parse":
        if not isinstance(plugin, ParserPlugin):
            return _build_error_response(
                error_code="unsupported_operation",
                error_message="当前插件不支持 parse 操作",
            )

        plugin_output = _require_plugin_output(
            plugin.parse(
                text=_require_text_payload(request.payload),
                params=normalized_params,
            )
        )
        return PluginInvokeResponse.success(plugin_output)

    if request.operation == "split":
        if not isinstance(plugin, SplitterPlugin):
            return _build_error_response(
                error_code="unsupported_operation",
                error_message="当前插件不支持 split 操作",
            )

        plugin_output = _require_plugin_output(
            plugin.split(
                text=_require_text_payload(request.payload),
                params=normalized_params,
            )
        )
        return PluginInvokeResponse.success(plugin_output)

    return _build_error_response(
        error_code="unsupported_operation",
        error_message=f"不支持的插件操作: {request.operation}",
    )


@dataclass(slots=True)
class EngineRuntimeManager:
    """
    引擎插件运行时管理器
    """

    # 引擎插件注册表
    plugin_catalog: PluginCatalog

    # 当前已加载的插件实例
    loaded_plugins_by_id: dict[str, Any] = field(default_factory=dict)

    # 每个 subprocess 插件独占一把锁，保证一组 stdin/stdout 请求响应不会交叉。
    _subprocess_locks_by_id: dict[str, RLock] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    # 保护锁字典本身的创建过程。
    _subprocess_locks_guard: Lock = field(
        default_factory=Lock,
        init=False,
        repr=False,
    )

    # 当前活跃的 remote 会话索引
    remote_registry: RemoteSessionRegistry = field(
        default_factory=RemoteSessionRegistry
    )

    # 可选的监控埋点入口
    monitor_tracker: MonitorTracker | None = None

    def _record_plugin_event(
        self,
        entry: PluginCatalogEntry | None,
        *,
        event_type: PluginEventType,
        message: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """
        写入一条插件事件监控记录。
        """

        if self.monitor_tracker is None or entry is None or entry.manifest is None:
            return

        try:
            self.monitor_tracker.record_plugin_event(
                PluginEventRecord(
                    event_id=uuid4().hex,
                    plugin_id=entry.manifest.plugin_id,
                    version=entry.manifest.version,
                    event_type=event_type,
                    message=message,
                    detail=detail or {},
                    created_at=get_curr_time(),
                )
            )
        except Exception:
            return

    def _record_plugin_status(
        self,
        entry: PluginCatalogEntry | None,
        *,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """
        写入当前插件状态快照。
        """

        if self.monitor_tracker is None or entry is None or entry.manifest is None:
            return

        try:
            self.monitor_tracker.record_plugin_status(
                PluginStatusRecord(
                    plugin_id=entry.manifest.plugin_id,
                    version=entry.manifest.version,
                    install_status=entry.install_status,
                    runtime_status=entry.runtime_status,
                    updated_at=get_curr_time(),
                    detail={
                        "plugin_dir": str(entry.plugin_dir_path),
                        "error_message": entry.error_message or "",
                        "is_compatible": entry.is_compatible,
                        "runtime_mode": _enum_value(entry.manifest.runtime_mode),
                        **(detail or {}),
                    },
                )
            )
        except Exception:
            return

    def _record_plugin_invocation(
        self,
        *,
        entry: PluginCatalogEntry | None,
        execution_id: str | None,
        trace_id: str | None,
        operation: str,
        status: InvocationStatus,
        started_at: datetime,
        finished_at: datetime,
        latency_ms: int | None,
        input_size: int | None,
        output_count: int | None,
        error_message: str | None = None,
    ) -> None:
        """
        写入一条插件调用记录。
        """

        if self.monitor_tracker is None or entry is None or entry.manifest is None:
            return

        try:
            self.monitor_tracker.record_plugin_invocation(
                PluginInvocationRecord(
                    invocation_id=uuid4().hex,
                    execution_id=execution_id or trace_id or uuid4().hex,
                    plugin_id=entry.manifest.plugin_id,
                    version=entry.manifest.version,
                    runtime_mode=str(_enum_value(entry.manifest.runtime_mode)),
                    status=status,
                    started_at=started_at,
                    finished_at=finished_at,
                    latency_ms=latency_ms,
                    input_size=input_size,
                    output_count=output_count,
                    error_message=error_message,
                    detail={
                        "operation": operation,
                        "trace_id": trace_id,
                    },
                )
            )
        except Exception:
            return

    def _get_subprocess_lock(self, plugin_id: str) -> RLock:
        """
        返回指定 subprocess 插件的串行调用锁。
        """

        with self._subprocess_locks_guard:
            lock = self._subprocess_locks_by_id.get(plugin_id)
            if lock is None:
                lock = RLock()
                self._subprocess_locks_by_id[plugin_id] = lock
            return lock

    def _discard_broken_subprocess_plugin(
        self,
        plugin_id: str,
        handle: Any,
        reason: str,
    ) -> None:
        """
        从运行时缓存中移除已回收的 subprocess 句柄
        """

        if self.loaded_plugins_by_id.get(plugin_id) is not handle:
            return

        self.loaded_plugins_by_id.pop(plugin_id, None)

        entry = self.plugin_catalog.get_entry(plugin_id)
        if entry is not None:
            entry.runtime_status = RuntimeStatus.UNAVAILABLE
            entry.error_message = reason

    def exchange_subprocess(
        self,
        plugin_id: str,
        request: AnalyzingModel,
        response_model: type[T],
        response_validator: Callable[[T], None] | None = None,
    ) -> T:
        """
        串行执行 subprocess 的一组 stdio 请求-响应通信。

        前一个请求发生协议错误后，后续等待请求会在这里重新加载新进程，
        不会继续使用已经错位的 stdout。
        """

        with self._get_subprocess_lock(plugin_id):
            handle = self.load_plugin(plugin_id)
            exchange = getattr(handle, "exchange", None)

            if not callable(exchange):
                raise PluginLoadError(
                    f"插件未暴露 subprocess stdio exchange: {plugin_id}"
                )

            try:
                return exchange(
                    request=request,
                    response_model=response_model,
                    response_validator=response_validator,
                )
            except PluginInvokeError as exc:
                if not _is_plugin_available(handle):
                    self._discard_broken_subprocess_plugin(
                        plugin_id=plugin_id,
                        handle=handle,
                        reason=str(exc),
                    )
                raise

    def preload_startup_plugins(self) -> None:
        """
        预加载配置为 startup 的插件
        """

        for entry in self.plugin_catalog.list_entries():
            if not entry.is_compatible or entry.manifest is None:
                continue

            if entry.load_strategy != PluginLoadStrategy.STARTUP:
                continue

            self.load_plugin(entry.manifest.plugin_id)

    def load_plugin(self, plugin_id: str) -> Any:
        """
        加载指定插件
        """

        loaded_plugin = self.get_available_plugin(plugin_id)
        if loaded_plugin is not None:
            return loaded_plugin

        entry = self.plugin_catalog.get_entry(plugin_id)
        if entry is None:
            raise PluginLoadError(f"未找到插件: {plugin_id}")

        if not entry.is_compatible or entry.manifest is None:
            raise PluginLoadError(
                f"插件不可用，无法加载: {plugin_id}, reason={entry.error_message or 'unknown'}"
            )

        if entry.manifest.runtime_mode == RuntimeMode.REMOTE:
            raise PluginLoadError(
                f"remote 插件不能通过本地加载，请远程注册: {plugin_id}"
            )

        try:
            plugin = _load_entry(entry)
        except Exception as exc:
            entry.runtime_status = RuntimeStatus.ERROR
            entry.error_message = str(exc)
            self._record_plugin_event(
                entry,
                event_type=PluginEventType.PLUGIN_LOAD_FAILED,
                message="插件加载失败",
                detail={
                    "error_message": str(exc),
                },
            )
            self._record_plugin_status(entry)
            raise

        self.loaded_plugins_by_id[plugin_id] = plugin
        entry.runtime_status = RuntimeStatus.LOADED
        entry.error_message = ""
        self._record_plugin_event(
            entry,
            event_type=PluginEventType.PLUGIN_LOADED,
            message="插件加载成功",
            detail={},
        )
        self._record_plugin_status(entry)
        return plugin

    def get_loaded_plugin(self, plugin_id: str) -> Any | None:
        """
        获取当前缓存中的已加载插件实例，不做可用性检查
        """

        return self.loaded_plugins_by_id.get(plugin_id)

    def get_available_plugin(self, plugin_id: str) -> Any | None:
        """
        获取当前可用的已加载插件实例，如果缓存实例已经失效，则顺手清理并返回 None
        """

        loaded_plugin = self.loaded_plugins_by_id.get(plugin_id)
        if loaded_plugin is None:
            return None

        if _is_plugin_available(loaded_plugin):
            return loaded_plugin

        self.unload_plugin(plugin_id)
        return None

    def invoke_plugin(
        self,
        plugin_id: str,
        operation: str,
        payload: dict[str, Any],
        execution_id: str | None = None,
        trace_id: str | None = None,
    ) -> PluginInvokeResponse:
        """
        统一调用插件

        - inproc：直接本地调用
        - subprocess：走 stdio client
        - remote：后续接入同一入口
        """

        entry = self.plugin_catalog.get_entry(plugin_id)
        started_at = get_curr_time()
        input_size = _estimate_payload_size(payload)

        request = PluginInvokeRequest(
            trace_id=trace_id,
            plugin_id=plugin_id,
            operation=operation,
            payload=payload,
        )

        is_subprocess = (
            entry is not None
            and entry.manifest is not None
            and entry.manifest.runtime_mode == RuntimeMode.SUBPROCESS
        )

        try:
            if is_subprocess:
                # 同一 subprocess 插件的 stdio 请求必须串行，避免并发读写同一条通信流。
                with self._get_subprocess_lock(plugin_id):
                    plugin = self.load_plugin(plugin_id)

                    try:
                        invoke = getattr(plugin, "invoke", None)
                        if callable(invoke):
                            response = invoke(request)
                        else:
                            response = _invoke_local_plugin(plugin, request)
                    except Exception as exc:
                        if not _is_plugin_available(plugin):
                            self._discard_broken_subprocess_plugin(
                                plugin_id=plugin_id,
                                handle=plugin,
                                reason=str(exc),
                            )
                        raise
            else:
                plugin = self.load_plugin(plugin_id)
                invoke = getattr(plugin, "invoke", None)

                if callable(invoke):
                    response = invoke(request)
                else:
                    response = _invoke_local_plugin(plugin, request)
        except Exception as exc:
            if entry is not None:
                entry.runtime_status = RuntimeStatus.ERROR
                entry.error_message = str(exc)

            finished_at = get_curr_time()
            latency_ms = int((finished_at - started_at).total_seconds() * 1000)
            invocation_status = (
                InvocationStatus.TIMEOUT
                if isinstance(exc, TimeoutError)
                else InvocationStatus.FAILED
            )
            self._record_plugin_invocation(
                entry=entry,
                execution_id=execution_id,
                trace_id=trace_id,
                operation=operation,
                status=invocation_status,
                started_at=started_at,
                finished_at=finished_at,
                latency_ms=latency_ms,
                input_size=input_size,
                output_count=None,
                error_message=str(exc),
            )
            self._record_plugin_status(entry)
            raise PluginInvokeError(
                f"插件调用失败: plugin_id={plugin_id}, operation={operation}"
            ) from exc

        if not response.ok:
            if entry is not None:
                entry.runtime_status = RuntimeStatus.ERROR
                entry.error_message = response.error_message or ""

            finished_at = get_curr_time()
            latency_ms = int((finished_at - started_at).total_seconds() * 1000)
            self._record_plugin_invocation(
                entry=entry,
                execution_id=execution_id,
                trace_id=trace_id,
                operation=operation,
                status=InvocationStatus.FAILED,
                started_at=started_at,
                finished_at=finished_at,
                latency_ms=latency_ms,
                input_size=input_size,
                output_count=None,
                error_message=response.error_message,
            )
            self._record_plugin_status(entry)
            raise PluginInvokeError(
                response.error_message
                or f"插件调用失败: plugin_id={plugin_id}, operation={operation}"
            )

        if entry is not None:
            entry.runtime_status = RuntimeStatus.READY
            entry.error_message = ""

        finished_at = get_curr_time()
        latency_ms = int((finished_at - started_at).total_seconds() * 1000)
        self._record_plugin_invocation(
            entry=entry,
            execution_id=execution_id,
            trace_id=trace_id,
            operation=operation,
            status=InvocationStatus.SUCCEEDED,
            started_at=started_at,
            finished_at=finished_at,
            latency_ms=latency_ms,
            input_size=input_size,
            output_count=_estimate_output_count(response),
        )
        self._record_plugin_status(entry)
        return response

    def invoke_parser_plugin(
        self,
        plugin_id: str,
        text: str,
        params: dict[str, Any] | None = None,
        execution_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, list[Any]]:
        """
        调用解析器插件并返回 processor 兼容结果
        """

        response = self.invoke_plugin(
            plugin_id=plugin_id,
            operation="parse",
            payload={
                "text": text,
                "params": params or {},
            },
            execution_id=execution_id,
            trace_id=trace_id,
        )

        return _require_parser_pipeline_output(response)

    def register_remote_plugin(
        self,
        register_request: RemoteRegisterRequest,
        *,
        host_profile: HostProfile,
        allow_anonymous_remote: bool,
        shared_token: str | None,
        authorization: str | None,
        runtime_plugins_dir_path: Path | None,
    ) -> RemoteRegisterResponse:
        """
        注册一个 remote 插件实例
        """

        plugin_id = register_request.manifest.plugin_id
        entry = self.plugin_catalog.get_entry(plugin_id)

        provided_token = _extract_bearer_token(authorization)

        # 配置了统一注册令牌时，首次动态注册和后续重连都必须先过这一层
        if shared_token:
            if provided_token != shared_token:
                return RemoteRegisterResponse(
                    accepted=False,
                    message="remote 注册鉴权失败",
                )

        try:
            validate_manifest(register_request.manifest, host_profile)
        except Exception as exc:
            return RemoteRegisterResponse(
                accepted=False,
                message=f"manifest 校验失败: {exc}",
            )

        trusted_manifest = register_request.manifest

        if entry is not None:
            if not entry.is_compatible or entry.manifest is None:
                return RemoteRegisterResponse(
                    accepted=False,
                    message=f"插件不可用，无法注册: {plugin_id}",
                )

            if entry.manifest.runtime_mode != RuntimeMode.REMOTE:
                return RemoteRegisterResponse(
                    accepted=False,
                    message=f"插件不是 remote 模式，无法注册: {plugin_id}",
                )

            try:
                _assert_remote_manifest_matches(
                    entry.manifest,
                    register_request.manifest,
                )
            except Exception as exc:
                return RemoteRegisterResponse(
                    accepted=False,
                    message=str(exc),
                )

            trusted_manifest = entry.manifest

            trusted_runtime = _require_remote_runtime_config(trusted_manifest)
            expected_token = trusted_runtime.registration.shared_token

            if expected_token and provided_token != expected_token:
                return RemoteRegisterResponse(
                    accepted=False,
                    message="remote 注册鉴权失败",
                )
        else:
            if not allow_anonymous_remote and not shared_token:
                return RemoteRegisterResponse(
                    accepted=False,
                    message="当前宿主未开启匿名 remote 接入",
                )

            entry = _build_remote_catalog_entry(
                manifest=trusted_manifest,
                runtime_plugins_dir_path=runtime_plugins_dir_path,
            )
            self.plugin_catalog.upsert_entry(entry)

        trusted_runtime = _require_remote_runtime_config(trusted_manifest)

        # 当前契约里没有单独的 remote invoke timeout，先复用 registration.request_timeout_seconds
        handle = build_remote_plugin_handle(
            manifest=trusted_manifest,
            instance_id=register_request.instance_id,
            endpoint=register_request.endpoint,
            sdk_version=register_request.sdk_version,
            lease_ttl_seconds=trusted_runtime.registration.lease_ttl_seconds,
            invoke_timeout_seconds=max(
                1,
                trusted_runtime.registration.request_timeout_seconds,
            ),
        )

        previous_handle = self.remote_registry.add(handle)
        if previous_handle is not None:
            try:
                previous_handle.close()
            except Exception:
                pass

        self.loaded_plugins_by_id[plugin_id] = handle
        entry.install_status = InstallStatus.INSTALLED
        entry.runtime_status = RuntimeStatus.REGISTERED
        entry.error_message = ""
        self._record_plugin_event(
            entry,
            event_type=PluginEventType.PLUGIN_LOADED,
            message="remote 插件注册成功",
            detail={
                "session_id": handle.session_id,
                "instance_id": handle.instance_id,
            },
        )
        self._record_plugin_status(entry)

        return RemoteRegisterResponse(
            accepted=True,
            session_id=handle.session_id,
            lease_ttl_seconds=trusted_runtime.registration.lease_ttl_seconds,
            message="registered",
        )

    def heartbeat_remote_plugin(
        self,
        heartbeat_request: RemoteHeartbeatRequest,
    ) -> RemoteHeartbeatResponse:
        """
        刷新一个 remote 插件实例的租约
        """

        handle = self.remote_registry.get_by_session_id(heartbeat_request.session_id)
        if handle is None:
            return RemoteHeartbeatResponse(
                accepted=False,
                message="remote 会话不存在",
            )

        if handle.instance_id != heartbeat_request.instance_id:
            return RemoteHeartbeatResponse(
                accepted=False,
                message="remote 实例 ID 不匹配",
            )

        if not handle.is_alive():
            self.remote_registry.remove_session(handle.session_id)
            self.loaded_plugins_by_id.pop(handle.plugin_id, None)

            entry = self.plugin_catalog.get_entry(handle.plugin_id)
            if entry is not None:
                entry.runtime_status = RuntimeStatus.UNAVAILABLE
                entry.error_message = "remote 租约已过期"

            try:
                handle.close()
            except Exception:
                pass

            return RemoteHeartbeatResponse(
                accepted=False,
                message="remote 租约已过期",
            )

        handle.refresh_lease()

        entry = self.plugin_catalog.get_entry(handle.plugin_id)
        if entry is not None:
            entry.runtime_status = RuntimeStatus.READY
            entry.error_message = ""
        self._record_plugin_status(entry)

        return RemoteHeartbeatResponse(
            accepted=True,
            lease_ttl_seconds=handle.lease_ttl_seconds,
            message="ok",
        )

    def unregister_remote_plugin(
        self,
        unregister_request: RemoteUnregisterRequest,
    ) -> bool:
        """
        注销一个 remote 插件实例
        """

        handle = self.remote_registry.get_by_session_id(unregister_request.session_id)
        if handle is None:
            return False

        if handle.instance_id != unregister_request.instance_id:
            return False

        removed_handle = self.remote_registry.remove_session(
            unregister_request.session_id
        )
        if removed_handle is None:
            return False

        self.loaded_plugins_by_id.pop(removed_handle.plugin_id, None)

        entry = self.plugin_catalog.get_entry(removed_handle.plugin_id)
        if entry is not None:
            entry.runtime_status = RuntimeStatus.UNAVAILABLE
            entry.error_message = ""
        self._record_plugin_status(entry)

        try:
            removed_handle.close()
        except Exception:
            pass

        return True

    def invoke_splitter_plugin(
        self,
        plugin_id: str,
        text: str,
        params: dict[str, Any] | None = None,
        execution_id: str | None = None,
        trace_id: str | None = None,
    ) -> list[str]:
        """
        调用拆分器插件并返回 processor 兼容结果
        """

        response = self.invoke_plugin(
            plugin_id=plugin_id,
            operation="split",
            payload={
                "text": text,
                "params": params or {},
            },
            execution_id=execution_id,
            trace_id=trace_id,
        )

        return _require_splitter_pipeline_output(response)

    def unload_plugin(self, plugin_id: str) -> None:
        """
        卸载指定插件
        """

        loaded_plugin = self.loaded_plugins_by_id.pop(plugin_id, None)
        if loaded_plugin is None:
            return

        entry = self.plugin_catalog.get_entry(plugin_id)

        try:
            _close_plugin(loaded_plugin)
        except Exception as exc:
            if entry is not None:
                entry.runtime_status = RuntimeStatus.ERROR
                entry.error_message = str(exc)
            raise

        if entry is not None:
            entry.runtime_status = RuntimeStatus.UNAVAILABLE
            entry.error_message = ""
        self._record_plugin_status(entry)

    def shutdown(self) -> None:
        """
        关闭全部已加载插件
        """

        for plugin_id in list(self.loaded_plugins_by_id.keys()):
            try:
                self.unload_plugin(plugin_id)
            except Exception:
                continue


__all__ = ["EngineRuntimeManager"]
