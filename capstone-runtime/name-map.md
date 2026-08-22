# Name-identity map — capstone runtime (extended sitting)

One spelling per thing. Every code name below is the exact Lab 1 / Lab 3 / Lab 9 / Lab 10 string — nothing forked, nothing invented as a new identity. Sources: Lab 1 index (I-1…I-11), Lab 3 §2 modules, Lab 9 §2 containers, Lab 10 participants.

## 1. Identity map (code → spec name)

| Code module / package / class | Identity (exact string) | Source |
|---|---|---|
| `payment_gateway/` (package) | Payment Gateway | I-1 system-in-focus |
| `payment_gateway/api_gateway.py` · `APIGateway` | API Gateway | I-4 |
| `payment_gateway/api_gateway.py` · `RateLimiter` | Rate Limiter (API Gateway named responsibility: "rate limiting") | I-4 note |
| `payment_gateway/payment_orchestrator/` (package) | Payment Orchestrator | I-4 |
| `payment_orchestrator/request_handler.py` · `RequestHandler` | Request Handler | Lab 3 §2 / Lab 9 §3 |
| `payment_orchestrator/input_validator.py` · `InputValidator` | Input Validator | Lab 3 §2 |
| `payment_orchestrator/idempotency_manager.py` · `IdempotencyManager` | Idempotency Manager | Lab 3 §2 |
| `payment_orchestrator/fraud_gate.py` · `FraudGate` | Fraud Gate (in-process module — "Fraud Engine is not a standalone container", I-4 note) | Lab 3 §2 |
| `payment_orchestrator/state_machine_engine.py` · `StateMachineEngine` | State Machine Engine | Lab 3 §2 |
| `payment_orchestrator/acquirer_client.py` · `AcquirerClient` | Acquirer Client | Lab 3 §2 |
| `payment_orchestrator/persistence_manager.py` · `PersistenceManager` | Persistence Manager | Lab 3 §2 |
| `payment_orchestrator/event_publisher.py` · `EventPublisher` | Event Publisher | Lab 3 §2 |
| `payment_gateway/stores.py` · `IdempotencyStore` | Idempotency Store | I-4 |
| `payment_gateway/stores.py` · `PaymentStore` | Payment Store | I-4 |
| `payment_gateway/stores.py` · `MessageQueue` | Message Queue | I-4 |
| `payment_gateway/query_store.py` · `QueryStore` | Query Store | I-4 |
| `payment_gateway/expiry_job.py` · `ExpiryJob` | Expiry Job | I-4 |
| `payment_gateway/webhook_service.py` · `WebhookService` | Webhook Service | I-4 |
| `payment_gateway/payment.py` · `Payment` / `PaymentState` | Payment — I-6 named object; states Pending, Authorized, Captured, Voided, Refunded, Declined, Failed; terminal Voided/Refunded/Declined/Failed | I-6 |
| `payment_gateway/mocks.py` · `AcquirerHostStub` | AcquirerHost (I-3). Internally stands for the AcquirerHost → NAPAS Switch → Issuing Bank chain — those two stay labels inside the stub, no new externals | I-3 / Lab 3 §4 |
| `payment_gateway/mocks.py` · `MerchantPlatformFake` | Merchant Platform (I-3) | I-3 |
| `payment_gateway/runtime.py` · `PaymentGatewayRuntime` | Composition root of the documented collapse (§2) — not a new container identity | — |
| `payment_gateway/demo.py` | Demo script only (12-min demo order) — drives the runtime, adds no identity | — |
| Routes `POST /v1/payments`, `POST /v1/payments/{id}/capture`, `POST /v1/payments/{id}/void`, `POST /v1/payments/{id}/refund`, `GET /v1/payments/{id}` | Lab 10 §1–§3 messages + extension (Void, Query) | Lab 10 / extension spec |
| Error codes `authorization_expired`, `amount_exceeds_authorized`, `invalid_state_transition`, `max_refunds_exceeded`, `refund_window_expired`, `amount_exceeds_refundable`, `idempotency_conflict`, `rate_limit_exceeded`, `acquirer_timeout`, fraud rule ids `FRAUD-01`…`FRAUD-05` | Exact Lab 10 / Lab 3 §3 strings + extension | Lab 3 §3, Lab 10, extension |
| Events `payment.authorized`, `payment.declined`, `payment.captured`, `payment.refunded`, `payment.voided`, `payment.failed` | Lab 10 event names + extension | Lab 10 / extension |

No other class, package, route, or error name exists in the runtime. `tests/support.py` (`make_card`, fixtures) is a test helper, not a new I-4 identity.

## 2. Documented collapse — one process

`payment_gateway/runtime.py :: PaymentGatewayRuntime` runs the whole slice in **one process** with **in-memory stores** and an **in-process bus** (allowed collapse per capstone.md). Modules keep the exact Lab 1 / Lab 3 strings (§1). Sync = direct in-process call; async = `publish()` → `drain()` boundary, so webhook delivery is never inside the synchronous response (I-5).

