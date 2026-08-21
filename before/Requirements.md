# Requirements

Source of truth: [Domain.md](Domain.md). This file states *what* the prototype must do. Analysis of those requirements is in [Analysis.md](Analysis.md).

**Domain.** Online Payment Processing — a payment gateway that processes card and digital wallet transactions on behalf of merchants, handling authorization, capture, void, refund, and webhook notification.

**In scope.**

- Payment Authorization
- Payment Capture
- Void & Refund
- Transaction Status Lifecycle
- Webhook Notification

**Out of scope** (will not implement; will not appear as stories): see [Out of scope](#out-of-scope).

Specific acquirer SLAs, network timeout durations, fraud ML models, 3DS flows, multi-currency, and recurring billing are **not specified** and are not requirements.

---

## Actors

| Actor | Type | Role |
|---|---|---|
| Merchant | Primary person/system | Initiates payment operations via API; receives webhooks |
| Customer | External person | Cardholder / payer whose funds are charged |
| Acquirer | External system | Merchant's bank; routes transactions to card networks |
| Card Network | External system | Visa/Mastercard; routes between acquirer and issuer |
| Issuing Bank | External system | Customer's bank; approves or declines authorization |
| Fraud Engine | Supporting service | Rule-based pass/fail gate on authorization path |
| Webhook Service | Supporting service | Async event delivery to merchant endpoints |

There is **no** manual-review actor, dispute-management actor, or card-issuing actor on the payment path.

---

## User stories

### US-01 — Authorize a payment

As a merchant, I want to authorize a payment so that funds are held on the customer's card without capturing them yet.

**Acceptance criteria**

- Given a valid payment request with a new idempotency key, when I submit POST /payments with `capture: false`, then the system validates the request, checks fraud rules, and routes to the acquirer.
- Given the fraud gate passes and the issuer approves, when the acquirer returns an auth code, then the payment status is `Authorized` and a webhook `payment.authorized` is fired.
- Given the fraud gate blocks, when rules fail, then the payment is `Declined` with reason, no acquirer call is made, and a webhook `payment.declined` is fired.
- Given the issuer declines, when the acquirer returns a decline, then the payment is `Declined` with the issuer reason code.
- Given a duplicate idempotency key, when I submit, then the original result is returned without a second acquirer call.
- Given an acquirer timeout, when retry is exhausted, then the payment is `Failed`.

### US-02 — Direct charge (authorize + capture)

As a merchant, I want to authorize and capture in one call so that funds are immediately captured for digital goods or instant fulfillment.

**Acceptance criteria**

- Given a valid payment request with `capture: true`, when I submit, then the system performs authorization and, if approved, immediately captures.
- Given authorization succeeds, when auto-capture completes, then payment status is `Captured` (not `Authorized` then `Captured` visible to merchant — single transition).
- Given authorization fails, when the issuer declines, then payment is `Declined`; no capture is attempted.
- Given capture fails after successful authorization, when the acquirer rejects capture, then payment remains `Authorized` and merchant is notified to retry capture.

### US-03 — Capture an authorized payment

As a merchant, I want to capture a previously authorized payment so that funds are actually transferred.

**Acceptance criteria**

- Given a payment in `Authorized` status, when I submit POST /payments/{id}/capture with an amount ≤ authorized amount, then the acquirer is instructed to capture and payment becomes `Captured`.
- Given capture amount is less than authorized amount (partial capture), when capture succeeds, then the remaining hold may be released (void remainder) or left to expire per acquirer behavior.
- Given a payment not in `Authorized` status, when I submit capture, then the request is rejected with an invalid-state error.
- Given capture amount exceeds authorized amount, when I submit, then the request is rejected.
- Given the authorization has expired (issuer window), when I submit capture, then the acquirer may decline; payment remains `Authorized` and merchant is informed.

### US-04 — Void an authorized payment

As a merchant, I want to void an authorization so that the hold on the customer's card is released without capturing.

**Acceptance criteria**

- Given a payment in `Authorized` status, when I submit POST /payments/{id}/void, then the acquirer releases the hold and payment becomes `Voided`.
- Given a payment already `Captured`, when I submit void, then the request is rejected (use refund instead).
- Given a payment already `Voided`, `Declined`, or `Failed`, when I submit void, then the request is rejected (no-op or error).
- Given a successful void, when status changes, then webhook `payment.voided` is fired.

### US-05 — Refund a captured payment

As a merchant, I want to refund a captured payment so that the customer receives their money back.

**Acceptance criteria**

- Given a payment in `Captured` status, when I submit POST /payments/{id}/refund with amount ≤ (captured amount - already refunded amount), then the acquirer processes the refund.
- Given a full refund (amount equals captured), when the refund succeeds, then payment status becomes `Refunded` and webhook `payment.refunded` fires.
- Given a partial refund, when the refund succeeds, then payment remains `Captured` with `refunded_amount` updated; multiple partial refunds allowed up to captured amount.
- Given refund amount exceeds remaining refundable amount, when I submit, then the request is rejected.
- Given a payment not in `Captured` status, when I submit refund, then the request is rejected.
- Given a refund request with an idempotency key already used, when I submit, then the original refund result is returned.

### US-06 — Transaction status lifecycle

As a merchant, I want each payment to follow a defined status lifecycle so that I always know the current state of a transaction.

**Acceptance criteria**

- Allowed statuses are only: `Pending`, `Authorized`, `Captured`, `Voided`, `Refunded`, `Declined`, `Failed`.
- `Pending` means the request is received and processing is in flight (acquirer call in progress).
- `Authorized` means issuer approved; funds held.
- `Captured` means funds captured; settlement queued.
- `Voided` means authorization cancelled; hold released.
- `Refunded` means full refund processed (partial refunds keep status `Captured` with tracked refunded amount).
- `Declined` means issuer or fraud rules rejected.
- `Failed` means system/network error; no successful outcome.
- Invalid transitions are rejected at the API level (e.g., void after capture, capture after void).

### US-07 — Idempotent operations

As a merchant, I want all write operations to be idempotent so that network retries do not cause double-charges or double-refunds.

**Acceptance criteria**

- Given a stable idempotency key on POST /payments, when the same key is submitted again, then the original authorization result is returned; no second acquirer call, no second fraud check.
- Given a stable idempotency key on POST /payments/{id}/capture, when retried, then the original capture result is returned.
- Given a stable idempotency key on POST /payments/{id}/refund, when retried, then the original refund result is returned.
- Given a **different** idempotency key, when submitted, then it is a new operation.
- Given an acquirer timeout where the outcome is unknown, when the same key is retried, then the system polls acquirer status or retries the same message; it does not initiate a new transaction.

### US-08 — Webhook notification

As a merchant, I want to receive webhook notifications when payment status changes so that my system stays synchronized without polling.

**Acceptance criteria**

- Given a payment status change, when it occurs, then an event is published asynchronously and delivered to the merchant's registered webhook URL.
- Given a successful delivery (merchant returns 2xx), when the webhook is sent, then it is marked delivered.
- Given the merchant endpoint is down, when delivery fails, then the system retries with exponential backoff up to a maximum retry count.
- Given maximum retries exhausted, when all fail, then the event is marked `failed_delivery` and available via API for merchant to poll.
- Given webhook delivery, when the merchant receives it, then the payload includes an HMAC signature for verification.
- Webhook delivery must **not** block or slow down the synchronous payment API response.

### US-09 — Query payment details

As a merchant, I want to query the current state of a payment so that I can reconcile or display status to my customer.

**Acceptance criteria**

- Given a payment ID, when I submit GET /payments/{id}, then I receive the full payment object including status, amount, payment method (masked), timestamps, and metadata.
- Given a list request, when I submit GET /payments with filters (status, date range, amount range), then I receive paginated results.
- Given a query, when I request it, then it is served from the gateway's own data store, not by calling the acquirer or card network in real time.

---

## Non-functional / quality

Only qualities implied by Domain.md. No specific latency numbers, availability SLAs, or acquirer timeouts.

| ID | Quality | Requirement |
|---|---|---|
| NFR-01 | Idempotency | Same idempotency key must not produce duplicate acquirer calls, double-charges, or double-refunds (US-07). |
| NFR-02 | Async webhook | Webhook delivery must not block the synchronous payment response path (US-08). |
| NFR-03 | Read independence | Payment queries (GET) must be answerable from the gateway's own store without calling acquirer or card network (US-09). |
| NFR-04 | Fraud gate position | Fraud rules must execute **after** validation but **before** acquirer routing; must not appear on capture/void/refund paths (Domain fraud gate). |
| NFR-05 | State integrity | Payment status transitions must be enforced; invalid transitions rejected (US-06). Only the defined status set is allowed. |

---

## Out of scope

Will not implement; will not appear in stories or as actors on the payment path.

- Card Issuing
- Recurring Billing / Subscriptions
- Dispute & Chargeback Management
- 3D Secure Authentication
- Multi-currency / FX
- Physical POS / In-store Payments
- KYC / AML

---

## Not specified

These are **not** requirements. Do not invent values in stories. Recorded as open assumptions in [Analysis.md](Analysis.md).

- Acquirer timeout duration or retry count
- Authorization expiry window (issuer-defined, varies)
- Specific fraud rule thresholds (velocity count, amount ceiling, geo list)
- Webhook retry schedule (intervals and max count)
- Settlement timing and batching frequency
- Whether partial capture voids the remainder or lets it expire
- Specific card networks supported (Visa, Mastercard, JCB, etc.)
- Merchant onboarding and API key provisioning process
- Rate limiting thresholds per merchant
