from typing import Any

from jsonpath_ng.ext import parse


def extract_value_by_jsonpath(
    parsed: dict[str, list[Any]],
    source_path: str,
) -> Any:
    """
    使用 JSONPath 从 parsed 中提取值
    """

    try:
        expression = parse(source_path)
    except Exception as error:
        raise ValueError(f"field_mapping 路径解析失败: {source_path}") from error

    matches = expression.find(parsed)
    if not matches:
        return None

    values = [match.value for match in matches]

    # 只有一个命中时直接返回值，多个命中时返回列表
    if len(values) == 1:
        return values[0]

    return values


def apply_field_mapping(
    parsed: dict[str, list[Any]],
    field_mapping: dict[str, str] | None,
) -> dict[str, Any]:
    """
    将 parsed 按 field_mapping 映射成最终输出
    """

    if not field_mapping:
        return parsed

    mapped_data: dict[str, Any] = {}

    for target_field, source_path in field_mapping.items():
        mapped_data[target_field] = extract_value_by_jsonpath(parsed, source_path)

    return mapped_data


__all__ = ["extract_value_by_jsonpath", "apply_field_mapping"]
