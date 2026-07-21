from __future__ import annotations

import os
import subprocess
import time
from collections import deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from threading import Lock, Thread
from typing import TypeVar

from analyzing.contracts.model import AnalyzingModel
from analyzing.plugin.errors import PluginLoadError, PluginInvokeError
from analyzing.plugin.remote import PluginInvokeRequest, PluginInvokeResponse
from analyzing.runtime.config import SubprocessRuntimeConfig
from analyzing.runtime.errors import RuntimeProtocolError
from analyzing.runtime.subprocess import (
    SubprocessJsonStdioClient,
    build_subprocess_command,
)

from src.registry.schemas import PluginCatalogEntry

T = TypeVar("T", bound=AnalyzingModel)

# Windows 拉起子进程时，不弹黑框窗口
if os.name == "nt":
    _SUBPROCESS_CREATION_FLAGS = subprocess.CREATE_NO_WINDOW
else:
    _SUBPROCESS_CREATION_FLAGS = 0


@dataclass(slots=True)
class SubprocessStderrBuffer:
    """
    缓存子进程最近的 stderr 输出，便于宿主定位问题
    """

    # 仅保留最近若干行，避免日志无限增长
    lines: deque[str] = field(default_factory=lambda: deque(maxlen=50))

    # 读取和写入都走同一把锁，避免并发时拿到半截结果
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def append(self, message: str) -> None:
        """
        记录一条 stderr 消息
        """

        normalized = message.rstrip()
        if not normalized:
            return

        with self._lock:
            self.lines.append(normalized)

    def render(self) -> str:
        """
        渲染最近的 stderr 内容
        """

        with self._lock:
            return "\n".join(self.lines)


def _consume_process_stderr(
    stream: subprocess.Popen[str] | object,
    stderr_buffer: SubprocessStderrBuffer,
) -> None:
    """
    持续消费 stderr，避免子进程因为错误输出堆积而阻塞
    """

    if not hasattr(stream, "readline"):
        return

    try:
        while True:
            line = stream.readline()
            if not line:
                return
            if isinstance(line, str):
                stderr_buffer.append(line)
    except Exception:
        return


def _close_process_streams(process: subprocess.Popen[str]) -> None:
    """
    关闭子进程关联的标准流
    """

    for stream in (process.stdin, process.stdout, process.stderr):
        if stream is None:
            continue

        try:
            stream.close()
        except Exception:
            continue


def _probe_process_started(
    process: subprocess.Popen[str],
    stderr_buffer: SubprocessStderrBuffer,
    startup_timeout_seconds: int,
) -> None:
    """
    当前阶段还没有 ready 握手协议，这里只做“是否秒退”的轻量探测
    """

    probe_seconds = min(max(float(startup_timeout_seconds), 0.1), 1.0)
    time.sleep(probe_seconds)

    return_code = process.poll()
    if return_code is None:
        return

    _close_process_streams(process)
    error_message = f"subprocess 插件启动后立即退出: code={return_code}"
    stderr_output = stderr_buffer.render()
    if stderr_output:
        error_message = f"{error_message}\nrecent stderr:\n{stderr_output}"

    raise PluginLoadError(error_message)


