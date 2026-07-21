from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from analyzing.contracts.model import AnalyzingModel


class PersistenceOperation(str, Enum):
    """
    sidecar/subprocess 存储操作类型
    """

    # 创建记录
    CREATE = "create"

    # 读取单条记录
    GET = "get"

    # 查询记录
    QUERY = "query"

    # 更新记录
    UPDATE = "update"

    # 删除记录
    DELETE = "delete"

    # 插入或更新记录
    UPSERT = "upsert"

    # 确保逻辑 schema 已落地
    ENSURE_SCHEMA = "ensure_schema"

    # 读取当前已登记 schema
    GET_SCHEMA = "get_schema"


class PersistenceRequest(AnalyzingModel):
    """
    发给 persistence 插件进程的统一请求
    """

    # 请求唯一标识，用于请求响应配对
    request_id: str = Field(min_length=1)

    # 本次请求要执行的存储操作
    operation: PersistenceOperation

    # 请求负载，具体结构由 operation 约定
    payload: dict[str, Any] = Field(default_factory=dict)


class PersistenceResponse(AnalyzingModel):
    """
    persistence 插件进程返回的统一响应
    """

    # 本次请求是否成功
    ok: bool

    # 对应的请求标识
    request_id: str = Field(min_length=1)

    # 成功时返回的数据内容
    data: dict[str, Any] | None = None

    # 失败时返回的错误码
    error_code: str | None = None

    # 失败时返回的错误描述
    error_message: str | None = None


__all__ = [
    "PersistenceOperation",
    "PersistenceRequest",
    "PersistenceResponse",
]