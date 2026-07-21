from fastapi import APIRouter

from src.api.system.base import base_router

system_router = APIRouter(prefix="/system", tags=["system"])
system_router.include_router(base_router)

__all__ = ["system_router"]
