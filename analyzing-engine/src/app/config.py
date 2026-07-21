import tomllib
from pathlib import Path

from src.app.constants import DEFAULT_ENGINE_CONFIG_FILE
from src.app.schemas import EngineConfig


def load_engine_config(
    config_file: str | Path = DEFAULT_ENGINE_CONFIG_FILE,
) -> EngineConfig:
    """
    读取并解析引擎配置文件
    """

    config_file_path = Path(config_file).expanduser().resolve(strict=False)

    if not config_file_path.exists():
        raise FileNotFoundError(f"引擎配置文件不存在: {config_file_path}")

    with config_file_path.open("rb") as fp:
        raw_data = tomllib.load(fp)

    config = EngineConfig.model_validate(raw_data)
    return config.resolve(config_file_path)


__all__ = ["load_engine_config"]
