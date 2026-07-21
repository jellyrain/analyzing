from __future__ import annotations

from pathlib import Path
from typing import Any

from analyzing.test.contract import validate_plugin_contract
from analyzing.test.invoke import invoke_plugin
from analyzing.test.models import SampleTestResult


def run_plugin_sample(
    text: str,
    params: dict[str, Any] | None = None,
    expected_pipeline_output: dict[str, list[Any]] | list[str] | None = None,
    project_dir: str | Path | None = None,
) -> SampleTestResult:
    """
    运行一条插件样例测试
    """

    output = invoke_plugin(
        text=text,
        params=params,
        project_dir=project_dir,
    )

    errors = validate_plugin_contract(output)

    if expected_pipeline_output is not None:
        pipeline_result = output.pipeline_result

        if pipeline_result is None:
            errors.append(
                "无法校验 expected_pipeline_output，因为 pipeline_result 为空"
            )
        elif pipeline_result.pipeline_output != expected_pipeline_output:
            errors.append("pipeline_output 与预期不一致")

    return SampleTestResult(
        ok=not errors,
        errors=errors,
        output=output,
    )


__all__ = ["run_plugin_sample"]
