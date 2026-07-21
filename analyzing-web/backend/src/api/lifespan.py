from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 复用到 Engine 的 HTTP 连接，避免监控轮询反复建连。
    app.state.engine_http = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=False,
    )
    yield
    await app.state.engine_http.aclose()


__all__ = ["lifespan"]
