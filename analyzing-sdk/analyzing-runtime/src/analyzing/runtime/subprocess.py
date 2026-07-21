from threading import Lock
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO, TypeVar

from analyzing.contracts.model import AnalyzingModel

from analyzing.runtime.config import SubprocessRuntimeConfig
from analyzing.runtime.stdio import read_model_message, write_model_message

T = TypeVar("T", bound=AnalyzingModel)


def build_subprocess_command(
    config: SubprocessRuntimeConfig,
    base_dir: str | None = None,
) -> tuple[list[str], str | None, dict[str, str]]:
    """
    把 subprocess 配置解析为 argv、cwd 和 env
    """

    launcher = config.launcher
    argv = [launcher.command, *launcher.args]

    cwd: str | None = None
    if launcher.cwd:
        if base_dir:
            cwd = str((Path(base_dir) / launcher.cwd).resolve())
        else:
            cwd = str(Path(launcher.cwd).resolve())

    env = dict(launcher.env)
    return argv, cwd, env


@dataclass(slots=True)
class SubprocessJsonStdioClient:
    """
    宿主侧 stdio JSON 调用客户端
    """

    # 子进程标准输入
    writer: TextIO

    # 子进程标准输出
    reader: TextIO

    # 串行化 stdio 请求，避免多线程同时读写同一条流
    _io_lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def exchange(self, request: AnalyzingModel, response_model: type[T]) -> T:
        with self._io_lock:
            write_model_message(self.writer, request)
            return read_model_message(self.reader, response_model)


__all__ = ["build_subprocess_command", "SubprocessJsonStdioClient"]
