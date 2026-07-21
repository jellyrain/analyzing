from __future__ import annotations

from typing import Any

from analyzing.plugin.result import SplitterPluginResultPayload
from analyzing.plugin.splitter import (
    BaseManifestSplitterPlugin,
    SplitterPluginExecutionOutput,
)

from .core import AnchorTextSplit


class AnchorSplitterPlugin(BaseManifestSplitterPlugin):
    manifest_levels_up = 1

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        anchor_start = params.get("anchor_start", "")
        anchor_end = params.get("anchor_end", "")

        if not isinstance(anchor_start, str) or not anchor_start.strip():
            raise ValueError("anchor_start must be a non-empty string")

        if not isinstance(anchor_end, str):
            raise ValueError("anchor_end must be a string")

        return {
            "anchor_start": anchor_start,
            "anchor_end": anchor_end.strip() or None,
            "is_regex": bool(params.get("is_regex", False)),
        }

    def split(self, text: str, params: dict[str, Any]) -> SplitterPluginExecutionOutput:
        normalized = self.validate_params(params)
        extracted = AnchorTextSplit.split_by_anchor(
            text=text,
            anchor_start=normalized["anchor_start"],
            anchor_end=normalized["anchor_end"],
            is_regex=normalized["is_regex"],
        )

        return SplitterPluginExecutionOutput(
            raw_output={
                "anchor-" + str(index + 1): item for index, item in enumerate(extracted)
            },
            pipeline_result=SplitterPluginResultPayload(
                plugin_type="splitter",
                pipeline_output=extracted,
            ),
        )


def build_plugin() -> AnchorSplitterPlugin:
    return AnchorSplitterPlugin()
