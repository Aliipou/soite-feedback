"""Security headers middleware — applied to every response."""

import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

_CSP_DEV = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-eval'; "  # vite HMR requires unsafe-eval in dev
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self' ws://localhost:* http://localhost:*; "
    "frame-ancestors 'none';"
)

_CSP_PROD = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "  # Tailwind compiled CSS requires this
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add required security headers and X-Request-ID to every response."""

    def __init__(self, app: object, production: bool = False) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._csp = _CSP_PROD if production else _CSP_DEV
        self._production = production

    async def dispatch(self, request: Request, call_next: object) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response: Response = await call_next(request)  # type: ignore[operator]

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = self._csp

        if self._production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response
