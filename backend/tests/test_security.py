import hashlib
import hmac
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app import security


class DummyRequest:
    def __init__(self, body=b"", headers=None, client_host="127.0.0.1"):
        self._body = body
        self.headers = headers or {}
        self.client = SimpleNamespace(host=client_host)

    async def body(self):
        return self._body


@pytest.fixture(autouse=True)
def clear_rate_buckets():
    security._RATE_BUCKETS.clear()


@pytest.mark.asyncio
async def test_agent_auth_accepts_bearer_token(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "top-secret")
    request = DummyRequest(headers={})
    await security.require_agent_api_key(
        request=request,
        x_agent_api_key=None,
        authorization="Bearer top-secret"
    )


@pytest.mark.asyncio
async def test_agent_auth_rejects_invalid_token(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "top-secret")
    request = DummyRequest(headers={})
    with pytest.raises(HTTPException) as exc:
        await security.require_agent_api_key(
            request=request,
            x_agent_api_key="wrong",
            authorization=None
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_webhook_hmac_validation(monkeypatch):
    secret = "webhook-secret"
    body = b'{"ping":"pong"}'
    signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256
    ).hexdigest()

    monkeypatch.setenv("WEBHOOK_SECRET", secret)
    request = DummyRequest(body=body, headers={"X-Webhook-Signature": signature})
    await security.verify_webhook_secret(request)


@pytest.mark.asyncio
async def test_agent_rate_limit(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "")
    monkeypatch.setenv("AGENT_RATE_LIMIT_PER_MINUTE", "2")
    request = DummyRequest(headers={})

    await security.require_agent_api_key(request=request)
    await security.require_agent_api_key(request=request)
    with pytest.raises(HTTPException) as exc:
        await security.require_agent_api_key(request=request)
    assert exc.value.status_code == 429
