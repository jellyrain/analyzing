import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from src.config.host_config import load_host_config

ENGINE_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

engine_router = APIRouter(prefix="/engine")


class HostNotConfiguredError(RuntimeError):
    """
    Web Host 尚未完成本地 Engine 连接配置。
    """


def get_engine_origin() -> str:
    config = load_host_config()
    if config is None:
        raise HostNotConfiguredError("尚未完成本地 Engine 连接配置")

    return config.engine_origin


@engine_router.api_route(
    "/{path:path}", methods=ENGINE_METHODS, include_in_schema=False
)
async def proxy_engine(path: str, request: Request) -> Response:
    try:
        engine_origin = get_engine_origin().rstrip("/")

        headers: dict[str, str] = {}

        content_type = request.headers.get("content-type")
        if content_type:
            headers["content-type"] = content_type

        client: httpx.AsyncClient = request.app.state.engine_http

        response = await client.request(
            method=request.method,
            url=f"{engine_origin}/api/{path}",
            params=request.query_params,
            content=await request.body(),
            headers=headers,
        )
    except HostNotConfiguredError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="无法连接 Engine",
        ) from exc

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type"),
    )


__all__ = ["engine_router"]
