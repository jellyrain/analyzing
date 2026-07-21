from fastapi import APIRouter

from src.api.runtime.remote import remote_router

runtime_router = APIRouter(prefix="/runtime", tags=["runtime"])
runtime_router.include_router(remote_router)

__all__ = ["runtime_router"]
