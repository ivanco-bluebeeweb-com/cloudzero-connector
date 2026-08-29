# CloudZero Connector -- Preparation (v0.1)

## API surface
CloudZero API v2 (api.cloudzero.com) -- REST/JSON, resources: billing
costs, billing dimensions, insights, roles, AnyCost stream connections
(billing drops), CostFormation definitions. Confirmed via
docs.cloudzero.com (2026-08-29).

## Auth model
Static **API key** passed directly in the Authorization header -- NO
"Bearer " prefix (confirmed via docs.cloudzero.com/reference/authorization
and docs.cloudzero.com/docs/send-via-api: "Authorization: <YOUR_API_KEY>").
Key is generated in the CloudZero console with a chosen scope (e.g. AI Hub
Access, standard read/write). No token exchange, no expiry -- same
simplicity class as Vantage/Expensify/Brex, EXCEPT the header format has
no Bearer prefix, which is the one implementation detail this connector
must get right and every other connector in this session's family gets
"Bearer X" by default -- flagged explicitly to avoid a silent auth bug.

## Why BYOK
Same reasoning as every other connector here -- the user's own
multi-cloud/SaaS/AI billing data is already aggregated and normalized
(via CostFormation) inside THEIR OWN CloudZero account. The API key is
generated per CloudZero organization from their own console.

## Scope for v1
Read-heavy: billing costs (with CloudProvider/dimension/granularity
filters), billing dimensions, insights, roles, AnyCost stream
connections and their billing drops. Write: none in v1 -- CloudZero's
primary write surface (AnyCost data ingestion / billing_drop creation)
is a data-pipeline operation for pushing NON-native cost data INTO
CloudZero, not a typical "create a business record" action, and is
explicitly deferred to v2 as a distinct ingestion-focused capability
rather than shoehorned into this read-focused v1.

## Rate limits / known constraints
Standard REST pagination. Billing cost queries require explicit
date-range and granularity params (hourly/daily/weekly/monthly/yearly)
per CloudZero's own /v2/billing/costs contract.
