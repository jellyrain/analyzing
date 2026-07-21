from typing import Any

from pydantic import Field
from analyzing.contracts.model import AnalyzingModel

from analyzing.plugin.enums.param import ParamType


class VisibleWhen(AnalyzingModel):
    """
    字段显示条件
    """

    # 被依赖的字段名
    field: str

    # 当字段值等于该值时显示
    equals: Any | None = None

    # 当字段值不等于该值时显示
    not_equals: Any | None = None

    # 当字段值属于该集合时显示
    in_values: list[Any] = Field(default_factory=list)


class EnumOption(AnalyzingModel):
    """
    枚举参数候选项
    """

    # 候选项展示名称
    label: str

    # 候选项真实取值
    value: str


class ParamDefinition(AnalyzingModel):
    """
    插件参数定义
    """

    # 参数唯一键
    key: str

    # 参数展示名称
    label: str

    # 参数类型
    type: ParamType

    # 是否必填
    required: bool = False

    # 默认值
    default: Any | None = None

    # 参数说明
    description: str = ""

    # 输入框占位提示
    placeholder: str = ""

    # 枚举候选项，仅枚举类型使用
    enum_options: list[EnumOption] = Field(default_factory=list)

    # 最小值，仅数值类型使用
    min: int | float | None = None

    # 最大值，仅数值类型使用
    max: int | float | None = None

    # 步长，仅数值类型使用
    step: int | float | None = None

    # 是否允许多值
    multiple: bool = False

    # 联动显示条件
    visible_when: VisibleWhen | None = None


__all__ = [
    "VisibleWhen",
    "EnumOption",
    "ParamDefinition",
]
