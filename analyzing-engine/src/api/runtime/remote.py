from analyzing.plugin.remote import (
    RemoteRegisterResponse,
    RemoteRegisterRequest,
    RemoteHeartbeatResponse,
    RemoteHeartbeatRequest,
    RemoteUnregisterRequest,
)
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status


from src.api.deps import get_engine_context
from src.app.schemas import EngineContext

remote_router = APIRouter(prefix="/remote", tags=["remote"])


@remote_router.post("/register", response_model=RemoteRegisterResponse)
def register_remote_plugin(
    payload: RemoteRegisterRequest,
    request: Request,
    context: EngineContext = Depends(get_engine_context),
) -> RemoteRegisterResponse:
    """
    remote 插件注册接口
    """

    runtime_manager = context.runtime_manager
    if runtime_manager is None:
        raise HTTPException(status_code=503, detail="引擎运行时未初始化")

    return runtime_manager.register_remote_plugin(
        payload,
        host_profile=context.host_profile,
        allow_anonymous_remote=context.config.remote.allow_anonymous_remote,
        authorization=request.headers.get("Authorization"),
        shared_token=context.config.remote.shared_token,
        runtime_plugins_dir_path=context.config.paths.runtime_plugins_dir_path,
    )


@remote_router.post("/heartbeat", response_model=RemoteHeartbeatResponse)
def remote_plugin_heartbeat(
    payload: RemoteHeartbeatRequest,
    context: EngineContext = Depends(get_engine_context),
) -> RemoteHeartbeatResponse:
    """
    remote 插件心跳接口
    """

    runtime_manager = context.runtime_manager
    if runtime_manager is None:
        raise HTTPException(status_code=503, detail="引擎运行时未初始化")

    return runtime_manager.heartbeat_remote_plugin(payload)


@remote_router.post("/unregister", status_code=status.HTTP_204_NO_CONTENT)
def unregister_remote_plugin(
    payload: RemoteUnregisterRequest,
    context: EngineContext = Depends(get_engine_context),
) -> Response:
    """
    remote 插件注销接口
    """

    runtime_manager = context.runtime_manager
    if runtime_manager is None:
        raise HTTPException(status_code=503, detail="引擎运行时未初始化")

    runtime_manager.unregister_remote_plugin(payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["remote_router"]
