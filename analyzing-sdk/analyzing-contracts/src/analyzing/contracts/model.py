from pydantic import BaseModel, ConfigDict


class AnalyzingModel(BaseModel):
    """
    所有长期契约模型的基础类
    """

    model_config = ConfigDict(
        # 禁止出现未声明字段
        extra="forbid",
        # 允许按字段别名进行填充
        populate_by_name=True,
        # 序列化时直接输出枚举值，而不是枚举对象
        use_enum_values=True,
    )


__all__ = ["AnalyzingModel"]
