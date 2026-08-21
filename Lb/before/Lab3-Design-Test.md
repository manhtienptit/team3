# Lab 3 — Design and Test Evidence

**R:** Dev · Test · **A:** SA

---

Design evidence for gates G4–G6 (checked later, not implemented here). Still no code, no running services, no deployed stack — only the six artifacts below, drawn from Lab 1's locked index.

---

## 1. Build List

One row per I-4 container (all eight). Build order follows dependency: data/queue layers first, then orchestration, then the edge.

| # | Container (I-4) | Dev Owner | Environment (I-9) |
|---|------------------|-----------|--------------------|
| 1 | Payment Store | Kim Đức Minh | Database Tier |
| 2 | Query Store | Kim Đức Minh | Database Tier |
| 3 | Idempotency Store | Kim Đức Minh | Cache Tier |
| 4 | Message Queue | Kim Đức Minh | Queue Tier |
| 5 | Payment Orchestrator | Kim Đức Minh | Application Tier |
| 6 | API Gateway | Kim Đức Minh | Application Tier |
| 7 | Webhook Service | Kim Đức Minh | Worker Tier |
| 8 | Expiry Job | Kim Đức Minh | Scheduler |

---

## 2. To-Be Component — Payment Orchestrator

Modules inside `Payment Orchestrator` only (matches Lab 9 §3). Neighbours stay black boxes, not exploded. `Fraud Engine` is not a container — its evaluation is the `Fraud Gate` module below.

| Module | Responsibility |
|--------|----------------|
| Request Handler | Receives requests from API Gateway; routes to flow |
| Input Validator | Validates amount (CON.1), card (Luhn, expiry) |
| Idempotency Manager | Check/lock/cache via Idempotency Store (CON.2) |
| Fraud Gate | Evaluates 5 fraud rules in-process, auth path only (CON.3) |
| State Machine Engine | Enforces valid transitions; rejects invalid with 409 |
| Acquirer Client | Talks to AcquirerHost; 30s timeout + 1 retry (CON.6) |
| Persistence Manager | Writes payment records to Payment Store |
| Event Publisher | Publishes events to Message Queue |

**Neighbours (black boxes):** `API Gateway`, `Idempotency Store`, `Payment Store`, `Message Queue`, `AcquirerHost`.

---

## 3. To-Be Sequence — Authorize Payment (I-11)

Every message is owned by a `Payment Orchestrator` module or a neighbour container.

| # | From | To | Message |
|---|------|----|---------|
| 1 | Merchant Platform | API Gateway | POST /v1/payments |
| 2 | API Gateway | Request Handler | forward validated request |
| 3 | Request Handler | Input Validator | validate(amount, card) |
| 4 | Request Handler | Idempotency Manager | check(idempotency_key) |
| 5 | Idempotency Manager | Idempotency Store | GET/SET idempotency key |
| 6 | Request Handler | Fraud Gate | evaluate(card, amount, merchant) |
| 7 | Request Handler | State Machine Engine | validateTransition(null → Pending) |
| 8 | Request Handler | Acquirer Client | authorize(card_ref, amount) |
| 9 | Acquirer Client | AcquirerHost | HTTPS authorize |
| 10 | Request Handler | Persistence Manager | persist(Payment{status: Authorized}) |
| 11 | Persistence Manager | Payment Store | INSERT Payment |
| 12 | Request Handler | Event Publisher | publish(payment.authorized) |
| 13 | Event Publisher | Message Queue | produce event |
| 14 | API Gateway | Merchant Platform | 201 Authorized |

**alt: Fraud Block [CON.3]**

| # | From | To | Message |
|----|------|----|---------|
| 6a | Fraud Gate | Request Handler | blocked(FRAUD-XX) |
| 6b | Request Handler | Persistence Manager | persist(Payment{status: Declined, fraud_rule}) |
| 6c | Request Handler | Event Publisher | publish(payment.declined) |
| 6d | API Gateway | Merchant Platform | 200 Declined |

No `AcquirerHost` call on this branch (CON.3).

---

## 4. Contract Register (I-8)

One row per I-8 relationship.

| Producer | Consumer | Mode | Operation / Event |
|----------|----------|------|--------------------|
| API Gateway | Payment Orchestrator | Sync | Forward validated request (HTTP/gRPC) |
| Payment Orchestrator | Idempotency Store | Sync | GET/SET/BLPOP idempotency key |
| Payment Orchestrator | AcquirerHost | Sync | authorize / capture / void / refund |
| Payment Orchestrator | Message Queue | Async | publish payment.* event |
| Message Queue | Webhook Service | Async | consume payment.* event |
| Webhook Service | Merchant Platform | Async | POST webhook (HMAC-SHA256) |

No new externals. `Merchant Platform`, `AcquirerHost`, `NAPAS Switch`, `Issuing Bank` are the only I-3 names.

---

## 5. Exception Spec (Critical CON.* Paths)

| CON | Trigger | Compensating Action | Who Performs It |
|-----|---------|----------------------|-------------------|
| CON.3 | Any fraud rule blocks (FRAUD-01→05) | Payment → Declined, no acquirer call | Fraud Gate (Payment Orchestrator) |
| CON.6 | AcquirerHost times out (30s), retry also times out | Payment → Failed, same transaction reference — no duplicate charge | Acquirer Client (Payment Orchestrator) |

---

## 6. Test Spec

One row per I-6 transition, plus the fraud-block `alt`. SUT is an I-4 name only.

| # | From | Trigger | To | SUT |
|---|------|---------|----|----|
| 1 | Pending | Issuer approves (capture:false) | Authorized | Payment Orchestrator |
| 2 | Pending | Issuer approves + immediate capture (Direct Charge) | Captured | Payment Orchestrator |
| 3 | Pending | Fraud blocks (`alt`, CON.3) | Declined | Payment Orchestrator |
| 4 | Pending | Issuer declines | Declined | Payment Orchestrator |
| 5 | Pending | Timeout/error (CON.6) | Failed | Payment Orchestrator |
| 6 | Authorized | Capture succeeds | Captured | Payment Orchestrator |
| 7 | Authorized | Void succeeds | Voided | Payment Orchestrator |
| 8 | Authorized | Auth expires (7d) | Failed | Expiry Job |
| 9 | Captured | Full refund | Refunded | Payment Orchestrator |
| 10 | Captured | Partial refund | Captured (refundedAmount updated) | Payment Orchestrator |
