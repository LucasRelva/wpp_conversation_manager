import os
import secrets
import time
import hmac
import hashlib
from collections import defaultdict, deque
from typing import Optional, Deque, Dict
from fastapi import Header, HTTPException, Request

_RATE_BUCKETS: Dict[str, Deque[float]] = defaultdict(deque)


def _is_missing(value: Optional[str]) -> bool:
    return value is None or value.strip() == ""


def _safe_equals(a: str, b: str) -> bool:
    return secrets.compare_digest(a, b)


def _get_client_id(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _enforce_rate_limit(bucket_key: str, max_requests: int, window_seconds: int) -> None:
    now = time.time()
    window_start = now - window_seconds
    bucket = _RATE_BUCKETS[bucket_key]

    while bucket and bucket[0] < window_start:
        bucket.popleft()

    if len(bucket) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    bucket.append(now)


def _verify_hmac_sha256_signature(body: bytes, secret: str, provided_signature: Optional[str]) -> bool:
    if _is_missing(provided_signature):
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    return _safe_equals(provided_signature.strip(), expected)


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if _is_missing(raw_value):
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


async def require_agent_api_key(
    request: Request,
    x_agent_api_key: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None)
) -> None:
    """
    Optional auth gate for agent-only endpoints.
    If AGENT_API_KEY is set, request must include either:
    - X-Agent-API-Key: <key>
    - Authorization: Bearer <key>
    """
    client_id = _get_client_id(request)
    _enforce_rate_limit(
        f"agent:{client_id}",
        max_requests=_get_int_env("AGENT_RATE_LIMIT_PER_MINUTE", 120),
        window_seconds=60
    )

    expected = os.getenv("AGENT_API_KEY", "").strip()
    if _is_missing(expected):
        return

    bearer = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()

    provided = x_agent_api_key or bearer
    if _is_missing(provided) or not _safe_equals(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing agent API key")


async def verify_webhook_secret(request: Request) -> None:
    """
    Optional webhook authenticity validation.
    If WEBHOOK_SECRET is set, incoming webhook must include X-Webhook-Secret.
    """
    client_id = _get_client_id(request)
    _enforce_rate_limit(
        f"webhook:{client_id}",
        max_requests=_get_int_env("WEBHOOK_RATE_LIMIT_PER_MINUTE", 300),
        window_seconds=60
    )

    expected = os.getenv("WEBHOOK_SECRET", "").strip()
    if _is_missing(expected):
        return

    body = await request.body()
    provided_hmac = request.headers.get("X-Webhook-Signature")
    provided_secret = request.headers.get("X-Webhook-Secret")

    # Preferred mode: HMAC SHA-256 signature on raw request body.
    # Backward-compatible fallback: exact shared secret header.
    is_valid = _verify_hmac_sha256_signature(body, expected, provided_hmac)
    if not is_valid and not _is_missing(provided_secret):
        is_valid = _safe_equals(provided_secret.strip(), expected)

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
