from dataclasses import dataclass, field
from pathlib import Path

from analyzing.plugin.manifest import PluginManifest


@dataclass(slots=True)
class RainPackageSpec:
    """
    单个 .rain 插件包的安装信息
    """

    # .rain 包文件路径
    package_file_path: Path

    # 包内 plugin.toml 对应的 manifest
    manifest: PluginManifest

    # 解包目标的角色目录名
    role_dir_name: str

    # 解包目标的插件目录名
    target_dir_name: str

    # .rain 包最后修改时间
    modified_at_ns: int

    @property
    def plugin_id(self) -> str:
        return self.manifest.plugin_id

    @property
    def target_relative_dir(self) -> Path:
        return Path(self.role_dir_name) / self.target_dir_name


@dataclass(slots=True)
class RainSyncResult:
    """
    .rain 同步结果
    """

    # 本次已解包的插件
    installed_plugins: list[str] = field(default_factory=list)

    # 本次已清理的旧目录
    removed_dirs: list[str] = field(default_factory=list)

    # 同步过程中产生的告警
    warnings: list[str] = field(default_factory=list)


__all_ = ["RainPackageSpec", "RainSyncResult"]
