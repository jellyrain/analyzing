from analyzing.monitor.queries import PluginStatusQuery
from analyzing.plugin.enums.plugin import InstallStatus, RuntimeStatus
from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from src.api.deps import get_engine_context
from src.app.schemas import EngineContext
from src.utils.response import APIResponse

plugins_monitor_router = APIRouter()


@plugins_monitor_router.get("")
def get_plugins_monitor_snapshot(
    plugin_id: str | None = None,
    install_status: InstallStatus | None = None,
    runtime_status: RuntimeStatus | None = None,
    offset: int = 0,
    limit: int = 50,
    context: EngineContext = Depends(get_engine_context),
) -> JSONResponse:
    """
    返回插件运行监控快照
    """

    service = context.monitor_service
    if service is None:
        return APIResponse.error(message="监控服务尚未初始化")

    items = service.list_plugin_status(
        PluginStatusQuery(
            plugin_id=plugin_id,
            install_status=install_status,
            runtime_status=runtime_status,
            offset=offset,
            limit=limit,
        )
    )
    return APIResponse.success_data_to_json({"items": items})


__all__ = ["plugins_monitor_router"]
