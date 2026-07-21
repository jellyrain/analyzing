from analyzing.monitor.queries import HostSnapshotQuery, SystemSnapshotQuery
from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from src.api.deps import get_engine_context
from src.app.schemas import EngineContext
from src.utils.response import APIResponse

system_monitor_router = APIRouter()


@system_monitor_router.get("")
def get_system_monitor_snapshot(
    limit: int = 20,
    context: EngineContext = Depends(get_engine_context),
) -> JSONResponse:
    """
    返回引擎系统监控快照
    """

    service = context.monitor_service
    if service is None:
        return APIResponse.error(message="监控服务尚未初始化")

    system_items = service.list_system_snapshots(
        SystemSnapshotQuery(offset=0, limit=limit)
    )
    host_items = service.list_host_snapshots(HostSnapshotQuery(offset=0, limit=limit))

    return APIResponse.success_data_to_json(
        {
            "latest_system": service.latest_system_snapshot(),
            "latest_host": service.latest_host_snapshot(),
            "system_items": system_items,
            "host_items": host_items,
        }
    )


__all__ = ["system_monitor_router"]
