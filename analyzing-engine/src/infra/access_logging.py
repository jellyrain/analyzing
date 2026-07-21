from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from analyzing.monitor.records import AccessLogRecord
from analyzing.monitor.tracker import MonitorTracker
from fastapi import Request, Response

from src.utils.time import get_curr_time


def _parse_content_length(value: str | None) -> int | None:
    """
    将 Content-Length 请求头安全转换为整数
    """

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_response_size(response: Response) -> int | None:
    """
    优先从响应头读取响应体大小，取不到时再回退到内存中的 body 长度
    """

    header_size = _parse_content_length(response.headers.get("content-length"))
    if header_size is not None:
        return header_size

    body = getattr(response, "body", None)
    if isinstance(body, (bytes, bytearray)):
        return len(body)

    return None


def build_access_log_middleware(
    tracker: MonitorTracker,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    """
    构建引擎 API 访问日志中间件
    """

    async def access_log_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """
        记录每次 API 请求的基础访问日志
        """

        started_at = get_curr_time()
        started_perf = perf_counter()
        response: Response | None = None
        error_message: str | None = None

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            error_message = str(exc)
            raise
        finally:
            try:
                tracker.record_access_log(
                    AccessLogRecord(
                        access_id=uuid4().hex,
                        trace_id=request.headers.get("x-trace-id"),
                        method=request.method,
                        path=request.url.path,
                        status_code=response.status_code
                        if response is not None
                        else 500,
                        request_size=_parse_content_length(
                            request.headers.get("content-length")
                        ),
                        response_size=(
                            _resolve_response_size(response)
                            if response is not None
                            else None
                        ),
                        latency_ms=int((perf_counter() - started_perf) * 1000),
                        client_ip=(
                            request.client.host if request.client is not None else None
                        ),
                        detail={
                            "query_string": request.url.query or "",
                            "user_agent": request.headers.get("user-agent"),
                            "referer": request.headers.get("referer"),
                            "error_message": error_message,
                        },
                        created_at=started_at,
                    )
                )
            except Exception as exc:
                print(f"[engine.access_monitor] access 日志写入失败: {exc}")

    return access_log_middleware


__all__ = ["build_access_log_middleware"]
