from pathlib import Path
from urllib.parse import urlparse

import tomlkit
from platformdirs import user_config_path
from pydantic import BaseModel, Field, field_validator


class HostConfig(BaseModel):
    """
    Web Host 自己的本地配置，不属于 Engine 配置
    """

    # engine 的根地址
    engine_origin: str
    # 运行监控页面的默认轮询间隔
    monitor_refresh_seconds: int = Field(default=5, ge=1, le=3600)

    @field_validator("engine_origin")
    @classmethod
    def normalize_engine_origin(cls, value: str) -> str:
        origin = value.strip().rstrip("/")
        parsed = urlparse(origin)

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("engine_origin 必须是有效的 http/https 地址")

        return origin


def get_config_file_path() -> Path:
    config_dir = Path("config")
    return config_dir / "web.toml"


def load_host_config() -> HostConfig | None:
    config_file = get_config_file_path()

    if not config_file.exists():
        return None

    document = tomlkit.parse(config_file.read_text(encoding="utf-8"))
    engine_section = document.get("engine", {})
    ui_section = document.get("ui", {})

    return HostConfig(
        engine_origin=str(engine_section["origin"]),
        monitor_refresh_seconds=int(ui_section.get("monitor_refresh_seconds", 5)),
    )


def save_host_config(config: HostConfig) -> None:
    config_file = get_config_file_path()

    document = {
        "engine": {
            "origin": config.engine_origin,
        },
        "ui": {
            "monitor_refresh_seconds": config.monitor_refresh_seconds,
        },
    }

    temporary_file = config_file.with_suffix(".tmp")
    temporary_file.write_text(tomlkit.dumps(document), encoding="utf-8")
    temporary_file.replace(config_file)


def delete_host_config() -> None:
    get_config_file_path().unlink(missing_ok=True)


__all__ = [
    "HostConfig",
    "get_config_file_path",
    "load_host_config",
    "save_host_config",
    "delete_host_config",
]
