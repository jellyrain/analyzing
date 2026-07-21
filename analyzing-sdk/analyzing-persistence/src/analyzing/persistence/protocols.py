from __future__ import annotations

from typing import Protocol, runtime_checkable

from analyzing.persistence.queries import QueryRequest, QueryResult
from analyzing.persistence.records import (
    DeleteResult,
    PersistenceRecord,
    UpdateResult,
    WriteResult,
)
from analyzing.persistence.schema import NamespaceSchema


@runtime_checkable
class PersistenceSchemaManager(Protocol):
    """
    schema 管理能力

    由具体存储插件负责根据逻辑 schema 建立底层表结构和索引
    """

    def ensure_schema(
        self,
        schema: NamespaceSchema,
    ) -> None:
        """
        确保指定 namespace 的底层结构已经就绪
        """

        ...

    def get_schema(
        self,
        namespace: str,
    ) -> NamespaceSchema | None:
        """
        返回当前已登记的逻辑 schema
        """

        ...


@runtime_checkable
class PersistenceReader(Protocol):
    """
    只读能力面
    """

    def get(
        self,
        namespace: str,
        record_id: str,
    ) -> PersistenceRecord | None:
        """
        按主键读取单条记录
        """

        ...

    def query(
        self,
        request: QueryRequest,
    ) -> QueryResult:
        """
        按统一查询模型检索记录
        """

        ...


@runtime_checkable
class PersistenceWriter(Protocol):
    """
    写能力面
    """

    def create(
        self,
        record: PersistenceRecord,
    ) -> WriteResult:
        """
        创建记录
        """

        ...

    def update(
        self,
        record: PersistenceRecord,
    ) -> UpdateResult:
        """
        更新记录
        """

        ...

    def delete(
        self,
        namespace: str,
        record_id: str,
    ) -> DeleteResult:
        """
        删除记录
        """

        ...

    def upsert(
        self,
        record: PersistenceRecord,
    ) -> WriteResult | UpdateResult:
        """
        不区分新增或更新的写入操作
        """

        ...


@runtime_checkable
class PersistenceService(
    PersistenceSchemaManager,
    PersistenceReader,
    PersistenceWriter,
    Protocol,
):
    """
    统一存储服务协议

    具体数据库插件负责：
    - schema 落地
    - indexed_values 结构化存储
    - payload 的完整保存
    """


__all__ = [
    "PersistenceReader",
    "PersistenceSchemaManager",
    "PersistenceService",
    "PersistenceWriter",
]