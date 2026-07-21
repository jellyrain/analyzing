from __future__ import annotations

from typing import Any

from analyzing.plugin.result import PluginExecutionOutput, ParserPluginResultPayload
from analyzing.plugin.parser import BaseManifestParserPlugin

from .core import ChoiceParserCore


class ChoiceParserPlugin(BaseManifestParserPlugin):
    manifest_levels_up = 1

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        markers = params.get("markers", [])
        strip_chars = params.get("strip_chars", "")

        if not isinstance(markers, list) or not all(
            isinstance(item, str) and item for item in markers
        ):
            raise ValueError("markers must be a non-empty string list")

        if not isinstance(strip_chars, str):
            raise ValueError("strip_chars must be a string")

        return {
            "markers": markers,
            "allow_multiline": bool(params.get("allow_multiline", False)),
            "is_suffix_marker": bool(params.get("is_suffix_marker", False)),
            "strip_chars": strip_chars,
        }

    def parse(self, text: str, params: dict[str, Any]) -> PluginExecutionOutput:
        normalized = self.validate_params(params)
        extracted = ChoiceParserCore.parse(
            text=text,
            markers=normalized["markers"],
            allow_multiline=normalized["allow_multiline"],
            is_suffix_marker=normalized["is_suffix_marker"],
            strip_chars=normalized["strip_chars"],
        )

        items: list[dict[str, str]] = []
        for marker, values in extracted.items():
            for index, value in enumerate(values, start=1):
                items.append({"marker": marker, "value": value, "occurrence": index})

        return PluginExecutionOutput(
            raw_output=items,
            pipeline_result=ParserPluginResultPayload(
                plugin_type="parser",
                pipeline_output=extracted,
            ),
        )


def build_plugin() -> ChoiceParserPlugin:
    return ChoiceParserPlugin()
