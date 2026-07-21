from fastapi import APIRouter

from src.api.host import host_router
from src.api.engine import engine_router

api_router = APIRouter(prefix="/api")
api_router.include_router(host_router)
api_router.include_router(engine_router)

__all__ = ["api_router"]
