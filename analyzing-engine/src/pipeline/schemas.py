from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from analyzing.contracts.model import AnalyzingModel
from pydantic import Field


class PipelineSplitConfig(AnalyzingModel):
    """
    拆分器配置
    """

    # 直接使用 split 插件标识，不在引擎里做类型翻译
    split_type: str

    # 拆分插件参数，保持透传
    split_params: dict[str, Any] | None = None


class PipelineParserConfig(AnalyzingModel):
    """
    解析器配置
    """

    # 直接使用 parser 插件标识，不在引擎里做类型翻译
    parser_type: str

    # 解析插件参数，保持透传
    parser_params: dict[str, Any] | None = None

    # 兼容旧配置里的 app_root 包装根
    app_root: str | None = None

    # 子层流水线，key 为父层某个字段名
    children: dict[str, list[PipelineParserConfig]] | None = None

    # 为 True 时将子层结果拍平到当前层
    flatten: bool = False

    # flatten 时使用的别名前缀
    alias_prefix: str | None = None


# 重新解析 PipelineParserConfig 的所有字段类型
PipelineParserConfig.model_rebuild()


class ParserResult(AnalyzingModel):
    """
    单次解析结果
    """

    # 解析结果ID
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # 保留流水线原始结构，供 field_mapping 和排查使用
    parsed: dict[str, list[Any]] | None = None

    # 最终输出结果；未做 field_mapping 时通常等于 parsed 的兼容形态
    data: dict[str, Any]

    # 原文字段来源，key 与 parsed 对齐
    origin: dict[str, list[str]] = Field(default_factory=dict)

    # 记录本次使用的解析插件标识
    parser_type: str

    # 解析结果生成的时间
    parser_time: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


class PipelineExtractionConfig(AnalyzingModel):
    """
    单条抽取规则
    """

    # 提取配置ID
    extraction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # 提取配置名称
    extraction_name: str

    # 切分配置
    split_config: list[PipelineSplitConfig] | None = None

    # 解析配置
    parser_config: PipelineParserConfig

    # 字段映射配置
    field_mapping: dict[str, str] | None = None


@dataclass(slots=True)
class ConfigValidationResult:
    """
    配置校验结果
    """

    # 是否校验通过
    ok: bool

    # 校验失败时返回的人类可读错误列表
    errors: list[str]

    # 校验通过后得到的结构化配置对象
    config: PipelineExtractionConfig | None = None


__all__ = [
    "PipelineSplitConfig",
    "PipelineParserConfig",
    "ParserResult",
    "PipelineExtractionConfig",
    "ConfigValidationResult",
]
