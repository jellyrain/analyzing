from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from analyzing.contracts.model import AnalyzingModel


class StorageFieldType(str, Enum):
    """
    逻辑字段类型
    """

    # 短文本
    STRING = "string"

    # 长文本
    TEXT = "text"

    # 整数
    INTEGER = "integer"

    # 浮点数
    FLOAT = "float"

    # 布尔值
    BOOLEAN = "boolean"

    # 日期时间
    DATETIME = "datetime"

    # 结构化 JSON
    JSON = "json"


class IndexedField(AnalyzingModel):
    """
    可索引字段声明
    """

    # 字段名
    name: str = Field(min_length=1)

    # 字段逻辑类型
    field_type: StorageFieldType

    # 是否要求写入时提供该字段
    required: bool = False

    # 是否允许该字段值为 None
    nullable: bool = True

    # 字段说明
    description: str = ""


class SchemaIndex(AnalyzingModel):
    """
    逻辑索引声明
    """

    # 索引名，允许存储插件自行生成
    name: str | None = None

    # 索引覆盖的字段列表
    fields: list[str] = Field(default_factory=list, min_length=1)

    # 是否为唯一索引
    unique: bool = False


class NamespaceSchema(AnalyzingModel):
    """
    单个 namespace 的逻辑结构声明
    """

    # 逻辑命名空间，例如 monitor.executions
    namespace: str = Field(min_length=1)

    # 对关系型数据库可以直接作为表名，对文档型数据库可以作为 collection 名
    target_name: str = Field(min_length=1)

    # schema 版本号，用于后续迁移
    version: int = Field(default=1, ge=1)

    # schema 说明
    description: str = ""

    # 可索引字段定义列表
    indexed_fields: list[IndexedField] = Field(default_factory=list)

    # 索引定义列表
    indexes: list[SchemaIndex] = Field(default_factory=list)

    # 是否允许 indexed_values 出现 schema 未声明字段
    allow_extra_indexed_values: bool = False

    @model_validator(mode="after")
    def validate_schema(self) -> "NamespaceSchema":
        """
        校验字段名唯一，且索引引用的字段必须已声明。
        """

        field_names: set[str] = set()
        for field in self.indexed_fields:
            if field.name in field_names:
                raise ValueError(f"schema 字段重复: {field.name}")
            field_names.add(field.name)

        for index in self.indexes:
            for field_name in index.fields:
                if field_name not in field_names:
                    raise ValueError(
                        f"schema 索引引用了未声明字段: "
                        f"namespace={self.namespace}, field={field_name}"
                    )

        return self


__all__ = [
    "IndexedField",
    "NamespaceSchema",
    "SchemaIndex",
    "StorageFieldType",
]