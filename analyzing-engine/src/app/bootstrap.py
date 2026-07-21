import json
import platform
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

import uvicorn
from analyzing.compat.host import HostProfile, SDKDistribution, HostFeatures
from analyzing.monitor.service import MonitorService
from analyzing.monitor.tracker import MonitorTracker
from analyzing.runtime.mode import RuntimeMode
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from src.app.static.docs import configure_local_docs
from infra.access_logging import build_access_log_middleware
from src.api.router import api_router
from src.app.config import load_engine_config
from src.app.constants import DEFAULT_ENGINE_CONFIG_FILE, PROJECT_ROOT_DIR
from src.app.lifespan import engine_lifespan
from src.app.schemas import EngineContext, EngineConfig
from src.infra.monitoring import (
    record_host_snapshot,
    record_system_snapshot,
    sync_plugin_catalog_statuses,
)
from src.infra.persistence import PersistenceServiceProxy
from src.install.rain import sync_rain_plugins
from src.registry.catalog import build_plugin_catalog, ensure_no_infra_slot_conflicts
from src.runtime.manager import EngineRuntimeManager

_HOST_PROFILE_FILE_NAME = "host_profile.json"


def _load_host_profile_file(
    file_path: str | Path,
) -> HostProfile:
    """
    从宿主快照 JSON 文件读取 HostProfile
    """

    resolved_file_path = Path(file_path).expanduser().resolve(strict=False)
    if not resolved_file_path.is_file():
        raise FileNotFoundError(f"未找到宿主快照文件: {resolved_file_path}")

    raw_data = json.loads(resolved_file_path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, dict):
        raise ValueError(f"宿主快照文件顶层必须是对象: {resolved_file_path}")

    return HostProfile.model_validate(raw_data)


def _ensure_engine_directories(config: EngineConfig) -> None:
    """
    确保引擎运行所需目录存在
    """

    if config.paths.data_dir_path is not None:
        config.paths.data_dir_path.mkdir(parents=True, exist_ok=True)

    if config.paths.logs_dir_path is not None:
        config.paths.logs_dir_path.mkdir(parents=True, exist_ok=True)

    if config.paths.plugins_dir_path is not None:
        config.paths.plugins_dir_path.mkdir(parents=True, exist_ok=True)

    if config.paths.runtime_plugins_dir_path is not None:
        config.paths.runtime_plugins_dir_path.mkdir(parents=True, exist_ok=True)


def _safe_package_version(package_name: str) -> str:
    """
    安全获取已安装包版本，取不到时返回 unknown
    """

    try:
        return version(package_name)
    except PackageNotFoundError:
        return "unknown"


def _resolve_host_profile_snapshot_file() -> Path:
    """
    返回宿主快照文件路径。
    """

    return PROJECT_ROOT_DIR / _HOST_PROFILE_FILE_NAME


def _build_runtime_host_profile() -> HostProfile:
    """
    按旧逻辑动态构建当前引擎画像。
    """

    return HostProfile(
        host_version="1.0.0",
        sdk_version=_safe_package_version("analyzing-plugin"),
        python_version=platform.python_version(),
        supported_runtime_modes=[
            RuntimeMode.INPROC,
            RuntimeMode.SUBPROCESS,
            RuntimeMode.REMOTE,
        ],
        plugin_package_suffix=".rain",
        features=HostFeatures(
            field_mapping=True,
            plugin_rescan=True,
            supports_output_flatten=True,
            service_mode=True,
        ),
        baseline_dependencies={
            "analyzing-plugin": _safe_package_version("analyzing-plugin"),
            "analyzing-monitor": _safe_package_version("analyzing-monitor"),
            "analyzing-persistence": _safe_package_version("analyzing-persistence"),
            "analyzing-compat": _safe_package_version("analyzing-compat"),
            "fastapi": _safe_package_version("fastapi"),
            "uvicorn": _safe_package_version("uvicorn"),
            "httpx": _safe_package_version("httpx"),
        },
        sdk_distribution=SDKDistribution(
            channel="private",
            public_pypi=False,
            format="wheel",
        ),
    )


def _build_host_profile() -> HostProfile:
    """
    优先读取构建期宿主快照，读不到时回退到运行时探测。
    """

    snapshot_file_path = _resolve_host_profile_snapshot_file()
    if snapshot_file_path.is_file():
        try:
            return _load_host_profile_file(snapshot_file_path)
        except Exception as exc:
            print(
                "[engine.host_profile] 宿主快照读取失败，回退运行时探测: "
                f"{snapshot_file_path}, reason={exc}"
            )

    return _build_runtime_host_profile()


def create_engine_context(
    config_file: str = str(DEFAULT_ENGINE_CONFIG_FILE),
) -> EngineContext:
    """
    创建引擎运行时上下文
    """

    config = load_engine_config(config_file)
    _ensure_engine_directories(config)
    sync_result = sync_rain_plugins(config)
    for warning in sync_result.warnings:
        print(f"[engine.rain] {warning}")

    host_profile = _build_host_profile()
    plugin_catalog = build_plugin_catalog(config, host_profile)
    ensure_no_infra_slot_conflicts(plugin_catalog)
    runtime_manager = EngineRuntimeManager(plugin_catalog=plugin_catalog)

    persistence = PersistenceServiceProxy(
        runtime_manager=runtime_manager,
        plugin_id=config.infra.storage.plugin_id,
    )
    monitor_tracker = MonitorTracker(persistence)
    monitor_service = MonitorService(persistence)

    monitor_tracker.ensure_ready()
    runtime_manager.monitor_tracker = monitor_tracker
    runtime_manager.preload_startup_plugins()
    sync_plugin_catalog_statuses(monitor_tracker, plugin_catalog)
    record_system_snapshot(monitor_tracker, plugin_catalog)
    record_host_snapshot(
        monitor_tracker,
        host_profile,
        root_dir_path=config.root_dir_path,
    )

    return EngineContext(
        config=config,
        host_profile=host_profile,
        plugin_catalog=plugin_catalog,
        runtime_manager=runtime_manager,
        persistence=persistence,
        monitor_tracker=monitor_tracker,
        monitor_service=monitor_service,
    )


def create_engine_app(
    config_file: str = str(DEFAULT_ENGINE_CONFIG_FILE),
) -> FastAPI:
    """
    创建引擎 FastAPI 应用
    """

    context = create_engine_context(config_file)

    app = FastAPI(
        title="Analyzing Engine",
        version=context.host_profile.host_version,
        lifespan=engine_lifespan,
        docs_url=None,
    )

    # 挂载本地静态文件目录
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # 挂载 Swagger
    configure_local_docs(app, static_dir=Path("static"))

    # 将引擎上下文挂到 app.state，后续 API、插件注册表、运行时都从这里取
    app.state.engine = context

    if context.monitor_tracker is not None:
        app.middleware("http")(build_access_log_middleware(context.monitor_tracker))

    app.include_router(api_router)

    return app


def run(
    config_file: str = str(DEFAULT_ENGINE_CONFIG_FILE),
) -> None:
    """
    启动引擎 API
    """

    app = create_engine_app(config_file)
    context = app.state.engine

    uvicorn.run(
        app=app,
        host=context.config.server.host,
        port=context.config.server.port,
    )


__all__ = ["create_engine_context", "create_engine_app", "run"]
