"""Pydantic params/result models for CloudZero Connector.

All params models are module-scope (V17 federal invariant, same rule as
every other connector this session's schemas.py).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class NoParams(BaseModel):
    """Explicit empty params model -- V17 disallows untyped handlers."""
    pass


class ConnectionScoped(BaseModel):
    connection_id: str = Field(
        "",
        description="Which connected CloudZero account to use (see list_connections). Omit if only one is connected.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Connection -- static API key, no Bearer prefix, no OAuth
# ──────────────────────────────────────────────────────────────────────────


class ConnectCloudZeroParams(BaseModel):
    api_key: str = Field("", description="Your CloudZero API key (from the CloudZero console).")
    label: str = Field("", description="Optional friendly label for this connection, e.g. 'Acme Inc CloudZero'.")


class ProviderConnection(BaseModel):
    id: str = ""
    label: str = ""


class ProviderConnectionList(BaseModel):
    connections: list[ProviderConnection] = Field(default_factory=list)


class DisconnectCloudZeroParams(BaseModel):
    connection_id: str = Field(description="Which connection to disconnect (see list_connections).")


class DeleteResult(BaseModel):
    deleted: bool = False
    id: str = ""


# ──────────────────────────────────────────────────────────────────────────
# Reads
# ──────────────────────────────────────────────────────────────────────────


class GetBillingCostsParams(ConnectionScoped):
    start_date: str = Field(description="Start date, YYYY-MM-DD.")
    end_date: str = Field(description="End date, YYYY-MM-DD.")
    granularity: str = Field("daily", description="One of: hourly, daily, weekly, monthly, yearly.")
    group_by: str = Field("", description="Optional dimension name to group by, e.g. 'CloudProvider'.")
    filter_expr: str = Field("", description="Optional filter, e.g. 'CloudProvider=AWS'.")


class BillingCostsReport(BaseModel):
    start_date: str = ""
    end_date: str = ""
    granularity: str = ""
    total_cost: float = 0.0
    rows: list[dict] = Field(default_factory=list)


class ListBillingDimensionsParams(ConnectionScoped):
    pass


class DimensionList(BaseModel):
    count: int = 0
    dimensions: list[dict] = Field(default_factory=list)


class ListInsightsParams(ConnectionScoped):
    limit: int = Field(50, ge=1, le=200, description="Maximum insights to return.")


class InsightList(BaseModel):
    count: int = 0
    insights: list[dict] = Field(default_factory=list)


class ListRolesParams(ConnectionScoped):
    pass


class RoleList(BaseModel):
    count: int = 0
    roles: list[dict] = Field(default_factory=list)


class ListAnycostConnectionsParams(ConnectionScoped):
    pass


class AnycostConnectionList(BaseModel):
    count: int = 0
    connections: list[dict] = Field(default_factory=list)


class GetAnycostBillingDropParams(ConnectionScoped):
    connection_id_cz: str = Field(description="The CloudZero AnyCost stream connection id.")
    month: str = Field(description="Month to read, YYYY-MM.")


class AnycostBillingDrop(BaseModel):
    connection_id_cz: str = ""
    month: str = ""
    record: dict = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────
# Value-add report
# ──────────────────────────────────────────────────────────────────────────


class GetSpendOverviewParams(ConnectionScoped):
    start_date: str = Field(description="Start date, YYYY-MM-DD.")
    end_date: str = Field(description="End date, YYYY-MM-DD.")


class SpendOverviewReport(BaseModel):
    start_date: str = ""
    end_date: str = ""
    total_spend: float = 0.0
    by_provider: dict[str, float] = Field(default_factory=dict)
