from __future__ import annotations

from typing import Any

from analyzing.plugin.result import PluginExecutionOutput, ParserPluginResultPayload
from analyzing.plugin.parser import BaseManifestParserPlugin

from .core import RegexParserCore


class RegexParserPlugin(BaseManifestParserPlugin):
    manifest_levels_up = 1

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        pattern = params.get("pattern", "")
        group_index = params.get("group_index", 1)
        negative_pattern = params.get("negative_pattern", "")

        if not isinstance(pattern, str) or not pattern.strip():
            raise ValueError("pattern must be a non-empty string")

        if not isinstance(group_index, int) or group_index < 0:
            raise ValueError("group_index must be a non-negative integer")

        if not isinstance(negative_pattern, str):
            raise ValueError("negative_pattern must be a string")

        return {
            "pattern": pattern,
            "group_index": group_index,
            "negative_pattern": negative_pattern.strip(),
        }

    def parse(self, text: str, params: dict[str, Any]) -> PluginExecutionOutput:
        normalized = self.validate_params(params)
        extracted = RegexParserCore.parse(
            text=text,
            pattern=normalized["pattern"],
            group_index=normalized["group_index"],
            negative_pattern=normalized["negative_pattern"] or None,
        )

        return PluginExecutionOutput(
            raw_output={
                "re-" + str(index + 1): item for index, item in enumerate(extracted)
            },
            pipeline_result=ParserPluginResultPayload(
                plugin_type="parser",
                pipeline_output={"re": extracted} if extracted else {},
            ),
        )


def build_plugin() -> RegexParserPlugin:
    return RegexParserPlugin()
