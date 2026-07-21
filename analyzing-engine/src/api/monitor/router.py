from fastapi import APIRouter

from src.api.monitor.access import access_monitor_router
from src.api.monitor.invocations import invocations_monitor_router
from src.api.monitor.overview import overview_monitor_router
from src.api.monitor.plugins import plugins_monitor_router
from src.api.monitor.system import system_monitor_router

monitor_router = APIRouter(prefix="/monitor", tags=["monitor"])
monitor_router.include_router(system_monitor_router, prefix="/system")
monitor_router.include_router(plugins_monitor_router, prefix="/plugins")
monitor_router.include_router(invocations_monitor_router, prefix="/invocations")
monitor_router.include_router(access_monitor_router, prefix="/access")
monitor_router.include_router(overview_monitor_router, prefix="/overview")

__all__ = ["monitor_router"]
