from typing import Literal, Annotated

from pydantic import Field

from analyzing.contracts.model import AnalyzingModel


class InprocEntrypoint(AnalyzingModel):
    """
    inproc 插件入口
    """

    # 模块路径，例如 plugin.main
    module: str

    # 模块中的目标属性名，例如 DemoParserPlugin
    attribute: str


class InprocRuntimeConfig(AnalyzingModel):
    """
    inproc 运行配置
    """

    # 运行配置类型标识
    kind: Literal["inproc"] = "inproc"

    # inproc 入口点定义
    entrypoint: InprocEntrypoint

    # 额外搜索路径，宿主可选择加入 sys.path
    search_paths: list[str] = Field(default_factory=list)


class SubprocessLauncherSpec(AnalyzingModel):
    """
    subprocess 启动配置
    """

    # 启动命令，例如 python
    command: str

    # 启动参数列表
    args: list[str] = Field(default_factory=list)

    # 工作目录
    cwd: str | None = None

    # 环境变量增量
    env: dict[str, str] = Field(default_factory=dict)

    # 通信协议，例如 json-stdio
    protocol: str = "json-stdio"

    # 启动超时时间，单位秒
    startup_timeout_seconds: int = 30

    # 调用超时时间，单位秒
    invoke_timeout_seconds: int = 300

    # 关闭超时时间，单位秒
    shutdown_timeout_seconds: int = 10


class SubprocessRuntimeConfig(AnalyzingModel):
    """
    subprocess 运行配置
    """

    # 运行配置类型标识
    kind: Literal["subprocess"] = "subprocess"

    # 子进程启动规格
    launcher: SubprocessLauncherSpec


class RemoteExposeSpec(AnalyzingModel):
    """
    remote 插件对宿主暴露的服务信息
    """

    # 远程插件服务基地址
    base_url: str

    # 通信协议，例如 http-json
    protocol: str = "http-json"

    # 调用接口路径
    invoke_path: str = "/invoke"

    # 健康检查接口路径
    healthcheck_path: str = "/healthz"

    # 调用时附加的请求头
    headers: dict[str, str] = Field(default_factory=dict)


class RemoteRegistrationSpec(AnalyzingModel):
    """
    remote 插件向宿主注册的配置
    """

    # 宿主基地址
    host_url: str

    # 注册接口路径
    register_path: str = "/api/runtime/remote/register"

    # 心跳接口路径
    heartbeat_path: str = "/api/runtime/remote/heartbeat"

    # 注销接口路径
    unregister_path: str = "/api/runtime/remote/unregister"

    # 鉴权令牌
    shared_token: str | None = None

    # 心跳发送间隔，单位秒
    heartbeat_interval_seconds: int = 15

    # 宿主租约有效期，单位秒
    lease_ttl_seconds: int = 45

    # 请求超时时间，单位秒
    request_timeout_seconds: int = 10


class RemoteRuntimeConfig(AnalyzingModel):
    """
    remote 运行配置
    """

    # 运行配置类型标识
    kind: Literal["remote"] = "remote"

    # 对宿主暴露的远程服务信息
    service: RemoteExposeSpec

    # 向宿主注册所需的配置
    registration: RemoteRegistrationSpec


RuntimeConfig = Annotated[
    InprocRuntimeConfig | SubprocessRuntimeConfig | RemoteRuntimeConfig,
    Field(discriminator="kind"),
]

__all__ = [
    "InprocEntrypoint",
    "InprocRuntimeConfig",
    "SubprocessLauncherSpec",
    "SubprocessRuntimeConfig",
    "RemoteExposeSpec",
    "RemoteRegistrationSpec",
    "RemoteRuntimeConfig",
    "RuntimeConfig",
]
