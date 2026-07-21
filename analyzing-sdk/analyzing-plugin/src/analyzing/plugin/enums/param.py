from enum import StrEnum


class ParamType(StrEnum):
    """
    参数类型
    """

    # 单行字符串
    STRING = "string"

    # 多行文本
    TEXT = "text"

    # 整数
    INT = "int"

    # 浮点数
    FLOAT = "float"

    # 布尔值
    BOOL = "bool"

    # 枚举项
    ENUM = "enum"

    # 字符串列表
    STRING_LIST = "string_list"

    # 键值对
    KEY_VALUE = "key_value"

    # JSON 对象
    JSON = "json"

    # 文件路径
    FILE = "file"

    # 目录路径
    DIRECTORY = "directory"


class ExecutionStatus(StrEnum):
    """
    执行状态
    """

    # 已创建，尚未开始执行
    CREATED = "created"

    # 执行中
    RUNNING = "running"

    # 执行成功
    SUCCEEDED = "succeeded"

    # 执行失败
    FAILED = "failed"

    # 已取消
    CANCELED = "canceled"


__all__ = ["ParamType", "ExecutionStatus"]
