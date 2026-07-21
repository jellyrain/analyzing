from __future__ import annotations

from typing import Callable


ProgressCallback = Callable[[str], None]


def emit_progress(
    progress_callback: ProgressCallback | None,
    message: str,
) -> None:
    if progress_callback is not None:
        progress_callback(message)
        return

    print(message)
