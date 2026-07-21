from __future__ import annotations

from typing import Any

from analyzing.plugin.result import SplitterPluginResultPayload
from analyzing.plugin.splitter import (
    BaseManifestSplitterPlugin,
    SplitterPluginExecutionOutput,
)

from .core import SentenceTextSplit


class SentenceSplitterPlugin(BaseManifestSplitterPlugin):
    manifest_levels_up = 1

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        return {}

    def split(self, text: str, params: dict[str, Any]) -> SplitterPluginExecutionOutput:
        extracted = SentenceTextSplit.split_by_sentence(text)

        return SplitterPluginExecutionOutput(
            raw_output={
                "sentence-" + str(index + 1): item for index, item in enumerate(extracted)
            },
            pipeline_result=SplitterPluginResultPayload(
                plugin_type="splitter",
                pipeline_output=extracted,
            ),
        )


def build_plugin() -> SentenceSplitterPlugin:
    return SentenceSplitterPlugin()
