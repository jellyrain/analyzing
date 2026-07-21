from analyzing.monitor.queries import PluginInvocationQuery
from analyzing.plugin.enums.plugin import InvocationStatus
from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from src.api.deps import get_engine_context
from src.app.schemas import EngineContext
from src.utils.response import APIResponse

invocations_monitor_router = APIRouter()


@invocations_monitor_router.get("")
def get_invocations_monitor_snapshot(
    execution_id: str | None = None,
    plugin_id: str | None = None,
    status: InvocationStatus | None = None,
    runtime_mode: str | None = None,
    offset: int = 0,
    limit: int = 50,
    context: EngineContext = Depends(get_engine_context),
) -> JSONResponse:
    """
    返回插件调用监控快照
    """

    service = context.monitor_service
    if service is None:
        return APIResponse.error(message="监控服务尚未初始化")

    items = service.list_plugin_invocations(
        PluginInvocationQuery(
            execution_id=execution_id,
            plugin_id=plugin_id,
            status=status,
            runtime_mode=runtime_mode,
            offset=offset,
            limit=limit,
        )
    )
    return APIResponse.success_data_to_json({"items": items})


__all__ = ["invocations_monitor_router"]
