from __future__ import annotations

import re
from typing import Any

from analyzing.plugin.result import SplitterPluginResultPayload
from analyzing.plugin.splitter import (
    BaseManifestSplitterPlugin,
    SplitterPluginExecutionOutput,
)

from .core import RegexTextSplit


class RegexSplitterPlugin(BaseManifestSplitterPlugin):
    manifest_levels_up = 1

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        pattern = params.get("pattern", "")

        if not isinstance(pattern, str) or not pattern.strip():
            raise ValueError("pattern must be a non-empty string")

        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"invalid regex pattern: {exc}") from exc

        return {
            "pattern": pattern,
        }

    def split(self, text: str, params: dict[str, Any]) -> SplitterPluginExecutionOutput:
        normalized = self.validate_params(params)
        extracted = RegexTextSplit.split_by_regex(
            text=text,
            pattern=normalized["pattern"],
        )

        return SplitterPluginExecutionOutput(
            raw_output={
                "re-" + str(index + 1): item for index, item in enumerate(extracted)
            },
            pipeline_result=SplitterPluginResultPayload(
                plugin_type="splitter",
                pipeline_output=extracted,
            ),
        )


def build_plugin() -> RegexSplitterPlugin:
    return RegexSplitterPlugin()
