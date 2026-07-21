from enum import StrEnum


class RuntimeMode(StrEnum):
    """
    插件运行模式
    """

    # 进程内运行，适合轻量插件
    INPROC = "inproc"

    # 子进程运行，适合重依赖插件
    SUBPROCESS = "subprocess"

    # 外部进程主动注册到宿主
    REMOTE = "remote"


__all__ = ["RuntimeMode"]