@dataclass(slots=True)
class SubprocessPluginHandle:
    """
    引擎内维护的 subprocess 插件句柄
    """

    # 插件 ID
    plugin_id: str

    # 子进程对象
    process: subprocess.Popen[str]

    # stdio 调用客户端
    client: SubprocessJsonStdioClient

    # 实际启动命令
    argv: list[str]

    # 实际工作目录
    cwd: str

    # 实际环境变量
    env: dict[str, str]

    # 通信协议
    protocol: str

    # 最近的 stderr 输出
    stderr_buffer: SubprocessStderrBuffer

    # 调用超时时间，单位秒
    invoke_timeout_seconds: int

    # 关闭超时时间，单位秒
    shutdown_timeout_seconds: int

    # 将阻塞式 stdio 调用包进单线程执行器，便于做调用超时控制
    invoke_executor: ThreadPoolExecutor = field(repr=False)

    # stderr 消费线程
    stderr_thread: Thread | None = field(default=None, repr=False)

    # 避免并发调用 close 时重复回收同一个进程
    _close_lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def get_recent_stderr(self) -> str:
        """
        返回最近采集到的 stderr 内容
        """

        return self.stderr_buffer.render()

    def is_alive(self) -> bool:
        """
        返回子进程当前是否仍在运行
        """

        return self.process.poll() is None

    def invoke(self, request: PluginInvokeRequest) -> PluginInvokeResponse:
        """
        通过 stdio 协议调用 subprocess 插件
        """

        return self.exchange(
            request=request,
            response_model=PluginInvokeResponse,
        )

    def exchange(
        self,
        request: AnalyzingModel,
        response_model: type[T],
        response_validator: Callable[[T], None] | None = None,
    ) -> T:
        """
        执行一次 stdio 请求-响应通信
        """

        if not self.is_alive():
            self.close()

            stderr_output = self.get_recent_stderr()
            detail = f"\nrecent stderr:\n{stderr_output}" if stderr_output else ""
            raise PluginInvokeError(
                f"subprocess 插件进程已退出，无法调用: {self.plugin_id}{detail}"
            )

        future = self.invoke_executor.submit(
            self.client.exchange,
            request,
            response_model,
        )

        try:
            response = future.result(timeout=self.invoke_timeout_seconds)

            if response_validator is not None:
                response_validator(response)

            return response
        except FutureTimeoutError as exc:
            # 超时后无法确认响应是否会迟到，当前 stdio 流不能继续复用。
            self.close()

            stderr_output = self.get_recent_stderr()
            detail = f"\nrecent stderr:\n{stderr_output}" if stderr_output else ""
            raise PluginInvokeError(
                "subprocess 插件调用超时: "
                f"{self.plugin_id}, timeout={self.invoke_timeout_seconds}s{detail}"
            ) from exc
        except (
            RuntimeProtocolError,
            UnicodeDecodeError,
            EOFError,
            BrokenPipeError,
            OSError,
            ValueError,
        ) as exc:
            # 非法 JSON、乱码、管道关闭、request_id 不匹配等都视为协议损坏。
            self.close()

            stderr_output = self.get_recent_stderr()
            detail = f"\nrecent stderr:\n{stderr_output}" if stderr_output else ""
            raise PluginInvokeError(
                f"subprocess 插件协议通信失败: {self.plugin_id}{detail}"
            ) from exc

    def close(self) -> None:
        """
        关闭子进程并回收关联资源。
        """

        with self._close_lock:
            if self.process.poll() is None:
                self.process.terminate()

                try:
                    self.process.wait(timeout=self.shutdown_timeout_seconds)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()

            _close_process_streams(self.process)
            self.invoke_executor.shutdown(wait=False, cancel_futures=True)


def load_subprocess_plugin(entry: PluginCatalogEntry) -> SubprocessPluginHandle:
    """
    根据登记项拉起 subprocess 插件
    """

    manifest = entry.manifest
    if manifest is None:
        raise PluginLoadError("插件 manifest 不存在，无法加载 subprocess 插件")

    runtime_config = manifest.runtime
    if runtime_config is None:
        raise PluginLoadError("插件未声明 runtime 配置，无法加载 subprocess 插件")

    if not isinstance(runtime_config, SubprocessRuntimeConfig):
        raise PluginLoadError(
            "插件 runtime 配置不是 subprocess，无法按 subprocess 方式加载"
        )

    launcher = runtime_config.launcher
    if launcher.protocol != "json-stdio":
        raise PluginLoadError(
            f"当前版本仅支持 json-stdio subprocess 协议: {launcher.protocol}"
        )

    argv, configured_cwd, env_delta = build_subprocess_command(
        config=runtime_config,
        base_dir=str(entry.plugin_dir_path),
    )

    if not argv or not argv[0]:
        raise PluginLoadError("subprocess 启动命令为空")

    # 未显式声明 cwd 时，默认使用插件目录作为工作目录
    cwd = configured_cwd or str(entry.plugin_dir_path)

    env = os.environ.copy()
    env.update(env_delta)
    env.setdefault("PYTHONUNBUFFERED", "1")
    stderr_buffer = SubprocessStderrBuffer()

    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=_SUBPROCESS_CREATION_FLAGS,
        )
    except OSError as exc:
        raise PluginLoadError(
            f"拉起 subprocess 插件失败: plugin_id={manifest.plugin_id}, argv={argv}"
        ) from exc

    stderr_thread: Thread | None = None
    if process.stderr is not None:
        stderr_thread = Thread(
            target=_consume_process_stderr,
            args=(process.stderr, stderr_buffer),
            daemon=True,
            name=f"plugin-stderr-{manifest.plugin_id}",
        )
        stderr_thread.start()

    _probe_process_started(
        process=process,
        stderr_buffer=stderr_buffer,
        startup_timeout_seconds=launcher.startup_timeout_seconds,
    )

    if process.stdin is None or process.stdout is None:
        process.kill()
        process.wait()
        raise PluginLoadError("subprocess 插件 stdio 管道不可用")

    client = SubprocessJsonStdioClient(
        writer=process.stdin,
        reader=process.stdout,
    )

    return SubprocessPluginHandle(
        plugin_id=manifest.plugin_id,
        process=process,
        client=client,
        argv=argv,
        cwd=cwd,
        env=env,
        protocol=launcher.protocol,
        stderr_buffer=stderr_buffer,
        invoke_timeout_seconds=launcher.invoke_timeout_seconds,
        shutdown_timeout_seconds=launcher.shutdown_timeout_seconds,
        stderr_thread=stderr_thread,
        invoke_executor=ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix=f"plugin-invoke-{manifest.plugin_id}",
        ),
    )


__all__ = ["SubprocessPluginHandle", "load_subprocess_plugin"]
