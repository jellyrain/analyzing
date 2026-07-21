from collections import defaultdict
from typing import Any

from src.pipeline.field_mapping import apply_field_mapping
from src.pipeline.schemas import (
    PipelineExtractionConfig,
    ParserResult,
    PipelineParserConfig,
    PipelineSplitConfig,
)
from src.runtime.manager import EngineRuntimeManager


def _build_target_key(
    field_name: str,
    parser_config: PipelineParserConfig,
    prefix: str,
) -> str:
    """
    计算当前字段写入结果时使用的 key
    """

    if not parser_config.flatten:
        return field_name

    if parser_config.alias_prefix:
        return f"{parser_config.alias_prefix}_{field_name}"

    if prefix:
        return f"{prefix}_{field_name}"

    return field_name


class PipelineProcessor:
    """
    processor 执行器
    """

    def __init__(
        self,
        runtime_manager: EngineRuntimeManager,
        *,
        execution_id: str | None = None,
        trace_id: str | None = None,
    ):
        """
        初始化 processor 执行器
        """

        # 引擎插件运行时管理器
        self.runtime_manager = runtime_manager

        # 当前宿主执行标识
        self.execution_id = execution_id

        # 当前链路追踪标识
        self.trace_id = trace_id

    def run(
        self,
        text: str,
        config: PipelineExtractionConfig,
    ) -> ParserResult:
        """
        执行单条抽取配置
        """

        split_texts = self._run_split_pipeline(text, config.split_config)

        merged_parsed: dict[str, list[Any]] = defaultdict(list)
        merged_origin: dict[str, list[str]] = defaultdict(list)

        for segment in split_texts:
            segment_parsed, segment_origin = self._process_layer(
                content=segment,
                parser_configs=[config.parser_config],
            )

            for field_name, values in segment_parsed.items():
                merged_parsed[field_name].extend(values)

            for field_name, origins in segment_origin.items():
                merged_origin[field_name].extend(origins)

        normalized_parsed = dict(merged_parsed)
        normalized_origin = dict(merged_origin)
        mapped_data = apply_field_mapping(normalized_parsed, config.field_mapping)

        return ParserResult(
            parsed=normalized_parsed,
            data=mapped_data,
            origin=normalized_origin,
            parser_type=config.parser_config.parser_type,
        )

    def _run_split_pipeline(
        self,
        text: str,
        split_config_list: list[PipelineSplitConfig] | None,
    ) -> list[str]:
        """
        执行拆分流水线
        """

        if not split_config_list:
            return [text]

        current_segments = [text]

        for split_config in split_config_list:
            next_segments: list[str] = []

            for segment in current_segments:
                split_result = self.runtime_manager.invoke_splitter_plugin(
                    plugin_id=split_config.split_type,
                    text=segment,
                    params=split_config.split_params or {},
                    execution_id=self.execution_id,
                    trace_id=self.trace_id,
                )

                if not split_result:
                    continue

                next_segments.extend(split_result)

            current_segments = next_segments

            if not current_segments:
                break

        return current_segments

    def _process_layer(
        self,
        content: str,
        parser_configs: list[PipelineParserConfig],
        prefix: str = "",
    ) -> tuple[dict[str, list[Any]], dict[str, list[str]]]:
        """
        处理单层解析流水线
        """

        layer_output: dict[str, list[Any]] = defaultdict(list)
        layer_origin: dict[str, list[str]] = defaultdict(list)

        for parser_config in parser_configs:
            parse_result = self.runtime_manager.invoke_parser_plugin(
                plugin_id=parser_config.parser_type,
                text=content,
                params=parser_config.parser_params or {},
                execution_id=self.execution_id,
                trace_id=self.trace_id,
            )

            if not parse_result:
                continue

            for field_name, extracted_values in parse_result.items():
                if not extracted_values:
                    continue

                target_key = _build_target_key(
                    field_name=field_name,
                    parser_config=parser_config,
                    prefix=prefix,
                )

                child_configs = None
                if parser_config.children:
                    child_configs = parser_config.children.get(field_name)

                if not child_configs:
                    layer_output[target_key].extend(extracted_values)
                    layer_origin[target_key].extend([content] * len(extracted_values))
                    continue

                # 命中 children 后：
                # 1. 子层有结果时优先使用子层结果
                # 2. 子层无结果时回退保留父值
                # 3. flatten 只决定结果挂载方式，不决定是否吞掉父值
                refined_values: list[Any] = []

                for extracted_value in extracted_values:
                    # 子解析当前只接受字符串输入，非字符串值直接回退保留父值
                    if not isinstance(extracted_value, str):
                        if parser_config.flatten:
                            layer_output[target_key].append(extracted_value)
                            layer_origin[target_key].append(content)
                        else:
                            refined_values.append(extracted_value)
                            layer_origin[target_key].append(content)
                        continue

                    child_output, child_origin = self._process_layer(
                        content=extracted_value,
                        parser_configs=child_configs,
                        prefix=target_key,
                    )

                    # 子层没有产出时，统一回退保留父值
                    if not child_output:
                        if parser_config.flatten:
                            layer_output[target_key].append(extracted_value)
                            layer_origin[target_key].append(extracted_value)
                        else:
                            refined_values.append(extracted_value)
                            layer_origin[target_key].append(extracted_value)
                        continue

                    if parser_config.flatten:
                        for child_key, child_values in child_output.items():
                            if not child_values:
                                continue

                            layer_output[child_key].extend(child_values)

                            # 子层已有 origin 就沿用；没有就回退到当前父值
                            child_key_origins = child_origin.get(child_key)
                            if child_key_origins:
                                layer_origin[child_key].extend(child_key_origins)
                            else:
                                layer_origin[child_key].extend(
                                    [extracted_value] * len(child_values)
                                )
                        continue

                    refined_values.append(child_output)
                    layer_origin[target_key].append(extracted_value)

                if not parser_config.flatten and refined_values:
                    layer_output[target_key].extend(refined_values)

        return dict(layer_output), dict(layer_origin)


def run_pipeline(
    text: str,
    config: PipelineExtractionConfig,
    runtime_manager: EngineRuntimeManager,
    *,
    execution_id: str | None = None,
    trace_id: str | None = None,
) -> ParserResult:
    """
    执行单条 processor 配置
    """

    processor = PipelineProcessor(
        runtime_manager=runtime_manager,
        execution_id=execution_id,
        trace_id=trace_id,
    )
    return processor.run(text=text, config=config)


__all__ = [
    "PipelineProcessor",
    "run_pipeline",
]
