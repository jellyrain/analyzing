from __future__ import annotations

from typing import Any

from analyzing.plugin.result import PluginExecutionOutput, ParserPluginResultPayload
from analyzing.plugin.parser import BaseManifestParserPlugin

from .core import KVParserCore


class KVParserPlugin(BaseManifestParserPlugin):
    manifest_levels_up = 1

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        separator_chars = params.get("separator_chars", ":：")
        punct_chars = params.get("punct_chars", r"\s,;，；。、")

        if not isinstance(separator_chars, str) or not separator_chars.strip():
            raise ValueError("separator_chars must be a non-empty string")

        if not isinstance(punct_chars, str) or not punct_chars.strip():
            raise ValueError("punct_chars must be a non-empty string")

        return {
            "separator_chars": separator_chars,
            "allow_multiline": bool(params.get("allow_multiline", False)),
            "punct_chars": punct_chars,
            "allow_key_start_with_digit": bool(
                params.get("allow_key_start_with_digit", False)
            ),
        }

    def parse(self, text: str, params: dict[str, Any]) -> PluginExecutionOutput:
        normalized = self.validate_params(params)
        extracted = KVParserCore.parse(
            text=text,
            separator_chars=normalized["separator_chars"],
            allow_multiline=normalized["allow_multiline"],
            punct_chars=normalized["punct_chars"],
            allow_key_start_with_digit=normalized["allow_key_start_with_digit"],
        )

        items: list[dict[str, Any]] = []
        for key, values in extracted.items():
            for index, value in enumerate(values, start=1):
                items.append(
                    {
                        "key": key,
                        "value": value,
                        "occurrence": index,
                    }
                )

        return PluginExecutionOutput(
            raw_output=items,
            pipeline_result=ParserPluginResultPayload(
                plugin_type="parser", pipeline_output=extracted
            ),
        )


def build_plugin() -> KVParserPlugin:
    return KVParserPlugin()
