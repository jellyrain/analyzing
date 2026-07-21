import json
from typing import Any

from src.pipeline.schemas import PipelineExtractionConfig, ConfigValidationResult


def parse_pipeline_config_input(
    config_input: PipelineExtractionConfig | dict[str, Any] | str,
) -> ConfigValidationResult:
    """
    解析并校验单条 processor 配置输入
    """

    if isinstance(config_input, PipelineExtractionConfig):
        errors = validate_pipeline_config_data(config_input.model_dump(mode="python"))
        if errors:
            return ConfigValidationResult(ok=False, errors=errors)
        return ConfigValidationResult(ok=True, errors=[], config=config_input)

    if isinstance(config_input, str):
        raw = config_input.strip()
        if not raw:
            return ConfigValidationResult(ok=False, errors=["请先提供 JSON 配置"])

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            return ConfigValidationResult(
                ok=False,
                errors=[
                    f"JSON 语法错误：第 {error.lineno} 行第 {error.colno} 列，{error.msg}"
                ],
            )
    else:
        data = config_input

    errors = validate_pipeline_config_data(data)
    if errors:
        return ConfigValidationResult(ok=False, errors=errors)

    try:
        parsed_config = PipelineExtractionConfig.model_validate(data)
    except Exception as error:
        return ConfigValidationResult(
            ok=False,
            errors=[f"模型校验失败：{format_validation_error(error)}"],
        )

    return ConfigValidationResult(ok=True, errors=[], config=parsed_config)


def validate_pipeline_config_data(data: Any) -> list[str]:
    """
    先做结构级校验，给出比 pydantic 更友好的错误信息
    """

    errors: list[str] = []

    if not isinstance(data, dict):
        return [
            '顶层 JSON 必须是对象，例如 {"extraction_name": "...", "parser_config": {...}}'
        ]

    extraction_name = data.get("extraction_name")
    if not isinstance(extraction_name, str) or not extraction_name.strip():
        errors.append("缺少 extraction_name，或 extraction_name 不是非空字符串")

    split_config = data.get("split_config")
    validate_split_config_for_import(split_config, "split_config", errors)

    parser_config = data.get("parser_config")
    if not isinstance(parser_config, dict):
        errors.append("缺少 parser_config，或 parser_config 不是对象")
    else:
        validate_parser_config_for_import(parser_config, "parser_config", errors)

    validate_field_mapping_for_import(
        data.get("field_mapping"), "field_mapping", errors
    )
    return errors


def validate_split_config_for_import(
    split_config: Any,
    path: str,
    errors: list[str],
) -> None:
    """
    校验 split_config 的结构以及链式 split 的旧语义
    """

    if split_config is None:
        return

    if not isinstance(split_config, list):
        errors.append(f"{path} 必须是数组或 null")
        return

    for index, item in enumerate(split_config):
        item_path = f"{path}[{index}]"

        if not isinstance(item, dict):
            errors.append(f"{item_path} 必须是对象")
            continue

        split_type = item.get("split_type")
        if (
            split_type is None
            or not isinstance(split_type, str)
            or not split_type.strip()
        ):
            errors.append(f"{item_path}.split_type 必须是非空字符串")

        split_params = item.get("split_params")
        if split_params is not None and not isinstance(split_params, dict):
            errors.append(f"{item_path}.split_params 必须是对象或 null")


def validate_parser_config_for_import(
    config: Any,
    path: str,
    errors: list[str],
) -> None:
    """
    递归校验 parser_config 与 children 结构
    """

    if not isinstance(config, dict):
        errors.append(f"{path} 必须是对象")
        return

    parser_type = config.get("parser_type")
    if not isinstance(parser_type, str) or not parser_type.strip():
        errors.append(f"{path}.parser_type 缺少，或不是非空字符串")

    parser_params = config.get("parser_params")
    if parser_params is not None and not isinstance(parser_params, dict):
        errors.append(f"{path}.parser_params 必须是对象或 null")

    flatten = config.get("flatten")
    if flatten is not None and not isinstance(flatten, bool):
        errors.append(f"{path}.flatten 必须是布尔值")

    alias_prefix = config.get("alias_prefix")
    if alias_prefix is not None and not isinstance(alias_prefix, str):
        errors.append(f"{path}.alias_prefix 必须是字符串或 null")

    app_root = config.get("app_root")
    if app_root is not None and not isinstance(app_root, str):
        errors.append(f"{path}.app_root 必须是字符串或 null")

    children = config.get("children")
    if children is None:
        return

    if isinstance(children, list):
        errors.append(
            f'{path}.children 不能是数组，必须是对象格式，例如 {{"父级字段名": [子解析器配置]}}'
        )
        return

    if not isinstance(children, dict):
        errors.append(f"{path}.children 必须是对象或 null")
        return

    for key, child_list in children.items():
        child_path = f"{path}.children.{key}"

        if not isinstance(key, str) or not key.strip():
            errors.append(f"{path}.children 的 key 必须是非空字符串")
            continue

        if not isinstance(child_list, list):
            errors.append(f"{child_path} 必须是数组，数组内放子解析器配置")
            continue

        for index, child_config in enumerate(child_list):
            validate_parser_config_for_import(
                child_config,
                f"{child_path}[{index}]",
                errors,
            )


def validate_field_mapping_for_import(
    mapping: Any,
    path: str,
    errors: list[str],
) -> None:
    """
    校验 field_mapping 结构
    """

    if mapping is None:
        return

    if not isinstance(mapping, dict):
        errors.append(f'{path} 必须是对象，格式例如 {{"目标字段": "$[\\"字段\\"][0]"}}')
        return

    for key, value in mapping.items():
        if not isinstance(key, str) or not key.strip():
            errors.append(f"{path} 的 key 必须是非空字符串")

        if not isinstance(value, str) or not value.strip():
            errors.append(f"{path}.{key} 的值必须是非空路径字符串")
            continue

        if not value.strip().startswith("$"):
            errors.append(f"{path}.{key} 必须以 $ 开头")


def format_validation_error(error: Exception) -> str:
    """
    格式化 pydantic 校验错误
    """

    if not hasattr(error, "errors"):
        return str(error)

    lines: list[str] = []
    for item in error.errors()[:10]:
        loc = ".".join(str(part) for part in item.get("loc", []))
        msg = item.get("msg", str(error))
        lines.append(f"{loc}: {msg}" if loc else msg)

    return "\n".join(lines)


__all__ = [
    "parse_pipeline_config_input",
    "validate_pipeline_config_data",
    "validate_split_config_for_import",
    "validate_parser_config_for_import",
    "validate_field_mapping_for_import",
    "format_validation_error",
]
