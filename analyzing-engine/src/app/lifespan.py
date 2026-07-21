from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app.schemas import EngineContext


@asynccontextmanager
async def engine_lifespan(app: FastAPI):
    """
    管理引擎生命周期内的共享资源
    """

    yield

    context: EngineContext = app.state.engine
    runtime_manager = context.runtime_manager
    if runtime_manager is not None:
        runtime_manager.shutdown()


__all__ = ["engine_lifespan"]
