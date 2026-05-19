"""Structured request logging middleware.

NEVER logs request bodies — could contain patient data.
Logs: request_id, method, path, status, latency_ms.
"""

import time

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger: structlog.BoundLogger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with timing. Body is never touched."""

    async def dispatch(self, request: Request, call_next: object) -> Response:
        start = time.perf_counter()
        response: Response = await call_next(request)  # type: ignore[operator]
        latency_ms = round((time.perf_counter() - start) * 1000, 1)

        request_id = getattr(request.state, "request_id", "-")

        logger.info(
            "request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            latency_ms=latency_ms,
        )
        return response
