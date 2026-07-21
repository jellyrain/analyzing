from dataclasses import dataclass
from pathlib import Path

from analyzing.compat.host import HostProfile
from analyzing.contracts.model import AnalyzingModel
from analyzing.monitor.service import MonitorService
from analyzing.monitor.tracker import MonitorTracker
from analyzing.persistence.protocols import PersistenceService
from pydantic import Field

from src.app.enums import PluginLoadStrategy
from src.registry.schemas import PluginCatalog
from src.runtime.manager import EngineRuntimeManager


def _resolve_project_path(root_dir_path: Path, path_value: str) -> Path:
    """
    将配置中的相对路径转换为基于项目根目录的绝对路径
    """

    path = Path(path_value).expanduser()

    if path.is_absolute():
        return path.resolve(strict=False)

    return (root_dir_path / path).resolve(strict=False)


class EngineServerConfig(AnalyzingModel):
    """
    引擎 HTTP 服务配置
    """

    # 引擎监听地址
    host: str = "0.0.0.0"

    # 引擎监听端口
    port: int = Field(default=8000, ge=1, le=65535)


class EnginePathsConfig(AnalyzingModel):
    """
    引擎目录配置
    """

    # 插件目录，相对路径基于项目根目录
    plugins_dir: str = "plugins"

    # 数据目录，相对路径基于项目根目录
    data_dir: str = "data"

    # 日志目录，相对路径基于项目根目录
    logs_dir: str = "data/logs"

    # 运行时插件目录，相对路径基于项目根目录
    runtime_plugins_dir: str = "data/plugins"

    # 解析后的插件目录绝对路径
    plugins_dir_path: Path | None = None

    # 解析后的数据目录绝对路径
    data_dir_path: Path | None = None

    # 解析后的日志目录绝对路径
    logs_dir_path: Path | None = None

    # 解析后的运行时插件目录绝对路径
    runtime_plugins_dir_path: Path | None = None

    def resolve(self, root_dir_path: Path) -> "EnginePathsConfig":
        """
        基于项目根目录补全绝对路径
        """

        return self.model_copy(
            update={
                "plugins_dir_path": _resolve_project_path(
                    root_dir_path, self.plugins_dir
                ),
                "data_dir_path": _resolve_project_path(root_dir_path, self.data_dir),
                "logs_dir_path": _resolve_project_path(root_dir_path, self.logs_dir),
                "runtime_plugins_dir_path": _resolve_project_path(
                    root_dir_path, self.runtime_plugins_dir
                ),
            }
        )


class EngineRemoteConfig(AnalyzingModel):
    """
    remote 插件接入配置
    """

    # 是否允许未携带注册令牌的 remote 插件匿名接入
    allow_anonymous_remote: bool = False

    # 统一的 remote 注册令牌
    shared_token: str | None = None


class EngineInfraStorageConfig(AnalyzingModel):
    """
    引擎存储基础设施配置
    """

    # 当前选中的存储插件 ID
    plugin_id: str

    # 当前存储插件配置文件，相对路径基于项目根目录
    config_file: str

    # 解析后的存储插件配置文件绝对路径
    config_file_path: Path | None = None

    def resolve(self, root_dir_path: Path) -> "EngineInfraStorageConfig":
        """
        基于项目根目录补全绝对路径
        """

        return self.model_copy(
            update={
                "config_file_path": _resolve_project_path(
                    root_dir_path, self.config_file
                ),
            }
        )


class EngineInfraConfig(AnalyzingModel):
    """
    引擎基础设施配置
    """

    # 引擎当前绑定的存储能力配置
    storage: EngineInfraStorageConfig

    def resolve(self, root_dir_path: Path) -> "EngineInfraConfig":
        """
        基于项目根目录补全绝对路径
        """

        return self.model_copy(
            update={
                "storage": self.storage.resolve(root_dir_path),
            }
        )


class EnginePluginsLoadConfig(AnalyzingModel):
    """
    插件默认加载策略配置
    """

    # 默认加载策略
    default: PluginLoadStrategy = PluginLoadStrategy.LAZY


class EnginePluginsStartupConfig(AnalyzingModel):
    """
    启动即加载插件配置
    """

    # 启动时立即加载的插件 ID 列表
    plugin_ids: list[str] = Field(default_factory=list)


class EnginePluginsConfig(AnalyzingModel):
    """
    引擎插件调度配置
    """

    # 默认加载策略配置
    load: EnginePluginsLoadConfig = Field(default_factory=EnginePluginsLoadConfig)

    # 启动即加载插件配置
    startup: EnginePluginsStartupConfig = Field(
        default_factory=EnginePluginsStartupConfig
    )


class EngineConfig(AnalyzingModel):
    """
    引擎主配置
    """

    # 引擎 HTTP 服务配置
    server: EngineServerConfig = Field(default_factory=EngineServerConfig)

    # 引擎目录配置
    paths: EnginePathsConfig = Field(default_factory=EnginePathsConfig)

    # remote 插件接入配置
    remote: EngineRemoteConfig = Field(default_factory=EngineRemoteConfig)

    # 引擎基础设施配置
    infra: EngineInfraConfig

    # 当前项目根目录绝对路径
    root_dir_path: Path | None = None

    # 当前配置文件绝对路径
    config_file_path: Path | None = None

    # 引擎插件调度配置
    plugins: EnginePluginsConfig = Field(default_factory=EnginePluginsConfig)

    def resolve(self, config_file_path: Path) -> "EngineConfig":
        """
        基于配置文件位置补全引擎运行时所需的绝对路径
        """

        normalized_config_file_path = config_file_path.resolve(strict=False)
        root_dir_path = normalized_config_file_path.parent.parent.resolve(strict=False)

        return self.model_copy(
            update={
                "root_dir_path": root_dir_path,
                "config_file_path": normalized_config_file_path,
                "paths": self.paths.resolve(root_dir_path),
                "infra": self.infra.resolve(root_dir_path),
            }
        )


@dataclass(slots=True)
class EngineContext:
    """
    引擎运行时上下文
    """

    # 引擎主配置
    config: EngineConfig

    # 引擎画像
    host_profile: HostProfile

    # 引擎插件注册表
    plugin_catalog: PluginCatalog | None = None

    # 引擎插件运行时管理器
    runtime_manager: EngineRuntimeManager | None = None

    # 引擎统一存储服务
    persistence: PersistenceService | None = None

    # 引擎监控写入入口
    monitor_tracker: MonitorTracker | None = None

    # 引擎监控查询服务
    monitor_service: MonitorService | None = None


__all__ = [
    "EngineServerConfig",
    "EnginePathsConfig",
    "EngineRemoteConfig",
    "EngineInfraStorageConfig",
    "EngineInfraConfig",
    "EnginePluginsLoadConfig",
    "EnginePluginsStartupConfig",
    "EnginePluginsConfig",
    "EngineConfig",
    "EngineContext",
]
