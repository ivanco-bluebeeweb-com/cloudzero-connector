"""Thin HTTP client for CloudZero API.

CRITICAL: static API key passed as the RAW Authorization header value --
NO "Bearer " prefix (confirmed via docs.cloudzero.com/reference/
authorization). Every other connector's *_client.py this session uses
"Bearer <token>"; this one deliberately does not, and that is correct.
"""
from __future__ import annotations

from typing import Any

import httpx

API_BASE = "https://api.cloudzero.com"

CLOUDZERO_NOT_CONNECTED = "CLOUDZERO_NOT_CONNECTED"
CLOUDZERO_UNAUTHORIZED = "CLOUDZERO_UNAUTHORIZED"
CLOUDZERO_FORBIDDEN = "CLOUDZERO_FORBIDDEN"
CLOUDZERO_NOT_FOUND = "CLOUDZERO_NOT_FOUND"
CLOUDZERO_RATE_LIMITED = "CLOUDZERO_RATE_LIMITED"
CLOUDZERO_BACKEND_ERROR = "CLOUDZERO_BACKEND_ERROR"
CLOUDZERO_VALIDATION_FAILED = "CLOUDZERO_VALIDATION_FAILED"

_MESSAGES = {
    CLOUDZERO_NOT_CONNECTED: "No CloudZero connection found. Connect CloudZero first.",
    CLOUDZERO_UNAUTHORIZED: "CloudZero rejected the API key as invalid.",
    CLOUDZERO_FORBIDDEN: "CloudZero rejected this request -- the connected API key lacks the required scope.",
    CLOUDZERO_NOT_FOUND: "That CloudZero record was not found.",
    CLOUDZERO_RATE_LIMITED: "CloudZero rate-limited this request. Try again shortly.",
    CLOUDZERO_BACKEND_ERROR: "CloudZero's API returned an error.",
    CLOUDZERO_VALIDATION_FAILED: "CloudZero rejected the request as invalid.",
}


class ClientFail(Exception):
    def __init__(self, payload: dict):
        self.payload = payload
        super().__init__(payload.get("message", "CloudZero request failed"))


def fail(code: str, detail: str = "") -> dict:
    msg = _MESSAGES.get(code, "CloudZero request failed.")
    if detail:
        msg = f"{msg} ({detail})"
    return {"ok": False, "code": code, "message": msg}


async def verify_key(api_key: str) -> dict:
    """Verify an API key works by calling a harmless read endpoint."""
    if not api_key:
        return fail(CLOUDZERO_VALIDATION_FAILED, "api_key is required")
    headers = {"Authorization": api_key}
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(f"{API_BASE}/v2/billing/dimensions", headers=headers)
        except httpx.RequestError as e:
            return fail(CLOUDZERO_BACKEND_ERROR, str(e))
    if resp.status_code == 401:
        return fail(CLOUDZERO_UNAUTHORIZED)
    if resp.status_code == 403:
        return fail(CLOUDZERO_FORBIDDEN)
    if resp.status_code >= 400:
        return fail(CLOUDZERO_BACKEND_ERROR, f"HTTP {resp.status_code}")
    return {"ok": True}


def _check_status(resp: httpx.Response, action: str) -> Any:
    if resp.status_code == 401:
        raise ClientFail(fail(CLOUDZERO_UNAUTHORIZED))
    if resp.status_code == 403:
        raise ClientFail(fail(CLOUDZERO_FORBIDDEN, action))
    if resp.status_code == 404:
        raise ClientFail(fail(CLOUDZERO_NOT_FOUND, action))
    if resp.status_code == 429:
        raise ClientFail(fail(CLOUDZERO_RATE_LIMITED))
    if resp.status_code >= 400:
        raise ClientFail(fail(CLOUDZERO_BACKEND_ERROR, f"HTTP {resp.status_code} on {action}"))
    if not resp.content:
        return {}
    try:
        return resp.json()
    except ValueError:
        return {}


async def request(ctx, conn: dict, method: str, path: str, *, params: dict | None = None,
                   json_body: dict | None = None, action: str = "") -> Any:
    headers = {"Authorization": conn.get("api_key", "")}
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(method, f"{API_BASE}{path}", headers=headers, params=params, json=json_body)
        except httpx.RequestError as e:
            raise ClientFail(fail(CLOUDZERO_BACKEND_ERROR, str(e)))
    return _check_status(resp, action or path)
