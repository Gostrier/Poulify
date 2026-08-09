import time

import importlib.util
import pytest

from core import security


def test_rate_limiter_allows_up_to_limit():
    limiter = security.RateLimiter(max_requests=3, window_seconds=60)
    assert limiter.allow("user-1") is True
    assert limiter.allow("user-1") is True
    assert limiter.allow("user-1") is True
    assert limiter.allow("user-1") is False


def test_rate_limiter_window_expires():
    limiter = security.RateLimiter(max_requests=1, window_seconds=1)
    assert limiter.allow("user-2") is True
    assert limiter.allow("user-2") is False
    time.sleep(1.1)
    assert limiter.allow("user-2") is True


@pytest.mark.skipif(
    importlib.util.find_spec("httpx") is None,
    reason="httpx required for TestClient",
)
def test_csrf_flow_rejects_posts_without_token():
    from fastapi import Depends, FastAPI, Form
    from starlette.middleware import Middleware
    from starlette.testclient import TestClient

    app = FastAPI(middleware=[Middleware(security.CSRFMiddleware, secure=False)])

    @app.post("/submit")
    async def submit(field: str = Form(...), _csrf=Depends(security.check_csrf)):
        return {"ok": field}

    client = TestClient(app)

    # First GET issues the CSRF cookie and exposes the token to templates.
    token_resp = client.get("/")
    csrf_cookie = token_resp.cookies.get("csrf_token")
    assert csrf_cookie

    # POST without the form token is rejected.
    resp = client.post("/submit", data={"field": "x"})
    assert resp.status_code == 403

    # POST with a matching token is accepted.
    resp = client.post("/submit", data={"field": "x", "csrf_token": csrf_cookie})
    assert resp.status_code == 200
    assert resp.json() == {"ok": "x"}
