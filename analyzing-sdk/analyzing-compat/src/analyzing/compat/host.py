from __future__ import annotations

from pydantic import Field

from analyzing.contracts.model import AnalyzingModel
from analyzing.runtime.mode import RuntimeMode


class SDKDistribution(AnalyzingModel):
    """
    SDK 分发信息
    """

    # 分发渠道，例如 private
    channel: str = "private"

    # 是否发布到公共 PyPI
    public_pypi: bool = False

    # 交付格式，例如 wheel
    format: str = "wheel"


class HostFeatures(AnalyzingModel):
    """
    宿主能力开关
    """

    # 是否支持字段映射能力
    field_mapping: bool = False

    # 是否支持插件目录重扫
    plugin_rescan: bool = False

    # 是否支持对结果进行拍平处理
    supports_output_flatten: bool = False

    # 是否支持服务模式运行
    service_mode: bool = False


class HostProfile(AnalyzingModel):
    """
    宿主画像
    """

    # 宿主自身版本
    host_version: str

    # 当前绑定的 SDK 版本
    sdk_version: str

    # 宿主运行时 Python 版本
    python_version: str

    # 宿主支持的运行模式列表
    supported_runtime_modes: list[RuntimeMode] = Field(default_factory=list)

    # 插件包后缀
    plugin_package_suffix: str = ".rain"

    # 宿主能力开关集合
    features: HostFeatures = Field(default_factory=HostFeatures)

    # 宿主承诺提供的基础依赖信息
    baseline_dependencies: dict[str, str] = Field(default_factory=dict)

    # SDK 分发方式信息
    sdk_distribution: SDKDistribution = Field(default_factory=SDKDistribution)


__all__ = ["SDKDistribution", "HostFeatures", "HostProfile"]