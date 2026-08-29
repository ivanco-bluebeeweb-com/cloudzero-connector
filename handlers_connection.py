"""Connection management for CloudZero Connector: connect/disconnect/list.

Static API key (no Bearer prefix) -- verified synchronously against a
harmless read endpoint at connect time. No refresh logic needed (no
expiry).
"""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import cloudzero_client as cz
from app import chat
from schemas import (
    NoParams,
    ConnectCloudZeroParams,
    ProviderConnection, ProviderConnectionList,
    DisconnectCloudZeroParams, DeleteResult,
)

_SECRET_NAME = "cloudzero_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


async def resolve_connection(ctx, connection_id: str = "") -> dict | None:
    connections = await _load_connections(ctx)
    if not connections:
        return None
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        return None
    return connections[0]


async def resolve_or_error(ctx, connection_id: str = ""):
    conn = await resolve_connection(ctx, connection_id)
    if not conn:
        return None, ActionResult.error(
            "No CloudZero connection found. Connect CloudZero first.",
            code="CLOUDZERO_NOT_CONNECTED",
        )
    return conn, None


@chat.function(
    "connect_cloudzero",
    "Connect your own CloudZero account by saving your API key (from the CloudZero console), after checking "
    "it actually works.",
    action_type="write", chain_callable=True, data_model=ProviderConnection,
    event="cloudzero-connected", effects=["create:connection"],
)
async def connect_cloudzero(ctx, params: ConnectCloudZeroParams) -> ActionResult:
    """Connect a CloudZero account."""
    check = await cz.verify_key(params.api_key)
    if not check.get("ok"):
        return ActionResult.error(check.get("message", "Could not verify CloudZero API key."), code=check.get("code", "CLOUDZERO_UNAUTHORIZED"))
    connections = await _load_connections(ctx)
    conn_id = str(uuid.uuid4())
    label = params.label or "CloudZero"
    connections.append({"id": conn_id, "api_key": params.api_key, "label": label})
    await _save_connections(ctx, connections)
    return ActionResult.ok(ProviderConnection(id=conn_id, label=label))


@chat.function(
    "list_connections",
    "List the connected CloudZero accounts.",
    action_type="read", chain_callable=True, data_model=ProviderConnectionList,
)
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """List connected CloudZero accounts."""
    connections = await _load_connections(ctx)
    return ActionResult.ok(ProviderConnectionList(
        connections=[ProviderConnection(id=c["id"], label=c.get("label", "CloudZero")) for c in connections]
    ))


@chat.function(
    "disconnect_cloudzero",
    "Disconnect a CloudZero account: deletes the saved API key. Nothing in CloudZero itself is changed.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="cloudzero-disconnected", effects=["delete:connection"],
)
async def disconnect_cloudzero(ctx, params: DisconnectCloudZeroParams) -> ActionResult:
    """Disconnect a CloudZero account."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error("Connection not found.", code="CLOUDZERO_NOT_CONNECTED")
    await _save_connections(ctx, remaining)
    return ActionResult.ok(DeleteResult(deleted=True, id=params.connection_id))
