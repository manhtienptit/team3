# Name-identity map — capstone runtime

One spelling per thing. Every code name below is the exact Lab 1 / Lab 3 / Lab 9 / Lab 10 string — nothing forked, nothing invented as a new identity. Sources: Lab 1 index (I-1…I-11), Lab 3 §2 modules, Lab 9 §2 containers, Lab 10 participants.

## 1. Identity map (code → spec name)

| Code module / package / class | Identity (exact string) | Source |
|---|---|---|
| `payment_gateway/` (package) | Payment Gateway | I-1 system-in-focus |
| `payment_gateway/api_gateway.py` · `APIGateway` | API Gateway | I-4 |
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
| `payment_gateway/webhook_service.py` · `WebhookService` | Webhook Service | I-4 |
| `payment_gateway/payment.py` · `Payment` / `PaymentState` | Payment — I-6 named object; states Pending, Authorized, Captured, Voided, Refunded, Declined, Failed; terminal Voided/Refunded/Declined/Failed | I-6 |
| `payment_gateway/mocks.py` · `AcquirerHostStub` | AcquirerHost (I-3). Internally stands for the AcquirerHost → NAPAS Switch → Issuing Bank chain — those two stay labels inside the stub, no new externals | I-3 / Lab 3 §4 |
| `payment_gateway/mocks.py` · `MerchantPlatformFake` | Merchant Platform (I-3) | I-3 |
| `payment_gateway/runtime.py` · `PaymentGatewayRuntime` | Composition root of the documented collapse (§2) — not a new container identity | — |
| `payment_gateway/demo.py` | Demo script only (10-min demo order) — drives the runtime, adds no identity | — |
| Routes `POST /v1/payments`, `POST /v1/payments/{id}/capture`, `POST /v1/payments/{id}/refund` | Lab 10 §1–§3 messages `POST /v1/payments`, `POST /v1/payments/{id}/capture`, `POST /v1/payments/{id}/refund` | Lab 10 |
| Error codes `authorization_expired`, `amount_exceeds_authorized`, `invalid_state_transition`, `max_refunds_exceeded`, `refund_window_expired`, `amount_exceeds_refundable`, `idempotency_conflict`, fraud rule ids `FRAUD-01`…`FRAUD-05` | Exact Lab 10 / Lab 3 §3 strings | Lab 3 §3, Lab 10 |
| Events `payment.authorized`, `payment.declined`, `payment.captured`, `payment.refunded` | Lab 10 event names | Lab 10 |

JSON wire values for `status` are lowercase (`"authorized"`, `"captured"`, …) exactly as the Lab 10 §1–§3 response bodies write them (`{id, status:"authorized", auth_code}`); the I-6 state identity itself is the capitalized `PaymentState` member (`Authorized`, …). Not a fork — both spellings come from the spec, one per layer.

No other class, package, route, or error name exists in the runtime. `tests/support.py` (`make_card`, fixtures) is a test helper, not a new I-4 identity.

## 2. Documented collapse — one process

`payment_gateway/runtime.py :: PaymentGatewayRuntime` runs the whole slice in **one process** with **in-memory stores** and an **in-process bus** (allowed collapse per capstone.md). Modules keep the exact Lab 1 / Lab 3 strings (§1). Sync = direct in-process call; async = `publish()` → `drain()` boundary, so webhook delivery is never inside the synchronous response (I-5).

| I-4 container / I-9 location | Where it lives in the collapsed build | I-9 location it stands for |
|---|---|---|
| API Gateway | `api_gateway.APIGateway` (in-process) | Application Tier |
| Payment Orchestrator (8 modules) | `payment_orchestrator/` package | Application Tier |
| Idempotency Store | `stores.IdempotencyStore` (in-memory dict) | Cache Tier |
| Payment Store | `stores.PaymentStore` (in-memory dict) | Database Tier |
| Message Queue | `stores.MessageQueue` (in-process bus) | Queue Tier |
| Webhook Service | `webhook_service.WebhookService` (driven by `drain()`) | Worker Tier |
| Load Balancer (L7) | **N/A** — no network listener exists in the collapsed build; TLS termination / health checks stay labels at the in-process call boundary | Load Balancer |
| Scheduler | **N/A** — Expiry Job is not built (I-1 item not in I-11; see spec-trace §3 row 8) | Scheduler |

