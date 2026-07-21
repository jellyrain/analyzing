from __future__ import annotations

from analyzing.contracts.model import AnalyzingModel
from pydantic import JsonValue, Field, model_validator

from analyzing.plugin.enums.ui import FieldType, WidgetType


class UIOption(AnalyzingModel):
    """
    select、radio、checkbox_group 的一个候选项
    """

    # 前端展示文字
    label: str

    # 最终传递给插件的值
    value: str | int | float | bool


class UIField(AnalyzingModel):
    """
    一个插件参数字段的完整定义
    """

    # 参数的数据类型
    type: FieldType

    # 字段是否必须由用户填写。
    required: bool = False

    # 新建配置时使用的默认值。
    default: JsonValue | None = None

    # 前端控件类型
    widget: WidgetType | None = None

    # 前端显示的字段名称。
    label: str = ""

    # 可输入控件的占位提示。
    placeholder: str = ""

    # select、radio 是否允许选择空值。
    allow_empty: bool = False

    # select、radio、checkbox_group 的候选项
    options: list[UIOption] = Field(default_factory=list)

    # array 的元素定义
    items: UIField | None = None

    # object 的固定字段定义。
    properties: dict[str, UIField] = Field(default_factory=dict)

    @staticmethod
    def _matches_type(value: JsonValue, field_type: FieldType) -> bool:
        """
        判断默认值或候选值是否匹配声明的数据类型
        """

        if field_type == FieldType.STRING:
            return isinstance(value, str)

        if field_type == FieldType.NUMBER:
            return isinstance(value, (int, float)) and not isinstance(value, bool)

        if field_type == FieldType.INTEGER:
            return isinstance(value, int) and not isinstance(value, bool)

        if field_type == FieldType.BOOLEAN:
            return isinstance(value, bool)

        if field_type == FieldType.ARRAY:
            return isinstance(value, list)

        if field_type == FieldType.OBJECT:
            return isinstance(value, dict)

        return False

    @model_validator(mode="after")
    def validate_definition(self) -> UIField:
        """
        校验字段类型、控件类型和嵌套结构的组合是否合法
        """

        if self.default is not None and not self._matches_type(
            self.default,
            self.type,
        ):
            raise ValueError("default 与字段 type 不匹配")

        if self.type == FieldType.ARRAY:
            if self.items is None:
                raise ValueError("array 类型字段必须声明 items")

            # v1 的列表只支持标量列表和固定对象列表
            if self.items.type not in {
                FieldType.STRING,
                FieldType.NUMBER,
                FieldType.INTEGER,
                FieldType.OBJECT,
            }:
                raise ValueError("array.items 只支持 string、number、integer、object")

            # items 只负责描述数组元素，不单独渲染控件
            if self.items.widget is not None:
                raise ValueError("array.items 不能声明 widget")

        if self.type == FieldType.OBJECT:
            if self.widget is not None:
                raise ValueError("object 只用于描述 list 元素，不能声明 widget")

            if not self.properties:
                raise ValueError("object 类型字段必须声明 properties")

            for property_name, property_field in self.properties.items():
                # v1 禁止对象继续嵌套数组或对象，保证前端渲染深度固定
                if property_field.type in {FieldType.ARRAY, FieldType.OBJECT}:
                    raise ValueError(
                        f"object.properties[{property_name}] 只能是标量类型"
                    )

                if property_field.widget is None:
                    raise ValueError(
                        f"object.properties[{property_name}] 必须声明 widget"
                    )

                if not property_field.label:
                    raise ValueError(
                        f"object.properties[{property_name}] 必须声明 label"
                    )

        if self.widget == WidgetType.INPUT:
            if self.type not in {
                FieldType.STRING,
                FieldType.NUMBER,
                FieldType.INTEGER,
            }:
                raise ValueError("input 只能用于 string、number、integer")

        if self.widget == WidgetType.TEXTAREA and self.type != FieldType.STRING:
            raise ValueError("textarea 只能用于 string")

        if self.widget == WidgetType.NUMBER:
            if self.type not in {FieldType.NUMBER, FieldType.INTEGER}:
                raise ValueError("number 只能用于 number、integer")

        if self.widget == WidgetType.SWITCH and self.type != FieldType.BOOLEAN:
            raise ValueError("switch 只能用于 boolean")

        if self.widget == WidgetType.LIST and self.type != FieldType.ARRAY:
            raise ValueError("list 只能用于 array")

        if self.widget == WidgetType.CHECKBOX_GROUP:
            if self.type != FieldType.ARRAY:
                raise ValueError("checkbox_group 只能用于 array")

        if self.widget in {WidgetType.SELECT, WidgetType.RADIO}:
            if self.type not in {
                FieldType.STRING,
                FieldType.NUMBER,
                FieldType.INTEGER,
                FieldType.BOOLEAN,
            }:
                raise ValueError("select、radio 只能用于标量类型")

        if self.options and self.widget not in {
            WidgetType.SELECT,
            WidgetType.RADIO,
            WidgetType.CHECKBOX_GROUP,
        }:
            raise ValueError("options 只能用于选择类控件")

        if self.widget in {WidgetType.SELECT, WidgetType.RADIO} and not self.options:
            raise ValueError("select、radio 必须声明 options")

        if self.widget == WidgetType.CHECKBOX_GROUP and not self.options:
            raise ValueError("checkbox_group 必须声明 options")

        return self


class UISection(AnalyzingModel):
    """
    插件配置页中的一个字段分组
    """

    # 分组名称
    title: str

    # 当前分组展示的顶层字段名
    fields: list[str] = Field(default_factory=list)


class UISchema(AnalyzingModel):
    """
    插件 form.schema.json 的统一表单契约
    """

    # 当前表单协议版本
    version: int = 1

    # 页面字段分组
    sections: list[UISection] = Field(default_factory=list)

    # 顶层插件参数字段
    fields: dict[str, UIField] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_schema(self) -> UISchema:
        """
        校验顶层字段和页面分组是否完整且一致
        """

        section_field_names: list[str] = []

        for field_name, field in self.fields.items():
            # object 只能作为 list.items，不能直接成为插件参数。
            if field.type == FieldType.OBJECT:
                raise ValueError(f"顶层字段不能使用 object 类型: {field_name}")

            if field.widget is None:
                raise ValueError(f"顶层字段必须声明 widget: {field_name}")

            if not field.label:
                raise ValueError(f"顶层字段必须声明 label: {field_name}")

        for section in self.sections:
            for field_name in section.fields:
                if field_name not in self.fields:
                    raise ValueError(f"section 引用了不存在的字段: {field_name}")

                section_field_names.append(field_name)

        if len(section_field_names) != len(set(section_field_names)):
            raise ValueError("同一个字段不能出现在多个 section 中")

        unsectioned = set(self.fields) - set(section_field_names)
        if unsectioned:
            raise ValueError(f"以下字段没有放入任何 section: {sorted(unsectioned)}")

        return self


__all__ = [
    "UIOption",
    "UIField",
    "UISection",
    "UISchema",
]
