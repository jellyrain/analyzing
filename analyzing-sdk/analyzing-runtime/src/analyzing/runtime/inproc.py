import sys
from contextlib import contextmanager
from importlib import import_module
from pathlib import Path
from typing import Iterator, Any

from analyzing.runtime.errors import RuntimeLoadError
from analyzing.runtime.config import InprocRuntimeConfig


@contextmanager
def temporary_sys_path(paths: list[str]) -> Iterator[None]:
    """
    临时把插件目录加入 sys.path，退出时恢复
    """

    inserted: list[str] = []

    for raw_path in paths:
        resolved = str(Path(raw_path).resolve())
        if resolved not in sys.path:
            sys.path.insert(0, resolved)
            inserted.append(resolved)

    try:
        yield
    finally:
        for path in inserted:
            if path in sys.path:
                sys.path.remove(path)


def load_inproc_symbol(
    config: InprocRuntimeConfig,
    extra_search_paths: list[str] | None = None,
) -> Any:
    """
    根据 runtime.entrypoint 加载模块内对象
    """

    search_paths = list(config.search_paths)
    if extra_search_paths:
        search_paths.extend(extra_search_paths)

    try:
        with temporary_sys_path(search_paths):
            module = import_module(config.entrypoint.module)
            return getattr(module, config.entrypoint.attribute)
    except Exception as exc:
        raise RuntimeLoadError(
            f"加载 inproc 插件入口失败: {config.entrypoint.module}:{config.entrypoint.attribute}"
        ) from exc


def build_inproc_plugin(
    config: InprocRuntimeConfig,
    extra_search_paths: list[str] | None = None,
) -> Any:
    """
    构造 inproc 插件对象
    """

    target = load_inproc_symbol(
        config=config,
        extra_search_paths=extra_search_paths,
    )

    try:
        if isinstance(target, type):
            return target()

        if callable(target):
            return target()

        return target
    except Exception as exc:
        raise RuntimeLoadError("构造 inproc 插件实例失败") from exc


__all__ = ["temporary_sys_path", "load_inproc_symbol", "build_inproc_plugin"]
