"""Value-add report for CloudZero Connector -- spend overview by cloud
provider, same "aggregate raw records into one glance" shape as every
other connector's handlers_reports.py this session.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import cloudzero_client as cz
from app import chat
from handlers_connection import resolve_or_error
from schemas import GetSpendOverviewParams, SpendOverviewReport


@chat.function(
    "get_spend_overview_report",
    "Value-add report: summarize CloudZero billing costs by cloud provider for a date range.",
    action_type="read", chain_callable=True, data_model=SpendOverviewReport,
)
async def get_spend_overview_report(ctx, params: GetSpendOverviewParams) -> ActionResult:
    """Scan billing costs grouped by CloudProvider and summarize."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    query = {
        "start_date": params.start_date, "end_date": params.end_date,
        "granularity": "daily", "group_by": "CloudProvider",
    }
    data = await cz.request(ctx, conn, "GET", "/v2/billing/costs", params=query, action="get billing costs for spend overview")
    rows = data.get("costs", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    total = 0.0
    by_provider: dict[str, float] = {}
    for r in rows:
        provider = r.get("CloudProvider") or r.get("group") or "Unknown"
        try:
            cost = float(r.get("cost", 0) or 0)
        except (TypeError, ValueError):
            continue
        total += cost
        by_provider[provider] = by_provider.get(provider, 0.0) + cost
    return ActionResult.success(SpendOverviewReport(
        start_date=params.start_date, end_date=params.end_date,
        total_spend=round(total, 2),
        by_provider={k: round(v, 2) for k, v in by_provider.items()},
    ), summary="Spend overview report retrieved.")
