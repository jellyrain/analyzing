from __future__ import annotations

from typing import Any
from uuid import uuid4

from analyzing.persistence.queries import QueryRequest, QueryResult
from analyzing.persistence.records import (
    DeleteResult,
    PersistenceRecord,
    UpdateResult,
    WriteResult,
)
from analyzing.persistence.remote import (
    PersistenceOperation,
    PersistenceRequest,
    PersistenceResponse,
)
from analyzing.persistence.schema import NamespaceSchema
from analyzing.plugin.errors import PluginInvokeError
from analyzing.runtime.errors import RuntimeProtocolError

from src.runtime.manager import EngineRuntimeManager


class PersistenceServiceProxy:
    """
    通过 engine 已加载的 storage 插件代理 PersistenceService。
    """

    def __init__(
        self,
        runtime_manager: EngineRuntimeManager,
        plugin_id: str,
    ) -> None:
        # 引擎插件运行时管理器
        self.runtime_manager = runtime_manager

        # 当前绑定的 storage 插件 ID
        self.plugin_id = plugin_id

    def _exchange(
        self,
        operation: PersistenceOperation,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        发送一条 persistence 请求并返回响应数据。
        """

        request = PersistenceRequest(
            request_id=uuid4().hex,
            operation=operation,
            payload=payload,
        )

        def validate_response(response: PersistenceResponse) -> None:
            # request_id 不一致说明读到了其他请求遗留的响应，必须废弃该进程。
            if response.request_id != request.request_id:
                raise RuntimeProtocolError(
                    "storage 插件返回了不匹配的 request_id: "
                    f"expected={request.request_id}, actual={response.request_id}"
                )

        response = self.runtime_manager.exchange_subprocess(
            plugin_id=self.plugin_id,
            request=request,
            response_model=PersistenceResponse,
            response_validator=validate_response,
        )

        # 这是插件已经完整返回的业务错误，保留进程即可。
        if not response.ok:
            raise PluginInvokeError(
                response.error_message
                or f"storage 插件调用失败: plugin_id={self.plugin_id}, operation={operation}"
            )

        return response.data

    def ensure_schema(
        self,
        schema: NamespaceSchema,
    ) -> None:
        """
        确保指定 namespace 的底层结构已经就绪。
        """

        self._exchange(
            PersistenceOperation.ENSURE_SCHEMA,
            {
                "schema": schema.model_dump(mode="json"),
            },
        )

    def get_schema(
        self,
        namespace: str,
    ) -> NamespaceSchema | None:
        """
        返回当前已登记的逻辑 schema。
        """

        data = self._exchange(
            PersistenceOperation.GET_SCHEMA,
            {
                "namespace": namespace,
            },
        )
        if not data or data.get("schema") is None:
            return None

        return NamespaceSchema.model_validate(data["schema"])

    def get(
        self,
        namespace: str,
        record_id: str,
    ) -> PersistenceRecord | None:
        """
        按主键读取单条记录。
        """

        data = self._exchange(
            PersistenceOperation.GET,
            {
                "namespace": namespace,
                "record_id": record_id,
            },
        )
        if not data or data.get("record") is None:
            return None

        return PersistenceRecord.model_validate(data["record"])

    def query(
        self,
        request: QueryRequest,
    ) -> QueryResult:
        """
        按统一查询模型检索记录。
        """

        data = self._exchange(
            PersistenceOperation.QUERY,
            {
                "request": request.model_dump(mode="json"),
            },
        )
        return QueryResult.model_validate((data or {}).get("result", {}))

    def create(
        self,
        record: PersistenceRecord,
    ) -> WriteResult:
        """
        创建记录。
        """

        data = self._exchange(
            PersistenceOperation.CREATE,
            {
                "record": record.model_dump(mode="json"),
            },
        )
        return WriteResult.model_validate((data or {}).get("result", {}))

    def update(
        self,
        record: PersistenceRecord,
    ) -> UpdateResult:
        """
        更新记录。
        """

        data = self._exchange(
            PersistenceOperation.UPDATE,
            {
                "record": record.model_dump(mode="json"),
            },
        )
        return UpdateResult.model_validate((data or {}).get("result", {}))

    def delete(
        self,
        namespace: str,
        record_id: str,
    ) -> DeleteResult:
        """
        删除记录。
        """

        data = self._exchange(
            PersistenceOperation.DELETE,
            {
                "namespace": namespace,
                "record_id": record_id,
            },
        )
        return DeleteResult.model_validate((data or {}).get("result", {}))

    def upsert(
        self,
        record: PersistenceRecord,
    ) -> WriteResult | UpdateResult:
        """
        不区分新增或更新的写入操作。
        """

        data = self._exchange(
            PersistenceOperation.UPSERT,
            {
                "record": record.model_dump(mode="json"),
            },
        )

        raw_result = (data or {}).get("result", {})
        if raw_result.get("created") is not None:
            return WriteResult.model_validate(raw_result)

        return UpdateResult.model_validate(raw_result)


__all__ = ["PersistenceServiceProxy"]
