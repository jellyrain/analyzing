from enum import StrEnum


class FieldType(StrEnum):
    """
    插件参数可保存的数据类型
    """

    # 文本
    STRING = "string"

    # 数值，可包含小数
    NUMBER = "number"

    # 整数
    INTEGER = "integer"

    # 布尔值
    BOOLEAN = "boolean"

    # 列表
    ARRAY = "array"

    # 只能作为 list 的 items 使用，不能作为顶层参数
    OBJECT = "object"


class WidgetType(StrEnum):
    """
    前端支持的固定通用控件类型
    """

    # 单行输入
    INPUT = "input"

    # 多行文本输入
    TEXTAREA = "textarea"

    # 数值输入
    NUMBER = "number"

    # 布尔开关
    SWITCH = "switch"

    # 下拉单选
    SELECT = "select"

    # 单选按钮组
    RADIO = "radio"

    # 多选框组
    CHECKBOX_GROUP = "checkbox_group"

    # 可增删列表
    LIST = "list"


__all__ = ["FieldType", "WidgetType"]
