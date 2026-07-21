from __future__ import annotations

from typing import Any

from analyzing.plugin.result import PluginExecutionOutput, ParserPluginResultPayload
from analyzing.plugin.parser import BaseManifestParserPlugin

from .core import BracketKVParserCore


class BracketKVParserPlugin(BaseManifestParserPlugin):
    manifest_levels_up = 1

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        left_bracket = params.get("left_bracket", "【")
        right_bracket = params.get("right_bracket", "】")

        if not isinstance(left_bracket, str) or not left_bracket:
            raise ValueError("left_bracket must be a non-empty string")

        if not isinstance(right_bracket, str) or not right_bracket:
            raise ValueError("right_bracket must be a non-empty string")

        return {
            "left_bracket": left_bracket,
            "right_bracket": right_bracket,
            "allow_multiline": bool(params.get("allow_multiline", False)),
        }

    def parse(self, text: str, params: dict[str, Any]) -> PluginExecutionOutput:
        normalized = self.validate_params(params)
        extracted = BracketKVParserCore.parse(
            text=text,
            left_bracket=normalized["left_bracket"],
            right_bracket=normalized["right_bracket"],
            allow_multiline=normalized["allow_multiline"],
        )

        items: list[dict[str, str]] = []
        for key, values in extracted.items():
            for index, value in enumerate(values, start=1):
                items.append({"key": key, "value": value, "occurrence": index})

        return PluginExecutionOutput(
            raw_output=items,
            pipeline_result=ParserPluginResultPayload(
                plugin_type="parser",
                pipeline_output=extracted,
            ),
        )


def build_plugin() -> BracketKVParserPlugin:
    return BracketKVParserPlugin()
