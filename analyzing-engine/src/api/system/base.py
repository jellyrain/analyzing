from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from src.api.deps import get_engine_context
from src.app.schemas import EngineContext
from src.utils.response import APIResponse

base_router = APIRouter()


@base_router.get("/healthz")
def healthz() -> JSONResponse:
    """
    引擎健康检查
    """

    return APIResponse.success_data_to_json(
        {
            "status": "ok",
        }
    )


@base_router.get("/info")
def get_system_info(
    context: EngineContext = Depends(get_engine_context),
) -> JSONResponse:
    """
    返回引擎基础信息
    """

    return APIResponse.success_data_to_json(
        {
            "host_profile": context.host_profile.model_dump(mode="json"),
        }
    )


@base_router.get("/config")
def get_system_config(
    context: EngineContext = Depends(get_engine_context),
) -> JSONResponse:
    """
    返回当前引擎配置
    """

    return APIResponse.success_data_to_json(
        {
            "config": context.config.model_dump(mode="json"),
        }
    )


__all__ = ["base_router"]
