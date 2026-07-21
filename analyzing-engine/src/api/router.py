from fastapi import APIRouter

from src.api.monitor.router import monitor_router
from src.api.processor.router import pipeline_router
from src.api.plugins.router import plugin_router
from src.api.runtime.router import runtime_router
from src.api.system.router import system_router

api_router = APIRouter(prefix="/api")
api_router.include_router(system_router)
api_router.include_router(plugin_router)
api_router.include_router(runtime_router)
api_router.include_router(pipeline_router)
api_router.include_router(monitor_router)

__all__ = ["api_router"]
