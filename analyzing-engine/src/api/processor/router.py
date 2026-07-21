from uuid import uuid4

from analyzing.monitor.records import ExecutionRecord, ExecutionStatus
from fastapi import APIRouter, Form, Depends
from starlette.responses import JSONResponse

from src.api.deps import get_engine_context
from src.api.processor.schema import PipelineRunRequest
from src.app.schemas import EngineContext
from src.pipeline.processor import run_pipeline
from src.pipeline.schemas import ParserResult
from src.pipeline.validator import parse_pipeline_config_input
from src.utils.response import APIResponse
from src.utils.time import get_curr_time

pipeline_router = APIRouter(prefix="/processor", tags=["processor"])


def _estimate_result_output_count(result: ParserResult) -> int:
    """
    估算本次 processor 最终输出数量。
    """

    total = 0

    for value in result.data.values():
        if isinstance(value, list):
            total += len(value)
        else:
            total += 1

    return total


def _record_execution_safely(
    context: EngineContext,
    record: ExecutionRecord,
) -> None:
    """
    以“失败不影响主流程”的方式写入 execution 监控。
    """

    monitor_tracker = context.monitor_tracker
    if monitor_tracker is None:
        return

    try:
        monitor_tracker.record_execution(record)
    except Exception:
        return


def _run_pipeline_with_monitor(
    *,
    text: str,
    config,
    context: EngineContext,
) -> JSONResponse:
    """
    在 execution 监控包裹下执行一次 processor。
    """

    runtime_manager = context.runtime_manager
    if runtime_manager is None:
        return APIResponse.error(message="引擎运行时管理器尚未初始化")

    execution_id = uuid4().hex
    trace_id = uuid4().hex
    started_at = get_curr_time()
    _record_execution_safely(
        context,
        ExecutionRecord(
            execution_id=execution_id,
            trace_id=trace_id,
            status=ExecutionStatus.RUNNING,
            input_size=len(text),
            started_at=started_at,
            detail={},
        ),
    )
    try:
        result = run_pipeline(
            text=text,
            config=config,
            runtime_manager=runtime_manager,
            execution_id=execution_id,
            trace_id=trace_id,
        )
    except Exception as exc:
        finished_at = get_curr_time()
        _record_execution_safely(
            context,
            ExecutionRecord(
                execution_id=execution_id,
                trace_id=trace_id,
                status=ExecutionStatus.FAILED,
                input_size=len(text),
                latency_ms=int((finished_at - started_at).total_seconds() * 1000),
                error_message=str(exc),
                started_at=started_at,
                finished_at=finished_at,
                detail={},
            ),
        )

        return APIResponse.error_data_to_json(
            message="处理失败",
            data={
                "error_message": str(exc),
                "execution_id": execution_id,
                "trace_id": trace_id,
            },
        )

    finished_at = get_curr_time()
    _record_execution_safely(
        context,
        ExecutionRecord(
            execution_id=execution_id,
            trace_id=trace_id,
            status=ExecutionStatus.SUCCEEDED,
            input_size=len(text),
            output_count=_estimate_result_output_count(result),
            latency_ms=int((finished_at - started_at).total_seconds() * 1000),
            started_at=started_at,
            finished_at=finished_at,
            detail={},
        ),
    )

    return APIResponse.success_data_to_json(result, message="处理成功")


@pipeline_router.post("")
def processor(
    request: PipelineRunRequest, context: EngineContext = Depends(get_engine_context)
) -> JSONResponse:
    """
    解析单个文书
    """
    result = parse_pipeline_config_input(request.config)
    if not result.ok:
        return APIResponse.error_code(
            400,
            "配置校验失败",
            {"valid": False, "errors": result.errors},
        )

    return _run_pipeline_with_monitor(
        text=request.text,
        config=result.config,
        context=context,
    )


@pipeline_router.post("/kettle")
def processor(
    text: str = Form(...),
    config: str = Form(...),
    context: EngineContext = Depends(get_engine_context),
) -> JSONResponse:
    """
    解析单个文书 kettle 兼容版
    """
    result = parse_pipeline_config_input(config)
    if not result.ok:
        return APIResponse.error_code(
            400,
            "配置校验失败",
            {"valid": False, "errors": result.errors},
        )

    return _run_pipeline_with_monitor(
        text=text,
        config=result.config,
        context=context,
    )


__all__ = ["pipeline_router"]
