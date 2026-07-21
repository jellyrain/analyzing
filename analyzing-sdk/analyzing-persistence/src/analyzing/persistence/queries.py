from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from analyzing.contracts.model import AnalyzingModel
from analyzing.persistence.records import PersistenceRecord


class QueryFilterOperator(str, Enum):
    """
    通用过滤操作符
    """

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    CONTAINS = "contains"


class SortDirection(str, Enum):
    """
    排序方向
    """

    ASC = "asc"
    DESC = "desc"


class QueryFieldSource(str, Enum):
    """
    查询字段来源
    """

    # 记录基础列，例如 record_id / created_at / updated_at / version
    RECORD = "record"

    # indexed_values 中声明的结构化字段
    INDEXED = "indexed"


class QueryFilter(AnalyzingModel):
    """
    单条过滤条件
    """

    # 过滤字段名
    field: str = Field(min_length=1)

    # 字段来源，默认查 indexed_values
    source: QueryFieldSource = QueryFieldSource.INDEXED

    # 过滤运算符
    operator: QueryFilterOperator

    # 过滤比较值
    value: Any


class QuerySort(AnalyzingModel):
    """
    单条排序规则
    """

    # 排序字段名
    field: str = Field(min_length=1)

    # 字段来源，默认按 indexed_values 排序
    source: QueryFieldSource = QueryFieldSource.INDEXED

    # 排序方向
    direction: SortDirection = SortDirection.ASC


class PageRequest(AnalyzingModel):
    """
    分页请求
    """

    # 查询起始偏移量
    offset: int = Field(default=0, ge=0)

    # 单页返回数量上限
    limit: int = Field(default=50, ge=1)


class PageResult(AnalyzingModel):
    """
    分页结果
    """

    # 本次结果对应的起始偏移量
    offset: int = Field(default=0, ge=0)

    # 本次结果对应的分页大小
    limit: int = Field(default=50, ge=1)

    # 符合条件的总记录数
    total: int = Field(default=0, ge=0)


class QueryRequest(AnalyzingModel):
    """
    统一查询请求
    """

    # 查询目标命名空间
    namespace: str = Field(min_length=1)

    # 过滤条件列表
    filters: list[QueryFilter] = Field(default_factory=list)

    # 排序规则列表
    sorts: list[QuerySort] = Field(default_factory=list)

    # 分页参数，None 表示不分页
    page: PageRequest | None = None


class QueryResult(AnalyzingModel):
    """
    统一查询结果
    """

    # 查询返回的记录列表
    items: list[PersistenceRecord] = Field(default_factory=list)

    # 查询返回的分页信息；不分页时允许为 None
    page: PageResult | None = None


__all__ = [
    "PageRequest",
    "PageResult",
    "QueryFieldSource",
    "QueryFilter",
    "QueryFilterOperator",
    "QueryRequest",
    "QueryResult",
    "QuerySort",
    "SortDirection",
]