from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator
from analyzing.contracts.model import AnalyzingModel
from analyzing.runtime.config import RuntimeConfig
from analyzing.runtime.mode import RuntimeMode

from analyzing.plugin.enums.plugin import (
    PluginRole,
    InfraSlot,
    PluginType,
    InstallStatus,
    RuntimeStatus,
)


class PluginExecutionSpec(AnalyzingModel):
    """
    插件能力描述
    """

    # 插件是否接收纯文本输入
    accepts_text: bool = True

    # 插件是否接收结构化输入
    accepts_structured_input: bool = False

    # 插件输出是否为多条结果
    returns_multiple: bool = False

    # 插件输出是否可能为树结构
    returns_hierarchical: bool = False


class HostRequirements(AnalyzingModel):
    """
    插件对宿主的要求
    """

    # 对宿主 Python 版本的要求
    python: str | None = None

    # 对宿主基础依赖的要求
    baseline_dependencies: dict[str, str] = Field(default_factory=dict)


class PluginManifest(AnalyzingModel):
    """
    插件包 manifest
    """

    # 插件唯一标识
    plugin_id: str

    # 插件名称
    name: str

    # 插件版本
    version: str

    # 插件角色
    plugin_role: PluginRole

    # 基础插件槽位
    infra_slot: InfraSlot | None = None

    # 插件类型
    plugin_type: PluginType | None = None

    # 插件运行模式
    runtime_mode: RuntimeMode

    # 插件运行配置，不同 runtime_mode 使用不同结构
    runtime: RuntimeConfig | None = None

    # 插件声明兼容的 SDK 版本约束
    sdk_version: str

    # Python 兼容版本范围
    python_version: str | None = None

    # 支持的平台列表
    platforms: list[str] = Field(default_factory=list)

    # 插件摘要
    summary: str = ""

    # 插件详细描述
    description: str = ""

    # 入口点分组名
    entry_point_group: str | None = None

    # 入口点名称
    entry_point_name: str | None = None

    # 插件输入输出能力
    capabilities: PluginExecutionSpec = Field(default_factory=PluginExecutionSpec)

    # 前端表单 schema 文件，相对 plugin.toml 所在目录
    form_schema_file: str | None = None

    # SDK 加载时注入的表单 schema 内容，只用于内存中的最终 manifest
    form_schema: dict[str, Any] = Field(default_factory=dict)

    # 对宿主的要求
    host_requirements: HostRequirements = Field(default_factory=HostRequirements)

    @model_validator(mode="after")
    def validate_runtime_config(self) -> PluginManifest:
        """
        如果提供了 runtime 配置，则要求它与 runtime_mode 一致
        """

        if self.runtime is None:
            return self

        expected_kind = (
            self.runtime_mode.value
            if hasattr(self.runtime_mode, "value")
            else str(self.runtime_mode)
        )

        if self.runtime.kind != expected_kind:
            raise ValueError(
                f"runtime.kind={self.runtime.kind!r} 与 runtime_mode={expected_kind!r} 不一致"
            )

        return self


class PluginDescriptor(AnalyzingModel):
    """
    宿主对外暴露的插件描述信息
    """

    # 插件唯一标识
    plugin_id: str

    # 插件名称
    name: str

    # 插件版本
    version: str

    # 插件角色
    plugin_role: PluginRole

    # 基础插件槽位
    infra_slot: InfraSlot | None = None

    # 业务插件类型
    plugin_type: PluginType | None = None

    # 插件运行模式
    runtime_mode: RuntimeMode

    # 是否启用
    enabled: bool = True

    # 安装状态
    install_status: InstallStatus

    # 运行状态
    runtime_status: RuntimeStatus

    # 插件摘要
    summary: str = ""

    # 插件详细描述
    description: str = ""

    # 插件能力描述
    capabilities: PluginExecutionSpec = Field(default_factory=PluginExecutionSpec)

    # 最终表单 schema，直接给前端渲染参数页
    form_schema: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "PluginExecutionSpec",
    "HostRequirements",
    "PluginManifest",
    "PluginDescriptor",
]