| I-4 container | Where it lives in the collapsed build | I-9 location it stands for |
|---|---|---|
| — (no I-4 container; N/A) | Not built — no TLS termination or reverse proxy exists in a single Python process | Load Balancer (L7) — collapsed into "not applicable"; `api_gateway.APIGateway` is the sync entry point in its place |
| API Gateway | `api_gateway.APIGateway` + `api_gateway.RateLimiter` (in-process) | Application Tier |
| Payment Orchestrator (8 modules) | `payment_orchestrator/` package | Application Tier |
| Query Store | `query_store.QueryStore` (in-memory read model of Payment Store) | Database Tier (read-replica) |
| Expiry Job | `expiry_job.ExpiryJob` (in-process tick, not a real cron) | Worker Tier |
| Idempotency Store | `stores.IdempotencyStore` (in-memory dict) | Cache Tier |
| Payment Store | `stores.PaymentStore` (in-memory dict) | Database Tier |
| Message Queue | `stores.MessageQueue` (in-process bus) | Queue Tier |
| Webhook Service | `webhook_service.WebhookService` (driven by `drain()`) | Worker Tier |

No extra deployable unit exists: `python -m unittest` and `python -m payment_gateway.demo` each start this single process. A cluster is not output; Nginx/Kong, Kafka/SQS, PostgreSQL, Redis are labels only (I-9 product names stay labels).

## 3. N/A rows — Lab 1 out-of-scope (not built)

| Item | Why N/A |
|---|---|
| Tokenization | Lab 1 out-of-scope |
| Card Issuing | Lab 1 out-of-scope |
| Recurring Billing | Lab 1 out-of-scope |
| Dispute/Chargeback | Lab 1 out-of-scope |
| 3D Secure | Lab 1 out-of-scope |
| Multi-currency/FX | Lab 1 out-of-scope |
| POS | Lab 1 out-of-scope |
| KYC/AML | Lab 1 out-of-scope |
| Settlement reconciliation | Lab 1 out-of-scope |

## 4. ASSUMPTION rows — invented simulated values (one string everywhere)

Lab 1 names fraud rules but no thresholds; these simulated values are used in exactly one place each and nowhere else:

| Assumption | Value (the one string) | Where |
|---|---|---|
| FRAUD-02 high-value threshold | `200_000_000` VND | `fraud_gate.HIGH_VALUE_LIMIT` + OpenAPI test bodies |
| FRAUD-01 card velocity | `10` auths/card/hour | `fraud_gate.CARD_VELOCITY_LIMIT` |
| FRAUD-03 merchant velocity | `100` auths/merchant/hour | `fraud_gate.MERCHANT_VELOCITY_LIMIT` |
| FRAUD-05 daily cumulative | `1_000_000_000` VND/card/day | `fraud_gate.DAILY_CARD_LIMIT` |
| Default merchant reference | `"mer_3"` | `request_handler.authorize` |
| Webhook signing secret | `WEBHOOK_SECRET` environment variable (S1: never hardcoded in source) | `runtime.py`, `webhook_service.py`, `mocks.py` |
| Card test data | Luhn-valid generated PANs (`4` + seed + check digit), exp 12/2030 | `tests/support.make_card` |
| Rate limit cap | `100` requests / merchant / `60`s | `api_gateway.RATE_LIMIT_CAP`, `api_gateway.RATE_LIMIT_WINDOW` |
| CON.6 retry | `2` attempts (initial + 1 retry, same transaction reference) | `acquirer_client.MAX_ATTEMPTS` |

Timings that stay labels over the in-process collapse (no real waiting, asserted nowhere as durations):

| Label | Collapsed behaviour |
|---|---|
| CON.2 5s BLPOP concurrent wait | immediate `409 idempotency_conflict` when the key is locked in-flight |
| CON.2 48h TTL / CON.7 30d event TTL | in-memory dicts live for the process; TTL noted in `IdempotencyManager.TTL_SECONDS` |
| CON.6 30s timeout + 1 retry after 5s | `AcquirerClient` retries once (MAX_ATTEMPTS=2); stub raises `AcquirerTimeout` when configured; no real sleep |
| CON.7 retry schedule 1m/5m/30m/2h/12h/24h | attempts counted (`WebhookService.MAX_ATTEMPTS = 7`), no real delays |
| S9 rate-limit window 60s | `RateLimiter` uses injected clock; tests advance time to cross the window |

## 5. I-7 ownership matrix

| Data object | Owner (may write) | Forbidden writers (test attempts) |
|---|---|---|
| Payment records | Persistence Manager (Payment Orchestrator), Expiry Job (CON.4 transition only) | Webhook Service → PermissionError (S6); Query Store → PermissionError (S8) |
| Webhook Event rows | Webhook Service | — |
| Idempotency Entries + Fraud Counters | Idempotency Manager | — |
