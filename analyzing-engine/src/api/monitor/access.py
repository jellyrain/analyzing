from datetime import datetime

from analyzing.monitor.queries import AccessLogQuery
from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from src.api.deps import get_engine_context
from src.app.schemas import EngineContext
from src.utils.response import APIResponse

access_monitor_router = APIRouter()


@access_monitor_router.get("")
def get_access_monitor_snapshot(
    method: str | None = None,
    path: str | None = None,
    status_code: int | None = None,
    client_ip: str | None = None,
    trace_id: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    offset: int = 0,
    limit: int = 50,
    context: EngineContext = Depends(get_engine_context),
) -> JSONResponse:
    """
    返回引擎 API 调用监控快照
    """

    service = context.monitor_service
    if service is None:
        return APIResponse.error(message="监控服务尚未初始化")

    items = service.list_access_logs(
        AccessLogQuery(
            method=method,
            path=path,
            status_code=status_code,
            client_ip=client_ip,
            trace_id=trace_id,
            created_from=created_from,
            created_to=created_to,
            offset=offset,
            limit=limit,
        )
    )
    return APIResponse.success_data_to_json({"items": items})


__all__ = ["access_monitor_router"]
