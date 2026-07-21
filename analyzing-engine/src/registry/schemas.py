from dataclasses import dataclass, field
from pathlib import Path

from analyzing.plugin.enums.plugin import InstallStatus, RuntimeStatus, PluginRole
from analyzing.plugin.manifest import PluginManifest, PluginDescriptor

from src.app.enums import PluginLoadStrategy


def _enum_value(raw: object) -> object:
    """
    兼容枚举对象或已经被序列化成字符串的枚举值。
    """

    return getattr(raw, "value", raw)


@dataclass(slots=True)
class PluginCatalogEntry:
    """
    引擎内存中的插件登记项
    """

    # 插件目录路径
    plugin_dir_path: Path

    # manifest 文件路径
    manifest_file_path: Path | None

    # 插件 manifest
    manifest: PluginManifest | None

    # 插件加载策略
    load_strategy: PluginLoadStrategy

    # 是否通过兼容性校验
    is_compatible: bool

    # 插件安装状态
    install_status: InstallStatus = InstallStatus.DISCOVERED

    # 插件运行状态
    runtime_status: RuntimeStatus = RuntimeStatus.UNAVAILABLE

    # 错误信息
    error_message: str = ""

    def to_descriptor(self) -> PluginDescriptor | None:
        """
        将登记项转换为引擎对外暴露的插件描述
        """

        if self.manifest is None:
            return None

        return PluginDescriptor(
            plugin_id=self.manifest.plugin_id,
            name=self.manifest.name,
            version=self.manifest.version,
            plugin_role=self.manifest.plugin_role,
            infra_slot=self.manifest.infra_slot,
            plugin_type=self.manifest.plugin_type,
            runtime_mode=self.manifest.runtime_mode,
            enabled=True,
            install_status=self.install_status,
            runtime_status=self.runtime_status,
            summary=self.manifest.summary,
            description=self.manifest.description,
            capabilities=self.manifest.capabilities,
            form_schema=self.manifest.form_schema,
        )

    def to_dict(self) -> dict:
        """
        将登记项转换为引擎内部可读的字典结构
        """

        return {
            "plugin_dir": str(self.plugin_dir_path),
            "manifest_file": (
                str(self.manifest_file_path)
                if self.manifest_file_path is not None
                else None
            ),
            "load_strategy": _enum_value(self.load_strategy),
            "is_compatible": self.is_compatible,
            "install_status": _enum_value(self.install_status),
            "runtime_status": _enum_value(self.runtime_status),
            "error_message": self.error_message,
            "manifest": (
                self.manifest.model_dump(mode="json")
                if self.manifest is not None
                else None
            ),
        }


@dataclass(slots=True)
class PluginCatalog:
    """
    引擎插件注册表
    """

    # 按 plugin_id 建立的登记项索引
    entries_by_id: dict[str, PluginCatalogEntry] = field(default_factory=dict)

    # 扫描失败但还没拿到 plugin_id 的目录登记项
    invalid_entries: list[PluginCatalogEntry] = field(default_factory=list)

    def add_entry(self, entry: PluginCatalogEntry) -> None:
        """
        添加一个插件登记项
        """

        if entry.manifest is None:
            self.invalid_entries.append(entry)
            return

        plugin_id = entry.manifest.plugin_id

        if plugin_id in self.entries_by_id:
            existing_entry = self.entries_by_id[plugin_id]
            duplicate_message = (
                f"发现重复的 plugin_id: {plugin_id}, "
                f"existing={existing_entry.plugin_dir_path}, current={entry.plugin_dir_path}"
            )

            existing_entry.is_compatible = False
            existing_entry.install_status = InstallStatus.FAILED
            existing_entry.runtime_status = RuntimeStatus.ERROR
            existing_entry.error_message = duplicate_message

            entry.is_compatible = False
            entry.install_status = InstallStatus.FAILED
            entry.runtime_status = RuntimeStatus.ERROR
            entry.error_message = duplicate_message

        self.entries_by_id[plugin_id] = entry

    def upsert_entry(self, entry: PluginCatalogEntry) -> None:
        """
        按 plugin_id 覆盖写入登记项
        """

        if entry.manifest is None:
            self.invalid_entries.append(entry)
            return

        self.entries_by_id[entry.manifest.plugin_id] = entry

    def get_entry(self, plugin_id: str) -> PluginCatalogEntry | None:
        """
        按 plugin_id 获取登记项
        """

        return self.entries_by_id.get(plugin_id)

    def list_entries(self) -> list[PluginCatalogEntry]:
        """
        返回全部已登记插件
        """

        return list(self.entries_by_id.values())

    def list_descriptors(self) -> list[PluginDescriptor]:
        """
        返回全部可对外暴露的插件描述
        """

        descriptors: list[PluginDescriptor] = []

        for entry in self.entries_by_id.values():
            descriptor = entry.to_descriptor()
            if descriptor is not None:
                descriptors.append(descriptor)

        return descriptors

    def list_invalid_entries(self) -> list[PluginCatalogEntry]:
        """
        返回全部无效插件登记项
        """

        invalid_entries = list(self.invalid_entries)

        for entry in self.entries_by_id.values():
            if not entry.is_compatible:
                invalid_entries.append(entry)

        return invalid_entries

    def get_descriptor(self, plugin_id: str) -> PluginDescriptor | None:
        """
        按 plugin_id 获取插件描述
        """

        entry = self.get_entry(plugin_id)
        if entry is None:
            return None

        return entry.to_descriptor()

    def get_infra_slot_conflicts(self) -> dict[str, list[PluginCatalogEntry]]:
        """
        返回基础插件 slot 冲突信息
        """

        grouped: dict[str, list[PluginCatalogEntry]] = {}

        for entry in self.entries_by_id.values():
            if not entry.is_compatible or entry.manifest is None:
                continue

            manifest = entry.manifest
            if manifest.plugin_role != PluginRole.INFRA or manifest.infra_slot is None:
                continue

            slot = str(_enum_value(manifest.infra_slot))
            grouped.setdefault(slot, []).append(entry)

        return {slot: entries for slot, entries in grouped.items() if len(entries) > 1}


__all__ = ["PluginCatalogEntry", "PluginCatalog"]
