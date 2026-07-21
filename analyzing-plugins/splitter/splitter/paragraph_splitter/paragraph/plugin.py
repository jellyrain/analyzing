from __future__ import annotations

from typing import Any

from analyzing.plugin.result import SplitterPluginResultPayload
from analyzing.plugin.splitter import (
    BaseManifestSplitterPlugin,
    SplitterPluginExecutionOutput,
)

from .core import ParagraphTextSplit


class ParagraphSplitterPlugin(BaseManifestSplitterPlugin):
    manifest_levels_up = 1

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        return {}

    def split(self, text: str, params: dict[str, Any]) -> SplitterPluginExecutionOutput:
        extracted = ParagraphTextSplit.split_by_paragraph(text)

        return SplitterPluginExecutionOutput(
            raw_output={
                "paragraph-" + str(index + 1): item for index, item in enumerate(extracted)
            },
            pipeline_result=SplitterPluginResultPayload(
                plugin_type="splitter",
                pipeline_output=extracted,
            ),
        )


def build_plugin() -> ParagraphSplitterPlugin:
    return ParagraphSplitterPlugin()
