# Lab 1 — Scopes with Concrete Values

**R:** BA / SA · **A:** Owner

---

## I-1. Team and Topic

| Field | Your value |
|-------|------------|
| Group | Team 3 — Ninh Mạnh Tiến, Kim Đức Minh, Nguyễn Quang Huy, Trần Quốc Đạt |
| Topic / initiative name | Online Payment Gateway for Domestic Card Transactions |
| System-in-focus | Payment Gateway |
| Goal | Enable merchants to accept online card payments (Visa/MC) via a single API with fraud protection and reliable webhook notification |
| Outcome (measurable) | Process 500 TPS authorization with P95 < 2s; 99.9% uptime; zero duplicate charges via idempotency |
| Product | Payment Gateway API v1 |
| Contract | REST API — OpenAPI 3.0 specification for /v1/payments endpoints |
| Baseline → target | Manual bank transfer (T+2 settlement, no fraud gate) → Real-time card authorization with 5-rule fraud engine and async webhook |
| In scope | Authorization, Capture, Void, Refund, Direct Charge, Status Lifecycle, Fraud Gate (auth only), Webhook Notification, Idempotency, Payment Query |
| Out of scope | Tokenization, Card Issuing, Recurring Billing, Dispute/Chargeback, 3D Secure, Multi-currency/FX, POS, KYC/AML, Settlement reconciliation |

---

## I-2. Actors

| Name | ArchiMate | C4 (Person or —) | Role in the process |
|------|-----------|------------------|---------------------|
| Merchant | Business Actor | Person | Business owner who authorizes payment operations; technical API calls and webhook delivery go through Merchant Platform (I-3) |
| Customer | Business Actor | — | Cardholder; does not interact with Gateway directly |

---

## I-3. External Systems

| Name (simulated) | Responsibility |
|------------------|----------------|
| Merchant Platform | Merchant's backend system; calls the API to authorize/capture/void/refund and receives webhook deliveries |
| AcquirerHost | Routes authorization/capture/void/refund to card network; returns approve/decline |
| NAPAS Switch | Domestic card network connecting acquirer to issuing bank (Visa/MC routing) |
| Issuing Bank | Customer's bank; approves or declines the transaction; holds/releases funds |

---

## I-4. Internal Containers

| Name | Responsibility |
|------|----------------|
| API Gateway | TLS termination, rate limiting, request routing, input validation |
| Payment Orchestrator | Core payment logic: idempotency check → fraud gate → acquirer call → persist → publish event |
| Idempotency Store | Redis-backed key-value store for idempotency entries (48h TTL, 5s concurrent wait) |
| Payment Store | PostgreSQL primary — persistent payment records, status, amounts (write path) |
| Query Store | PostgreSQL streaming replica — serves GET queries (read path) |
| Message Queue | Decouples payment processing from webhook delivery (at-least-once, ordered per payment) |
| Webhook Service | Async event delivery to merchant: HMAC-SHA256 signing, retry (7 attempts), 30d event TTL |
| Expiry Job | Scheduled hourly background job: transitions expired authorizations (7d) to Failed |

**Fraud Engine is not a standalone container.** It runs as an in-process module inside Payment Orchestrator (rule-based pass/block evaluation, 5 rules, < 50ms, authorization path only) — one thing, not both a runnable container and a co-located module.

---

## I-5. Business Process (Happy Path)

**Object that moves:** Payment

1. Merchant Platform submits authorization request (amount, card, idempotency key)
2. API Gateway validates input (amount 10K–500M VND, Luhn, card expiry)
3. Payment Orchestrator checks Idempotency Store (Redis) — duplicate returns cached response
4. Fraud Engine evaluates 5 rules (velocity, high-value, merchant velocity, BIN country, daily cumulative)
5. Payment Orchestrator routes to AcquirerHost (30s timeout, 1 retry after 5s)
6. AcquirerHost → NAPAS → Issuing Bank → approve/decline
7. Payment Orchestrator persists Payment (status: Authorized, expiresAt: now + 7d) to Payment Store
8. Payment Orchestrator publishes payment.authorized event to Message Queue
9. Webhook Service consumes event, signs HMAC-SHA256, delivers POST to Merchant Platform (10s timeout)
10. Merchant Platform receives webhook; later calls capture/void/refund as needed

**Principles / hard rules (what must never happen):**

- Idempotency check must NEVER occur after fraud evaluation or acquirer call
- Fraud Engine must NEVER evaluate on capture, void, or refund paths
- Webhook delivery must NEVER block the synchronous payment API response
- Payment query must NEVER call AcquirerHost or NAPAS
- A single Payment must NEVER have more than 10 partial refunds
- Authorization hold must NEVER exceed 7 calendar days without expiring to Failed

---

## I-6. Named Object States (UML State)

**Object:** Payment

| State | Meaning |
|-------|---------|
| Pending | Request received, acquirer call in flight |
| Authorized | Issuer approved, funds held (7-day window) |
| Captured | Funds transferred to merchant |
| Voided | Authorization cancelled, hold released |
| Refunded | Full refund completed |
| Declined | Issuer or fraud rule rejected |
| Failed | System/network error or authorization expired |

