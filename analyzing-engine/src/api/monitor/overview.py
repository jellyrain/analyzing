from analyzing.monitor.queries import PluginInvocationQuery, PluginStatusQuery
from analyzing.plugin.enums.plugin import RuntimeStatus
from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from src.api.deps import get_engine_context
from src.app.schemas import EngineContext
from src.utils.response import APIResponse

overview_monitor_router = APIRouter()


@overview_monitor_router.get("")
def get_monitor_overview(
    context: EngineContext = Depends(get_engine_context),
) -> JSONResponse:
    """
    返回监控总览
    """

    service = context.monitor_service
    if service is None:
        return APIResponse.error(message="监控服务尚未初始化")

    latest_system = service.latest_system_snapshot()
    latest_host = service.latest_host_snapshot()
    plugin_items = service.list_plugin_status(PluginStatusQuery(offset=0, limit=200))
    recent_invocations = service.list_plugin_invocations(
        PluginInvocationQuery(offset=0, limit=20)
    )
    ready_statuses = {
        RuntimeStatus.READY,
        RuntimeStatus.LOADED,
        RuntimeStatus.REGISTERED,
    }

    return APIResponse.success_data_to_json(
        {
            "system": {
                "latest_system": latest_system,
                "latest_host": latest_host,
            },
            "plugins": {
                "count": len(plugin_items),
                "ready_count": sum(
                    1 for item in plugin_items if item.runtime_status in ready_statuses
                ),
                "error_count": sum(
                    1
                    for item in plugin_items
                    if item.runtime_status == RuntimeStatus.ERROR
                ),
                "items": plugin_items,
            },
            "invocations": {
                "recent": recent_invocations,
            },
            "access": {
                "supported": False,
                "message": "access 监控领域尚未接入",
            },
        }
    )


__all__ = ["overview_monitor_router"]
