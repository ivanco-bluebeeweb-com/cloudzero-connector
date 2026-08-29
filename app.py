"""Extension declaration, secrets, lifecycle hooks.

WHY BYOK, same reasoning as every other connector here -- the user's own
multi-cloud/SaaS/AI billing data is already aggregated and normalized
(via CostFormation) inside THEIR OWN CloudZero account.

WHY A STATIC API KEY, NO BEARER PREFIX (confirmed against
docs.cloudzero.com/reference/authorization and docs.cloudzero.com/docs/
send-via-api, 2026-08-29): "Authorization: <YOUR_API_KEY>" -- explicitly
NOT "Bearer <key>". This is the one auth detail that differs from every
other connector in this session's family and is called out here so it is
never silently "fixed" back to a Bearer prefix by habit.

WHY NO WRITES IN V1: CloudZero's write surface (AnyCost billing_drop
ingestion) is a data-pipeline operation for pushing non-native cost data
INTO CloudZero -- a distinct ingestion capability, not a typical
create-a-business-record action -- explicitly deferred to v2 per
PREPARATION.md rather than shoehorned in here.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "cloudzero-connector",
    version="0.1.0",
    display_name="CloudZero",
    icon="icon.svg",
    capabilities=["cloudzero:read"],
    description=(
        "Connect your own CloudZero account (bring your own API key from the CloudZero console) to read "
        "billing costs (by cloud provider, dimension, and granularity), billing dimensions, insights, roles, "
        "and AnyCost stream connections, plus a value-add spend overview report. Read-only in this release -- "
        "AnyCost data ingestion (pushing external cost data into CloudZero) is a separate pipeline capability "
        "deferred to v2."
    ),
)

chat = ChatExtension(ext)
