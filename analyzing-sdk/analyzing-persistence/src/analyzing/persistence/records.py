from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from analyzing.contracts.model import AnalyzingModel


class PersistenceRecord(AnalyzingModel):
    """
    通用存储记录
    """

    # 记录所属逻辑命名空间，用于隔离不同领域的数据
    namespace: str = Field(min_length=1)

    # 记录唯一标识
    record_id: str = Field(min_length=1)

    # 完整业务负载，通常以 JSON 形式整体存储
    payload: dict[str, Any] = Field(default_factory=dict)

    # 供存储插件结构化落库的索引字段值
    # 这里的 key 应与该 namespace 对应 schema 中声明的 indexed field 一致
    indexed_values: dict[str, Any] = Field(default_factory=dict)

    # 记录创建时间
    created_at: datetime | None = None

    # 记录最近更新时间
    updated_at: datetime | None = None

    # 记录版本号，可用于乐观锁或迁移追踪
    version: int | None = Field(default=None, ge=0)

    # 记录标签，便于轻量分类
    tags: list[str] = Field(default_factory=list)

class WriteResult(AnalyzingModel):
    """
    创建或写入结果
    """

    # 本次写入是否成功
    ok: bool

    # 本次写入对应的记录标识
    record_id: str = Field(min_length=1)

    # 是否为新建记录
    created: bool = False


class UpdateResult(AnalyzingModel):
    """
    更新结果
    """

    # 本次更新是否成功
    ok: bool

    # 本次更新对应的记录标识
    record_id: str = Field(min_length=1)

    # 是否确实发生了更新
    updated: bool = False


class DeleteResult(AnalyzingModel):
    """
    删除结果
    """

    # 本次删除是否成功
    ok: bool

    # 本次删除对应的记录标识
    record_id: str = Field(min_length=1)

    # 是否确实删除了目标记录
    deleted: bool = False


__all__ = [
    "PersistenceRecord",
    "WriteResult",
    "UpdateResult",
    "DeleteResult",
]