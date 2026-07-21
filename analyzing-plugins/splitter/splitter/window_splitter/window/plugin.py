from __future__ import annotations

from typing import Any

from analyzing.plugin.result import SplitterPluginResultPayload
from analyzing.plugin.splitter import (
    BaseManifestSplitterPlugin,
    SplitterPluginExecutionOutput,
)

from .core import WindowTextSplit


class WindowSplitterPlugin(BaseManifestSplitterPlugin):
    manifest_levels_up = 1

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        window_size = params.get("window_size", 512)
        overlap = params.get("overlap", 128)

        if not isinstance(window_size, int) or window_size <= 0:
            raise ValueError("window_size must be a positive integer")

        if not isinstance(overlap, int) or overlap < 0:
            raise ValueError("overlap must be a non-negative integer")

        if overlap >= window_size:
            raise ValueError("overlap must be smaller than window_size")

        return {
            "window_size": window_size,
            "overlap": overlap,
        }

    def split(self, text: str, params: dict[str, Any]) -> SplitterPluginExecutionOutput:
        normalized = self.validate_params(params)
        extracted = WindowTextSplit.split_by_window(
            text=text,
            window_size=normalized["window_size"],
            overlap=normalized["overlap"],
        )

        return SplitterPluginExecutionOutput(
            raw_output={
                "window-" + str(index + 1): item for index, item in enumerate(extracted)
            },
            pipeline_result=SplitterPluginResultPayload(
                plugin_type="splitter",
                pipeline_output=extracted,
            ),
        )


def build_plugin() -> WindowSplitterPlugin:
    return WindowSplitterPlugin()
