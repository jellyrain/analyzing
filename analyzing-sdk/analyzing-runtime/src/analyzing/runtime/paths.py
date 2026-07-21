# 当前约定的插件角色目录
from pathlib import Path

from analyzing.runtime.errors import RuntimeLoadError

_PLUGIN_ROLE_DIR_NAMES = frozenset({"infra", "biz"})

def resolve_host_root_dir(plugin_dir: str | Path) -> Path:
    """
    根据插件安装目录反推出宿主根目录。
    """

    plugin_dir_path = Path(plugin_dir).expanduser().resolve(strict=False)
    role_dir_path = plugin_dir_path.parent
    plugins_dir_path = role_dir_path.parent
    data_dir_path = plugins_dir_path.parent

    if role_dir_path.name not in _PLUGIN_ROLE_DIR_NAMES:
        raise RuntimeLoadError(
            f"插件目录结构不符合约定，未找到 role 目录: {plugin_dir_path}"
        )

    if plugins_dir_path.name != "plugins":
        raise RuntimeLoadError(
            f"插件目录结构不符合约定，未找到 plugins 目录: {plugin_dir_path}"
        )

    if data_dir_path.name != "data":
        raise RuntimeLoadError(
            f"插件目录结构不符合约定，未找到 data 目录: {plugin_dir_path}"
        )

    return data_dir_path.parent.resolve(strict=False)


def try_resolve_host_root_dir(plugin_dir: str | Path) -> Path | None:
    """
    尝试根据插件安装目录反推出宿主根目录，失败时返回 None，便于插件做回退。
    """

    try:
        return resolve_host_root_dir(plugin_dir)
    except RuntimeLoadError:
        return None


__all__ = ["resolve_host_root_dir", "try_resolve_host_root_dir"]