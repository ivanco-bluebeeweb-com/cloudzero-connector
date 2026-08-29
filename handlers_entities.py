"""Read-only entity layer for CloudZero Connector.

No generic writes in v1 -- CloudZero's write surface (AnyCost billing
ingestion) is a distinct data-pipeline capability deferred to v2 per
PREPARATION.md/app.py.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import cloudzero_client as cz
from app import chat
from handlers_connection import resolve_or_error
from schemas import (
    GetBillingCostsParams, BillingCostsReport,
    ListBillingDimensionsParams, DimensionList,
    ListInsightsParams, InsightList,
    ListRolesParams, RoleList,
    ListAnycostConnectionsParams, AnycostConnectionList,
    GetAnycostBillingDropParams, AnycostBillingDrop,
)


@chat.function(
    "get_billing_costs",
    "Read CloudZero billing costs for a date range, with optional granularity, group-by dimension, and filter.",
    action_type="read", chain_callable=True, data_model=BillingCostsReport,
)
async def get_billing_costs(ctx, params: GetBillingCostsParams) -> ActionResult:
    """Read billing costs for a date range."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    query = {"start_date": params.start_date, "end_date": params.end_date, "granularity": params.granularity}
    if params.group_by:
        query["group_by"] = params.group_by
    if params.filter_expr:
        query["filter"] = params.filter_expr
    data = await cz.request(ctx, conn, "GET", "/v2/billing/costs", params=query, action="get billing costs")
    rows = data.get("costs", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    total = 0.0
    for r in rows:
        try:
            total += float(r.get("cost", 0) or 0)
        except (TypeError, ValueError):
            continue
    return ActionResult.ok(BillingCostsReport(
        start_date=params.start_date, end_date=params.end_date, granularity=params.granularity,
        total_cost=round(total, 2), rows=rows,
    ))


@chat.function(
    "list_billing_dimensions",
    "List billing dimensions (e.g. CloudProvider, Service, Team) configured on the connected CloudZero account.",
    action_type="read", chain_callable=True, data_model=DimensionList,
)
async def list_billing_dimensions(ctx, params: ListBillingDimensionsParams) -> ActionResult:
    """List billing dimensions."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    data = await cz.request(ctx, conn, "GET", "/v2/billing/dimensions", action="list billing dimensions")
    dims = data.get("dimensions", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    return ActionResult.ok(DimensionList(count=len(dims), dimensions=dims))


@chat.function(
    "list_insights",
    "List cost insights (CloudZero's own anomaly/opportunity findings) on the connected account.",
    action_type="read", chain_callable=True, data_model=InsightList,
)
async def list_insights(ctx, params: ListInsightsParams) -> ActionResult:
    """List cost insights."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    data = await cz.request(ctx, conn, "GET", "/v2/insights", params={"limit": params.limit}, action="list insights")
    items = data.get("insights", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    return ActionResult.ok(InsightList(count=len(items), insights=items))


@chat.function(
    "list_roles",
    "List user roles configured on the connected CloudZero account.",
    action_type="read", chain_callable=True, data_model=RoleList,
)
async def list_roles(ctx, params: ListRolesParams) -> ActionResult:
    """List roles."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    data = await cz.request(ctx, conn, "GET", "/v2/roles", action="list roles")
    items = data.get("roles", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    return ActionResult.ok(RoleList(count=len(items), roles=items))


@chat.function(
    "list_anycost_connections",
    "List AnyCost stream connections (external cost-data feeds) configured on the connected CloudZero account.",
    action_type="read", chain_callable=True, data_model=AnycostConnectionList,
)
async def list_anycost_connections(ctx, params: ListAnycostConnectionsParams) -> ActionResult:
    """List AnyCost stream connections."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    data = await cz.request(ctx, conn, "GET", "/v2/connections/anycost/stream", action="list AnyCost connections")
    items = data.get("connections", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    return ActionResult.ok(AnycostConnectionList(count=len(items), connections=items))


@chat.function(
    "get_anycost_billing_drop",
    "Read one AnyCost stream connection's billing drop contents for a given month.",
    action_type="read", chain_callable=True, data_model=AnycostBillingDrop,
)
async def get_anycost_billing_drop(ctx, params: GetAnycostBillingDropParams) -> ActionResult:
    """Read an AnyCost billing drop."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    data = await cz.request(
        ctx, conn, "GET",
        f"/v2/connections/anycost/stream/{params.connection_id_cz}/billing-drop/{params.month}",
        action="get AnyCost billing drop",
    )
    return ActionResult.ok(AnycostBillingDrop(connection_id_cz=params.connection_id_cz, month=params.month, record=data if isinstance(data, dict) else {}))