**Transitions:**

| From | Trigger | Next | Terminal? |
|------|---------|------|-----------|
| Pending | Issuer approves (capture:false) | Authorized | No |
| Pending | Issuer approves + immediate capture (Direct Charge, capture:true) | Captured | No |
| Pending | Issuer/fraud declines | Declined | Yes |
| Pending | Timeout/error | Failed | Yes |
| Authorized | Capture succeeds | Captured | No |
| Authorized | Void succeeds | Voided | Yes |
| Authorized | Auth expires (7d, hourly job) | Failed | Yes |
| Captured | Full refund | Refunded | Yes |
| Captured | Partial refund | Captured (refundedAmount updated) | No |

**Terminal states:** Voided, Refunded, Declined, Failed

---

## I-7. Source of Truth

| Data object | Meaning | Source of truth (one container or external) |
|-------------|---------|---------------------------------------------|
| Payment | Transaction record (amount, status, timestamps) | Payment Store |
| Idempotency Entry | Key → cached HTTP response | Idempotency Store |
| Webhook Event | Delivery status, retry count, next attempt | Payment Store (webhook_event records only — Webhook Service writes only this table, never Payment records) |
| Fraud Counters | Card velocity, merchant velocity, daily cumulative | Idempotency Store (Redis) |
| Card Authorization | Approve/decline decision | Issuing Bank (via AcquirerHost) |

---

## I-8. Integration (label sync vs async on Container)

| Pattern | Mechanism | Example on your landscape |
|---------|-----------|---------------------------|
| Sync | HTTPS REST, 30s timeout, 1 retry after 5s | Payment Orchestrator → AcquirerHost |
| Sync | Internal HTTP/gRPC | API Gateway → Payment Orchestrator |
| Sync | Redis GET/SET/BLPOP | Payment Orchestrator → Idempotency Store |
| Async | Message queue (Kafka/SQS), at-least-once | Payment Orchestrator → Message Queue → Webhook Service |
| Async | Webhook POST, HMAC-SHA256, 10s timeout | Webhook Service → Merchant Platform |

---

## I-9. Deployment

| Location | What runs there |
|----------|-----------------|
| Load Balancer (L7) | TLS termination, health checks |
| Application Tier (2+ nodes) | API Gateway, Payment Orchestrator (includes in-process Fraud Engine module) |
| Cache Tier (3-node cluster) | Idempotency Store (Redis) |
| Database Tier | Payment Store (PostgreSQL Primary), Query Store (PostgreSQL Replica) |
| Queue Tier | Message Queue (Kafka / SQS) |
| Worker Tier (2+ nodes) | Webhook Service |
| Scheduler | Expiry Job (hourly cron) |

**Forbidden path:** Webhook Service must NOT write Payment records to Payment Store — it may write only its own Webhook Event delivery-status rows (I-7). Merchant Platform must NOT query AcquirerHost directly.

---

## I-10. Constraints

| ID | Constraint | Effect on the process |
|----|------------|------------------------|
| CON.1 | Single currency VND only (10,000–500,000,000) | Amount validation rejects non-VND or out-of-range; no FX logic |
| CON.2 | Idempotency key required on all POST (max 64 chars, 48h TTL) | Missing/invalid key → 400; duplicate → cached response; concurrent same-key → 5s wait → 409 |
| CON.3 | Fraud gate on authorization path only | Capture/void/refund bypass Fraud Engine entirely |
| CON.4 | Authorization expires after 7 calendar days | Hourly job transitions Authorized → Failed if expiresAt ≤ now |
| CON.5 | Maximum 10 partial refunds per payment within 180 days | Refund request exceeding count/window → 400/409 |
| CON.6 | Acquirer timeout 30s + 1 retry after 5s | Exhausted retries → Failed; same transaction reference (no duplicate) |
| CON.7 | Webhook: 7 attempts (1m/5m/30m/2h/12h/24h), HMAC-SHA256, 30d TTL | After max retries → failed_delivery; event queryable 30 days |
| CON.8 | Single acquirer: AcquirerHost via NAPAS (domestic Visa/MC) | No acquirer routing logic; BIN country ≠ VN → fraud block |

---

## I-11. Named Use Cases for UML

| Use case | Happy path | At least one exception (`alt`) |
|----------|------------|--------------------------------|
| Authorize Payment | Merchant Platform → API Gateway → Payment Orchestrator → Idempotency Store check → Fraud pass → AcquirerHost approve → Persist Authorized → Webhook | alt: Fraud blocks → Declined (no acquirer call) |
| Capture Payment | Merchant Platform → API Gateway → Payment Orchestrator → Idempotency Store check → Validate (Authorized + not expired) → AcquirerHost capture → Persist Captured → Webhook | alt: Auth expired → 409 authorization_expired |
| Refund Payment | Merchant Platform → API Gateway → Payment Orchestrator → Idempotency Store check → Validate (Captured + amount ≤ remaining + count < 10 + ≤ 180d) → AcquirerHost refund → Persist → Webhook | alt: Max refunds exceeded → 400 max_refunds_exceeded |

**One container for optional C4 Component:** Payment Orchestrator
