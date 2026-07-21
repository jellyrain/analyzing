from enum import StrEnum


class PluginType(StrEnum):
    """
    插件类型
    """

    # 解析器插件
    PARSER = "parser"

    # 拆分器插件
    SPLITTER = "splitter"


class PluginRole(StrEnum):
    """
    插件角色
    """

    # 业务插件
    BIZ = "biz"

    # 基础插件
    INFRA = "infra"


class InfraSlot(StrEnum):
    """
    基础插件槽位
    """

    # 存储后端
    STORAGE = "storage"


class InstallStatus(StrEnum):
    """
    插件安装状态
    """

    # 已发现，但还未完成安装
    DISCOVERED = "discovered"

    # 已成功安装
    INSTALLED = "installed"

    # 安装失败
    FAILED = "failed"

    # 已卸载或已移除
    REMOVED = "removed"


class RuntimeStatus(StrEnum):
    """
    插件运行状态
    """

    # 已注册到宿主
    REGISTERED = "registered"

    # 已完成加载
    LOADED = "loaded"

    # 已就绪，可执行
    READY = "ready"

    # 当前不可用
    UNAVAILABLE = "unavailable"

    # 运行出错
    ERROR = "error"


class PluginEventType(StrEnum):
    """
    插件事件类型
    """

    # 发现插件包
    PACKAGE_DETECTED = "package_detected"

    # manifest 非法
    MANIFEST_INVALID = "manifest_invalid"

    # 开始安装
    INSTALL_STARTED = "install_started"

    # 安装成功
    INSTALL_SUCCEEDED = "install_succeeded"

    # 安装失败
    INSTALL_FAILED = "install_failed"

    # 检测到原始包已被删除
    PACKAGE_REMOVED = "package_removed"

    # 开始卸载
    UNINSTALL_STARTED = "uninstall_started"

    # 卸载成功
    UNINSTALL_SUCCEEDED = "uninstall_succeeded"

    # 卸载失败
    UNINSTALL_FAILED = "uninstall_failed"

    # 插件已加载
    PLUGIN_LOADED = "plugin_loaded"

    # 插件加载失败
    PLUGIN_LOAD_FAILED = "plugin_load_failed"


class InvocationStatus(StrEnum):
    """
    插件调用状态
    """

    # 已创建，尚未开始调用
    CREATED = "created"

    # 调用中
    RUNNING = "running"

    # 调用成功
    SUCCEEDED = "succeeded"

    # 调用失败
    FAILED = "failed"

    # 调用超时
    TIMEOUT = "timeout"

    # 已跳过
    SKIPPED = "skipped"


__all__ = [
    "PluginRole",
    "InfraSlot",
    "PluginType",
    "InstallStatus",
    "RuntimeStatus",
    "PluginEventType",
    "InvocationStatus",
]
