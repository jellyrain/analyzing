import httpx
from fastapi import APIRouter, Response, HTTPException, status
from pydantic import BaseModel

from src.config.host_config import (
    save_host_config,
    delete_host_config,
    load_host_config,
    HostConfig,
)

host_router = APIRouter(prefix="/host")


class BootstrapResponse(BaseModel):
    configured: bool
    engine_origin: str | None = None


class ConnectionTestResponse(BaseModel):
    ok: bool
    engine_origin: str
    status_code: int | None = None
    message: str


@host_router.get("/bootstrap", response_model=BootstrapResponse)
async def get_bootstrap() -> BootstrapResponse:
    config = load_host_config()

    if config is None:
        return BootstrapResponse(configured=False)

    return BootstrapResponse(
        configured=True,
        engine_origin=config.engine_origin,
    )


@host_router.get("/config", response_model=HostConfig)
async def get_host_config() -> HostConfig:
    config = load_host_config()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="本地 Web 配置不存在",
        )

    return config


@host_router.put("/config", response_model=HostConfig)
async def update_host_config(config: HostConfig) -> HostConfig:
    save_host_config(config)
    return config


@host_router.delete("/config", status_code=status.HTTP_204_NO_CONTENT)
async def remove_host_config() -> Response:
    delete_host_config()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@host_router.post("/config/test", response_model=ConnectionTestResponse)
async def test_host_config(config: HostConfig) -> ConnectionTestResponse:
    try:
        async with httpx.AsyncClient(
            base_url=config.engine_origin,
            timeout=10.0,
        ) as client:
            response = await client.get("/api/system/info")
    except httpx.RequestError as exc:
        return ConnectionTestResponse(
            ok=False,
            engine_origin=config.engine_origin,
            message=f"无法连接 Engine: {exc}",
        )

    if response.is_success:
        return ConnectionTestResponse(
            ok=True,
            engine_origin=config.engine_origin,
            status_code=response.status_code,
            message="Engine 连接成功",
        )

    return ConnectionTestResponse(
        ok=False,
        engine_origin=config.engine_origin,
        status_code=response.status_code,
        message="Engine 返回异常状态",
    )


@host_router.get("/health")
async def get_host_health() -> dict[str, str]:
    return {"status": "ok"}


__all__ = ["host_router"]
