from __future__ import annotations

from typing import Any

from analyzing.persistence.queries import (
    PageRequest,
    QueryFieldSource,
    QueryFilter,
    QueryFilterOperator,
    QuerySort,
    SortDirection,
)


def build_page(
    offset: int,
    limit: int,
) -> PageRequest:
    """
    构造分页请求
    """

    return PageRequest(offset=offset, limit=limit)


def field_eq(
    field: str,
    value: Any,
    *,
    source: QueryFieldSource,
) -> QueryFilter | None:
    """
    构造等值过滤条件
    """

    if value is None:
        return None

    return QueryFilter(
        field=field,
        source=source,
        operator=QueryFilterOperator.EQ,
        value=value,
    )


def field_gte(
    field: str,
    value: Any,
    *,
    source: QueryFieldSource,
) -> QueryFilter | None:
    """
    构造大于等于过滤条件
    """

    if value is None:
        return None

    return QueryFilter(
        field=field,
        source=source,
        operator=QueryFilterOperator.GTE,
        value=value,
    )


def field_lte(
    field: str,
    value: Any,
    *,
    source: QueryFieldSource,
) -> QueryFilter | None:
    """
    构造小于等于过滤条件
    """

    if value is None:
        return None

    return QueryFilter(
        field=field,
        source=source,
        operator=QueryFilterOperator.LTE,
        value=value,
    )


def field_sort(
    field: str,
    direction: SortDirection,
    *,
    source: QueryFieldSource,
) -> QuerySort:
    """
    构造排序规则
    """

    return QuerySort(
        field=field,
        source=source,
        direction=direction,
    )


def indexed_eq(
    field: str,
    value: Any,
) -> QueryFilter | None:
    """
    构造 indexed field 的等值过滤条件
    """

    return field_eq(
        field,
        value,
        source=QueryFieldSource.INDEXED,
    )


def indexed_gte(
    field: str,
    value: Any,
) -> QueryFilter | None:
    """
    构造 indexed field 的大于等于过滤条件
    """

    return field_gte(
        field,
        value,
        source=QueryFieldSource.INDEXED,
    )


def indexed_lte(
    field: str,
    value: Any,
) -> QueryFilter | None:
    """
    构造 indexed field 的小于等于过滤条件
    """

    return field_lte(
        field,
        value,
        source=QueryFieldSource.INDEXED,
    )


def indexed_sort(
    field: str,
    direction: SortDirection,
) -> QuerySort:
    """
    构造 indexed field 的排序规则
    """

    return field_sort(
        field,
        direction,
        source=QueryFieldSource.INDEXED,
    )


def record_eq(
    field: str,
    value: Any,
) -> QueryFilter | None:
    """
    构造记录基础列的等值过滤条件
    """

    return field_eq(
        field,
        value,
        source=QueryFieldSource.RECORD,
    )


def record_gte(
    field: str,
    value: Any,
) -> QueryFilter | None:
    """
    构造记录基础列的大于等于过滤条件
    """

    return field_gte(
        field,
        value,
        source=QueryFieldSource.RECORD,
    )


def record_lte(
    field: str,
    value: Any,
) -> QueryFilter | None:
    """
    构造记录基础列的小于等于过滤条件
    """

    return field_lte(
        field,
        value,
        source=QueryFieldSource.RECORD,
    )


def record_sort(
    field: str,
    direction: SortDirection,
) -> QuerySort:
    """
    构造记录基础列的排序规则
    """

    return field_sort(
        field,
        direction,
        source=QueryFieldSource.RECORD,
    )


__all__ = [
    "build_page",
    "field_eq",
    "field_gte",
    "field_lte",
    "field_sort",
    "indexed_eq",
    "indexed_gte",
    "indexed_lte",
    "indexed_sort",
    "record_eq",
    "record_gte",
    "record_lte",
    "record_sort",
]