from __future__ import annotations

from analyzing.plugin.result import PluginExecutionOutput


def validate_plugin_contract(output: PluginExecutionOutput) -> list[str]:
    """
    校验插件输出是否符合 SDK 契约
    """

    errors: list[str] = []

    if not isinstance(output, PluginExecutionOutput):
        return ["插件输出不是 PluginExecutionOutput"]

    pipeline_result = output.pipeline_result
    if pipeline_result is None:
        errors.append("pipeline_result 不能为空")
        return errors

    plugin_type = pipeline_result.plugin_type

    if plugin_type == "parser":
        pipeline_output = pipeline_result.pipeline_output

        if not isinstance(pipeline_output, dict):
            errors.append("parser 的 pipeline_output 必须是 dict[str, list[Any]]")
            return errors

        for key, value in pipeline_output.items():
            if not isinstance(key, str) or not key.strip():
                errors.append("parser 的 pipeline_output key 必须是非空字符串")

            if not isinstance(value, list):
                errors.append(f"parser 的 pipeline_output[{key!r}] 必须是 list")

        return errors

    if plugin_type == "splitter":
        pipeline_output = pipeline_result.pipeline_output

        if not isinstance(pipeline_output, list):
            errors.append("splitter 的 pipeline_output 必须是 list[str]")
            return errors

        for index, item in enumerate(pipeline_output):
            if not isinstance(item, str):
                errors.append(f"splitter 的 pipeline_output[{index}] 必须是字符串")

        return errors

    errors.append(f"未知的 pipeline_result.plugin_type: {plugin_type}")
    return errors


__all__ = ["validate_plugin_contract"]
