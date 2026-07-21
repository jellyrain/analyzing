from __future__ import annotations

from typing import Any

from analyzing.plugin.result import PluginExecutionOutput, ParserPluginResultPayload
from analyzing.plugin.parser import BaseManifestParserPlugin

from .core import StrNumberParserCore


class StrNumberParserPlugin(BaseManifestParserPlugin):
    manifest_levels_up = 1

    def __init__(self) -> None:
        super().__init__()
        self.core = StrNumberParserCore()

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        absolute = params.get("absolute", False)
        if not isinstance(absolute, bool):
            raise ValueError("absolute must be a boolean")
        return {"absolute": absolute}

    def parse(self, text: str, params: dict[str, Any]) -> PluginExecutionOutput:
        normalized = self.validate_params(params)
        extracted = self.core.parse(text, absolute=normalized["absolute"])
        pipeline_output = {
            "number": [item["number"] for item in extracted]
        } if extracted else {}

        return PluginExecutionOutput(
            raw_output=extracted,
            pipeline_result=ParserPluginResultPayload(
                plugin_type="parser",
                pipeline_output=pipeline_output,
            ),
        )


def build_plugin() -> StrNumberParserPlugin:
    return StrNumberParserPlugin()
