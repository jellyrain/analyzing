from typing import Any

from analyzing.contracts.model import AnalyzingModel

from src.pipeline.schemas import PipelineExtractionConfig


class PipelineRunRequest(AnalyzingModel):
    """
    processor 执行请求
    """

    # 待处理原文
    text: str

    # 单条 processor 配置
    config: PipelineExtractionConfig | dict[str, Any] | str


__all__ = ["PipelineRunRequest"]
