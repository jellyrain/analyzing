from fastapi import Request

from src.app.schemas import EngineContext


def get_engine_context(request: Request) -> EngineContext:
    """
    从 FastAPI 应用状态中获取引擎上下文
    """

    return request.app.state.engine


__all__ = ["get_engine_context"]