Every I-9 location of Lab 1 is accounted for above: six stand-for rows plus two N/A rows.

No extra deployable unit exists: `python -m unittest` and `python -m payment_gateway.demo` each start this single process. A cluster is not output; Nginx/Kong, Kafka/SQS, PostgreSQL, Redis are labels only (I-9 product names stay labels).

## 3. N/A rows — in I-1 scope, not I-11 (listed, not built)

| Item | Why N/A |
|---|---|
| Query Store (I-4) | Payment Query is not an I-11 use case → no GET route exists; the container is not built |
| Expiry Job (I-4) | Transition #8 not needed by any I-11 use case; CON.4 is enforced where I-11 needs it — on the capture validation (`authorization_expired` 409) |
| Void Payment | Not an I-11 use case → no route (API Gateway answers `404 not_found`). `AcquirerClient.void` exists only inside the Partial Capture alt (Lab 10 §2 "void remainder") |
| Direct Charge | Not a separate use case — variant of Authorize Payment (`capture:true`), same operation |
| Status Lifecycle | I-6 enforced by State Machine Engine inside the three use cases, not a standalone use case |
| Fraud Gate, Webhook Notification, Idempotency | I-1 in-scope items realized as behavior of the three I-11 use cases, not standalone use cases |
| Tokenization, Card Issuing, Recurring Billing, Dispute/Chargeback, 3D Secure, Multi-currency/FX, POS, KYC/AML, Settlement reconciliation | I-1 out-of-scope — untouched |

## 4. ASSUMPTION rows — invented simulated values (one string everywhere)

Lab 1 names fraud rules but no thresholds; these simulated values are used in exactly one place each and nowhere else:

| Assumption | Value (the one string) | Where |
|---|---|---|
| FRAUD-02 high-value threshold | `200_000_000` VND | `fraud_gate.HIGH_VALUE_LIMIT` + OpenAPI test bodies |
| FRAUD-01 card velocity | `10` auths/card/hour | `fraud_gate.CARD_VELOCITY_LIMIT` |
| FRAUD-03 merchant velocity | `100` auths/merchant/hour | `fraud_gate.MERCHANT_VELOCITY_LIMIT` |
| FRAUD-05 daily cumulative | `1_000_000_000` VND — **sum of authorized amounts** per card per day (not a transaction count; asserted by `test_fraud05_daily_cumulative_is_sum_not_count`) | `fraud_gate.DAILY_CARD_LIMIT` |
| Default merchant reference | `"mer_3"` | `request_handler.authorize` |
| Webhook signing secret (simulated) | `b"simulated-webhook-secret"` | `mocks.MerchantPlatformFake` (also used by Webhook Service) |
| Card test data | Luhn-valid generated PANs (`4` + seed + check digit), exp 12/2030 | `tests/support.make_card` |

Timings that stay labels over the in-process collapse (no real waiting, asserted nowhere as durations):

| Label | Collapsed behaviour |
|---|---|
| CON.2 5s BLPOP concurrent wait | immediate `409 idempotency_conflict` when the key is locked in-flight |
| CON.2 48h TTL / CON.7 30d event TTL | in-memory dicts live for the process; TTL noted in `IdempotencyManager.TTL_SECONDS` |
| CON.6 30s timeout + 1 retry after 5s | labels in `AcquirerClient` docstring — the stub responds instantly, so the timeout alt itself is N/A (not an I-11 named alt) |
| CON.7 retry schedule 1m/5m/30m/2h/12h/24h | attempts counted (`WebhookService.MAX_ATTEMPTS = 7`), no real delays |
