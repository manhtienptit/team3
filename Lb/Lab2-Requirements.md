# Lab 2 — Requirements and Analysis

**R:** BA (requirements) · EA (trace to Motivation) · **A:** Owner

---

## 1. Requirements List

Each requirement traces to Goal, a CON.*, a process step, or a state.

| ID | Requirement | Priority | Traces to |
|----|-------------|----------|-----------|
| REQ-01 | Merchant can authorize a card payment (hold funds) via POST /v1/payments with capture:false | High | Goal, I-5 step 1, State: Authorized |
| REQ-02 | Merchant can direct-charge (auth + capture in one call) via POST /v1/payments with capture:true | High | Goal, State: Pending → Captured |
| REQ-03 | Merchant can capture an authorized payment within 7-day window | High | CON.4, State: Authorized → Captured |
| REQ-04 | Merchant can void an authorized payment (release hold) | High | State: Authorized → Voided |
| REQ-05 | Merchant can refund a captured payment (full or partial, max 10, within 180d) | High | CON.5, State: Captured → Refunded |
| REQ-06 | System enforces state machine — invalid transitions rejected with 409 | High | I-6 transitions, CON.4/CON.5 |
| REQ-07 | Every POST operation requires idempotency key (max 64 chars, 48h TTL) | High | CON.2, I-5 step 3 |
| REQ-08 | Fraud rules evaluate on authorization path only, < 50ms (in-process module in Payment Orchestrator) | High | CON.3, I-5 step 4 |
| REQ-09 | Acquirer call: 30s timeout + 1 retry after 5s on timeout | High | CON.6, I-5 step 5 |
| REQ-10 | Webhook fires asynchronously on every status change (HMAC-SHA256, 7 attempts) to Merchant Platform | High | CON.7, I-5 step 8–9 |
| REQ-11 | Payment query served from Query Store only, no external calls | Medium | I-8 |
| REQ-12 | Amount validation: 10,000–500,000,000 VND; card Luhn + expiry check | High | CON.1, I-5 step 2 |
| REQ-13 | Authorization expires after 7 days — Expiry Job transitions to Failed | High | CON.4, State: Authorized → Failed |
| REQ-14 | Concurrent same idempotency key: second request waits 5s → 409 if timeout | High | CON.2 |
| REQ-15 | Fraud block → Declined immediately, no acquirer call | High | CON.3, I-5 step 4 |
| REQ-16 | Partial capture: one allowed; remainder auto-voided | Medium | State: Authorized → Captured |
| REQ-17 | System targets: P95 < 2s, 500 TPS sustained, 99.9% availability | High | Goal (outcome) |

---

## 2. Analysis

### 2.1 As-Is vs To-Be

| Aspect | As-Is (Baseline) | To-Be (Target) |
|--------|-------------------|----------------|
| Payment method | Manual bank transfer | Real-time card authorization (Visa/MC) |
| Settlement | T+2 manual reconciliation | Real-time auth + capture on demand |
| Fraud protection | None | 5-rule in-process module on auth path (< 50ms) |
| Duplicate protection | Manual check | Automated idempotency (Idempotency Store, 48h TTL) |
| Notification | Email (delayed) | Webhook to Merchant Platform (async, < 1s publish, HMAC signed) |
| Query | Call bank for status | Self-served from Query Store |
| Auth expiry | Manual follow-up | Automated Expiry Job (hourly, 7d window) |
| Refund | Bank form (days) | API-driven, partial supported (max 10, 180d) |

### 2.2 Capabilities Implied by the Goal

| Capability | Containers involved | Key constraint |
|------------|---------------------|----------------|
| Card Authorization | Payment Orchestrator (with fraud module), AcquirerHost | CON.1 (VND), CON.6 (30s timeout) |
| Idempotent Processing | Payment Orchestrator, Idempotency Store | CON.2 (48h, 64 chars, 5s wait) |
| Fraud Detection | Payment Orchestrator (in-process fraud module), Idempotency Store (counters) | CON.3 (auth only), CON.8 (BIN=VN) |
| Post-Auth Operations | Payment Orchestrator, AcquirerHost | CON.4 (7d), CON.5 (10 refunds, 180d) |
| Async Notification | Message Queue, Webhook Service, Webhook Event Store → Merchant Platform | CON.7 (7 attempts, HMAC) |
| Query Independence | Query Store | No external dependency |
| Auto-Expiry | Expiry Job, Payment Store | CON.4 (hourly, 7d) |

### 2.3 Exception Paths Named

| Exception | Trigger | Outcome | Process impact |
|-----------|---------|---------|----------------|
| Fraud Block | Any of FRAUD-01→05 triggers | Payment → Declined | No acquirer call; webhook fires to Merchant Platform |
| Issuer Decline | Issuing Bank rejects | Payment → Declined | Webhook fires |
| Acquirer Timeout | 30s + retry exhausted | Payment → Failed | Webhook fires |
| Idempotency Duplicate | Same key within 48h | Return cached response | No processing |
| Idempotency Conflict | Concurrent same key, 5s timeout | HTTP 409 | Request rejected |
| Invalid State Transition | e.g., void on Captured | HTTP 409 | No external call |
| Auth Expired | 7d elapsed, Expiry Job | Authorized → Failed | Webhook fires |
| Amount Exceeds | Capture > authorized, refund > remaining | HTTP 400 | No external call |
| Max Refunds | Count ≥ 10 | HTTP 400 | No external call |
| Refund Window Expired | > 180 days since capture | HTTP 409 | No external call |

---

## 3. Trace Table

| Requirement ID | Process Step (I-5) | Constraint | Named Object / State |
|----------------|-------------------|------------|---------------------|
| REQ-01 | Step 1, 5, 6, 7 | — | Payment: Pending → Authorized |
| REQ-02 | Step 1, 5, 6, 7 (+ immediate capture) | — | Payment: Pending → Captured |
| REQ-03 | (Capture flow) | CON.4 | Payment: Authorized → Captured |
| REQ-04 | (Void flow) | — | Payment: Authorized → Voided |
| REQ-05 | (Refund flow) | CON.5 | Payment: Captured → Refunded / Captured |
| REQ-06 | All flows (validation) | CON.4, CON.5 | All states: invalid → 409 |
| REQ-07 | Step 3 | CON.2 | Idempotency Entry |
| REQ-08 | Step 4 | CON.3 | Payment: Pending → Declined (if block) |
| REQ-09 | Step 5 | CON.6 | Payment: Pending → Failed (if exhausted) |
| REQ-10 | Step 8, 9 | CON.7 | Webhook Event |
| REQ-11 | (Query flow) | — | Payment (read from Query Store) |
| REQ-12 | Step 2 | CON.1 | — (validation, no state change) |
| REQ-13 | (Expiry Job) | CON.4 | Payment: Authorized → Failed |
| REQ-14 | Step 3 (concurrent) | CON.2 | Idempotency Entry |
| REQ-15 | Step 4 (block) | CON.3 | Payment: Pending → Declined |
| REQ-16 | (Capture flow, partial) | CON.4 | Payment: Authorized → Captured |
| REQ-17 | All flows | — | NFR (system-wide) |
