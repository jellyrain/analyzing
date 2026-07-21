from __future__ import annotations

from typing import Any

from analyzing.plugin.result import PluginExecutionOutput, ParserPluginResultPayload
from analyzing.plugin.parser import BaseManifestParserPlugin

from .core import HighPrecisionTimeParserCore


class HighPrecisionTimeParserPlugin(BaseManifestParserPlugin):
    manifest_levels_up = 1

    def __init__(self) -> None:
        super().__init__()
        self.core = HighPrecisionTimeParserCore()

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        keyword = params.get("keyword", "")
        window_size = params.get("window_size", 100)
        direction = params.get("direction")

        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError("keyword must be a non-empty string")

        if not isinstance(window_size, int) or window_size <= 0:
            raise ValueError("window_size must be a positive integer")

        if direction not in (None, "", "front", "back"):
            raise ValueError("direction must be front, back or empty")

        return {
            "keyword": keyword.strip(),
            "window_size": window_size,
            "direction": direction or None,
        }

    def parse(self, text: str, params: dict[str, Any]) -> PluginExecutionOutput:
        normalized = self.validate_params(params)
        extracted = self.core.parse(
            text=text,
            keyword=normalized["keyword"],
            window_size=normalized["window_size"],
            direction=normalized["direction"],
        )

        pipeline_output = {}
        if extracted:
            pipeline_output = {
                extracted[0]["keyword"]: [extracted[0]["full_datetime"]]
            }

        return PluginExecutionOutput(
            raw_output=extracted,
            pipeline_result=ParserPluginResultPayload(
                plugin_type="parser",
                pipeline_output=pipeline_output,
            ),
        )


def build_plugin() -> HighPrecisionTimeParserPlugin:
    return HighPrecisionTimeParserPlugin()
