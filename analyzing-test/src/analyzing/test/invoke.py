from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from analyzing.plugin.base import AbstractPlugin
from analyzing.plugin.enums.plugin import PluginType
from analyzing.plugin.errors import PluginInvokeError
from analyzing.plugin.parser import ParserPlugin
from analyzing.plugin.remote import PluginInvokeResponse, PluginInvokeRequest
from analyzing.plugin.result import PluginExecutionOutput
from analyzing.plugin.splitter import SplitterPlugin
from analyzing.runtime.config import SubprocessRuntimeConfig
from analyzing.runtime.subprocess import build_subprocess_command

from analyzing.test.loader import ensure_manifest_matches_instance, load_plugin


def _normalize_params(
    plugin: AbstractPlugin,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    调用插件自己的参数校验逻辑，并要求返回 dict
    """

    raw_params = params or {}
    if not isinstance(raw_params, dict):
        raise PluginInvokeError("params 必须是 dict")

    normalized_params = plugin.validate_params(raw_params)
    if not isinstance(normalized_params, dict):
        raise PluginInvokeError("plugin.validate_params 必须返回 dict")

    return normalized_params


def _require_plugin_output(raw_output: object) -> PluginExecutionOutput:
    """
    要求插件必须返回 SDK 规定的标准输出对象
    """

    if not isinstance(raw_output, PluginExecutionOutput):
        raise PluginInvokeError("插件必须返回 PluginExecutionOutput")

    return raw_output


def _build_operation(plugin_type: PluginType | None) -> str:
    """
    根据插件类型推导调用操作名
    """

    if plugin_type == PluginType.PARSER:
        return "parse"

    if plugin_type == PluginType.SPLITTER:
        return "split"

    raise PluginInvokeError(f"不支持的 plugin_type: {plugin_type}")


def _build_plugin_output_from_response(
    response: PluginInvokeResponse,
) -> PluginExecutionOutput:
    """
    把 subprocess 响应恢复成标准插件输出对象
    """

    if not response.ok:
        error_code = response.error_code or "plugin_invoke_failed"
        error_message = response.error_message or "插件调用失败"
        raise PluginInvokeError(f"{error_code}: {error_message}")

    return PluginExecutionOutput(
        raw_output=response.raw_output,
        pipeline_result=response.pipeline_result,
    )


def _invoke_subprocess_plugin(
    *,
    project_dir: Path,
    plugin_id: str,
    plugin_type: PluginType | None,
    runtime: SubprocessRuntimeConfig,
    text: str,
    params: dict[str, Any],
) -> PluginExecutionOutput:
    """
    以“一次请求一次进程”的方式调用 subprocess 插件

    这个模式更适合开发期测试：
    - 不需要额外维护常驻进程
    - 更容易定位启动失败和协议错误
    """

    argv, cwd, extra_env = build_subprocess_command(
        config=runtime,
        base_dir=str(project_dir),
    )

    request = PluginInvokeRequest(
        plugin_id=plugin_id,
        operation=_build_operation(plugin_type),
        payload={
            "text": text,
            "params": params,
        },
    )

    request_text = json.dumps(
        request.model_dump(mode="json"),
        ensure_ascii=False,
    )
    stdin_payload = f"{request_text}\n"

    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env={**os.environ, **extra_env},
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )

    try:
        stdout_text, stderr_text = process.communicate(
            input=stdin_payload,
            timeout=runtime.launcher.invoke_timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.communicate()
        raise PluginInvokeError("subprocess 插件调用超时") from exc

    response_line = ""
    for line in stdout_text.splitlines():
        stripped = line.strip()
        if stripped:
            response_line = stripped
            break

    if not response_line:
        stderr_message = stderr_text.strip()
        if process.returncode != 0:
            raise PluginInvokeError(
                f"subprocess 插件未返回响应，退出码={process.returncode}，stderr={stderr_message}"
            )
        raise PluginInvokeError("subprocess 插件未返回有效响应")

    try:
        response = PluginInvokeResponse.model_validate_json(response_line)
    except Exception as exc:
        raise PluginInvokeError(
            "subprocess 插件响应无法解析为 PluginInvokeResponse"
        ) from exc

    return _build_plugin_output_from_response(response)


def invoke_plugin(
    text: str,
    params: dict[str, Any] | None = None,
    project_dir: str | Path | None = None,
) -> PluginExecutionOutput:
    """
    调用当前插件项目中的插件
    """

    if not isinstance(text, str):
        raise PluginInvokeError("text 必须是字符串")

    loaded = load_plugin(project_dir)
    manifest = loaded.manifest
    runtime = manifest.runtime

    if manifest.runtime_mode == "inproc":
        instance = loaded.instance
        if instance is None:
            raise PluginInvokeError("inproc 插件加载成功，但未得到本地实例")

        ensure_manifest_matches_instance(loaded)
        normalized_params = _normalize_params(instance, params)

        if manifest.plugin_type == PluginType.PARSER:
            if not isinstance(instance, ParserPlugin):
                raise PluginInvokeError(
                    "manifest.plugin_type=parser，但实例未实现 ParserPlugin"
                )

            return _require_plugin_output(
                instance.parse(
                    text=text,
                    params=normalized_params,
                )
            )

        if manifest.plugin_type == PluginType.SPLITTER:
            if not isinstance(instance, SplitterPlugin):
                raise PluginInvokeError(
                    "manifest.plugin_type=splitter，但实例未实现 SplitterPlugin"
                )

            return _require_plugin_output(
                instance.split(
                    text=text,
                    params=normalized_params,
                )
            )

        raise PluginInvokeError(f"不支持的 plugin_type: {manifest.plugin_type}")

    if manifest.runtime_mode == "subprocess":
        if not isinstance(runtime, SubprocessRuntimeConfig):
            raise PluginInvokeError("subprocess 插件 runtime 配置类型不正确")

        # subprocess 模式下，参数规范化由插件子进程内部完成。
        raw_params = params or {}
        if not isinstance(raw_params, dict):
            raise PluginInvokeError("params 必须是 dict")

        return _invoke_subprocess_plugin(
            project_dir=loaded.project_dir,
            plugin_id=manifest.plugin_id,
            plugin_type=manifest.plugin_type,
            runtime=runtime,
            text=text,
            params=raw_params,
        )

    raise PluginInvokeError(f"当前版本尚未实现的 runtime_mode: {manifest.runtime_mode}")


__all__ = ["invoke_plugin"]
