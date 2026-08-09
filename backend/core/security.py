import secrets
import time
import logging
from collections import defaultdict, deque
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Issues a per-session CSRF token cookie and exposes it to templates.

    Validation of POST requests happens via the `check_csrf` dependency on
    each state-changing route. Splitting these keeps the middleware from
    consuming the request body (which would break FastAPI's own form parsing).
    """

    def __init__(self, app, cookie_name="csrf_token", secure=False):
        super().__init__(app)
        self.cookie_name = cookie_name
        self.secure = secure

    async def dispatch(self, request, call_next):
        token = request.cookies.get(self.cookie_name) or secrets.token_urlsafe(32)
        request.state.csrf_token = token

        response = await call_next(request)

        if self.cookie_name not in request.cookies:
            response.set_cookie(
                self.cookie_name,
                token,
                httponly=True,
                samesite="lax",
                secure=self.secure,
                max_age=60 * 60 * 12,
            )
        return response


async def check_csrf(request: Request):
    """FastAPI dependency: verify the POST form's `csrf_token` matches the cookie."""
    if request.method != "POST":
        return

    cookie_token = request.cookies.get("csrf_token")
    form_token = None
    try:
        form = await request.form()
        form_token = (form.get("csrf_token") or "").strip()
    except Exception:
        form_token = None

    if not cookie_token or not form_token or not secrets.compare_digest(cookie_token, form_token):
        logger.warning("Rejected POST %s with missing/invalid CSRF token", request.url.path)
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing CSRF token. Refresh the page and try again.",
        )


class RateLimiter:
    """Simple in-memory sliding-window rate limiter keyed by an arbitrary string."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        queue = self._hits[key]
        while queue and now - queue[0] > self.window_seconds:
            queue.popleft()
        if len(queue) >= self.max_requests:
            return False
        queue.append(now)
        return True


auth_limiter = RateLimiter(max_requests=5, window_seconds=300)


def client_ip(request: Request) -> str:
    """Return the client IP, honoring a trusted X-Forwarded-For header."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def check_auth_rate_limit(request: Request):
    """FastAPI dependency: blocks brute-force attempts on auth endpoints."""
    if not auth_limiter.allow(client_ip(request)):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please wait a few minutes.",
        )
