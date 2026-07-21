from __future__ import annotations

from typing import Any

from analyzing.plugin.result import PluginExecutionOutput, ParserPluginResultPayload
from analyzing.plugin.parser import BaseManifestParserPlugin

from .core import StrTimeParserCore


class StrTimeParserPlugin(BaseManifestParserPlugin):
    manifest_levels_up = 1

    def __init__(self) -> None:
        super().__init__()
        self.core = StrTimeParserCore()

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        return {}

    def parse(self, text: str, params: dict[str, Any]) -> PluginExecutionOutput:
        extracted = self.core.parse(text)
        pipeline_output = {
            "time": [item["full_datetime"] for item in extracted]
        } if extracted else {}

        return PluginExecutionOutput(
            raw_output=extracted,
            pipeline_result=ParserPluginResultPayload(
                plugin_type="parser",
                pipeline_output=pipeline_output,
            ),
        )


def build_plugin() -> StrTimeParserPlugin:
    return StrTimeParserPlugin()
