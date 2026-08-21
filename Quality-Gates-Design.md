# Quality gates — Design

**Unused — Lab 7 G1–G6 only.** Team 3 adopted the Guide's G1–G6 gates in `Lb/Lab7-Adoption.md`; this DG-\* checklist is a competing gate list and is not applied. Kept for reference only.

---

Reviewer checklist for a **logical / solution design** pack (UML behavior and domain design). C4 context/container is gated by [Quality-Gates-Architecture.md](Quality-Gates-Architecture.md), not this file.

**Source of truth.** [Domain.md](Domain.md), [Requirements.md](Requirements.md) (US-01…US-09, NFR-01…NFR-05), [Analysis.md](Analysis.md) (BR-01…BR-18, OA-01…OA-10).

**When applied.** Before accepting `Design.md` or any UML diagram pack for this prototype.

**Pass rule.** The pack **fails** if any **Must** row is Fail, if any automatic-fail anti-pattern is present, or if an open assumption (OA-*) is treated as a decided product rule. **Should** rows do not block; they must still be marked Pass, Fail, or N/A with a comment.

Notation (PlantUML, Mermaid, or other) is free. Content is not.

---

## Sign-off

**Pack title:** _______________  
**Author:** _______________  
**Reviewer:** _______________  
**Date:** _______________

**Approval:** [ ] Approved  [ ] Changes requested

---

## Required contents

The design pack must contain all of the following. Missing a section is Fail for the matching Must row.

| # | Section / artifact | Must show |
|---|---|---|
| D1 | Scope | Pointers to Domain / Requirements / Analysis; in-scope US-01…US-09; out-of-scope reminder (card issuing, recurring billing, disputes, 3DS, multi-currency, POS, KYC/AML) |
| D2 | Domain / class design | `Payment`, `PaymentMethod`, `WebhookEvent`, `FraudRule` with the same identities as Analysis (`idempotencyKey`, `status`, `amount`, `capturedAmount`, `refundedAmount`, `authCode`; webhook `deliveryStatus`, `attempts`) |
| D3 | Sequence — authorization | US-01: Merchant → validate → idempotency check → **Fraud gate** → Acquirer → response. Fraud gate **before** Acquirer |
| D4 | Sequence — direct charge | US-02: Same as auth sequence + immediate capture to Acquirer in one flow. If auth fails, no capture. If capture fails after auth, remains `Authorized` |
| D5 | Sequence — capture | US-03: Merchant → validate status=Authorized → Acquirer capture. **No** Fraud Engine |
| D6 | Sequence — void | US-04: Merchant → validate status=Authorized → Acquirer void. **No** Fraud Engine |
| D7 | Sequence — refund | US-05: Merchant → validate status=Captured, amount valid → Acquirer refund. **No** Fraud Engine. Partial vs full refund logic |
| D8 | State machine | Only `Pending`, `Authorized`, `Captured`, `Voided`, `Refunded`, `Declined`, `Failed`. No `PendingApproval`, `Disputed`, `AwaitingAuthentication` |
| D9 | Webhook | Sequence or activity: status change → event published to queue → Webhook Service delivers with retry. Async boundary explicit. Not blocking payment response |
| D10 | Idempotency | Alt/opt: same `idempotencyKey` returns cached result vs new key is a new operation. On authorize, capture, and refund paths (US-07, BR-04…06) |
| D11 | Fail paths | Fraud block (BR-02); issuer decline (BR-03); acquirer timeout + retry (BR-06); invalid state transition (BR-07); refund exceeds captured (BR-09); capture exceeds authorized (BR-11) |
| D12 | BR evidence table | Every BR-01…BR-18 mapped to a named diagram fragment. Empty cell = Fail for that BR |
| D13 | Open assumptions | OA-01…OA-10 listed as open (or closed only by a requirement change). Do not invent timeout durations, fraud thresholds, webhook intervals, SLAs |

---

## Automatic Fail (anti-patterns)

Any one of these is Fail for the whole pack, even if other rows pass.

- `PendingApproval`, `Disputed`, `AwaitingAuthentication` status, staff/review actor, or approval queue
- Card Issuing, Recurring Billing, Dispute/Chargeback, 3DS/ACS, POS, KYC/AML, SWIFT participant
- Fraud Engine on capture, void, or refund sequence
- **One** posting sequence used for both authorization and capture (stereotype or label only)
- Webhook delivery shown as synchronous / blocking the payment API response
- Payment query sequence calling Acquirer or Card Network
- Invented numeric acquirer timeout, fraud thresholds, webhook intervals, TPS, or availability presented as product fact (OA-01, OA-03, OA-04, OA-09)
- Settlement timing or batch frequency as a design decision without requirement basis
- OA-* silently closed (acquirer SLA, fraud rules, webhook schedule, rate limits, currency)

---

## Review checklist

Mark Pass or Fail. Comment is required on Fail.

| ID | Check | Must/Should | Trace | Pass | Fail | Comment |
|---|---|---|---|---|---|---|
| DG-01 | Scope lists US-01…US-09 and the Domain out-of-scope list | Must | D1, Domain | | | |
| DG-02 | Class/domain model includes `Payment`, `PaymentMethod`, `WebhookEvent`, `FraudRule` with Analysis identities | Must | D2, Analysis §2 | | | |
| DG-03 | Separate sequences for: authorization (US-01), direct charge (US-02), capture (US-03), void (US-04), refund (US-05) | Must | D3–D7 | | | |
| DG-04 | Authorization sequence: Fraud gate **after** validation, **before** Acquirer | Must | BR-01, NFR-04, D3 | | | |
| DG-05 | Capture sequence has **no** Fraud Engine participant | Must | BR-18, D5 | | | |
| DG-06 | Void sequence has **no** Fraud Engine participant | Must | BR-18, D6 | | | |
| DG-07 | Refund sequence has **no** Fraud Engine participant | Must | BR-18, D7 | | | |
| DG-08 | Void precondition: payment status must be `Authorized`; reject otherwise | Must | BR-08, US-04 | | | |
| DG-09 | Refund precondition: payment status must be `Captured`; amount ≤ (captured - refunded) | Must | BR-09, US-05 | | | |
| DG-10 | Capture precondition: payment status must be `Authorized`; amount ≤ authorized | Must | BR-11, US-03 | | | |
| DG-11 | Partial refund: payment remains `Captured` with `refundedAmount` updated; full refund → `Refunded` | Must | BR-10, US-05 | | | |
| DG-12 | Direct charge: auth + capture in one flow; auth fail → no capture; capture fail after auth → remains `Authorized` | Must | BR-12, US-02 | | | |
| DG-13 | State machine has only: `Pending`, `Authorized`, `Captured`, `Voided`, `Refunded`, `Declined`, `Failed` | Must | BR-07, US-06, D8 | | | |
| DG-14 | No `PendingApproval`, `Disputed`, or `AwaitingAuthentication` status | Must | Domain out of scope, US-06 | | | |
| DG-15 | Idempotency: same key → return cached result, no second acquirer call, no second fraud check | Must | BR-04, NFR-01, US-07, D10 | | | |
| DG-16 | Idempotency: different key → new operation | Must | BR-05, US-07 | | | |
| DG-17 | Acquirer timeout: retry with same reference (poll or identical message), not a new transaction | Must | BR-06, US-07 | | | |
| DG-18 | Fraud gate block → `Declined` with reason, no acquirer call | Must | BR-02, US-01 | | | |
| DG-19 | Issuer decline → `Declined` with reason code, no capture attempted | Must | BR-03, US-01 | | | |
| DG-20 | Invalid card data (Luhn, expired) rejected before Acquirer | Must | BR-17, US-01 | | | |
| DG-21 | Webhook: event published to queue **after** status change; delivery is async, does not block API response | Must | BR-13, NFR-02, D9 | | | |
| DG-22 | Webhook: at-least-once delivery with retry on failure; HMAC signature in payload | Must | BR-14, BR-15, US-08 | | | |
| DG-23 | Payment query: read from gateway store, no Acquirer/Network call | Must | BR-16, NFR-03, US-09 | | | |
| DG-24 | BR evidence table has a diagram fragment for **each** of BR-01…BR-18 (empty cell = Fail) | Must | D12 | | | |
| DG-25 | OA-01…OA-10 are listed as open; no invented timeout durations, fraud thresholds, webhook intervals | Must | D13, OA-01…OA-10 | | | |
| DG-26 | No automatic-fail anti-pattern from the list above | Must | Domain out of scope | | | |
| DG-27 | Participants named consistently with Analysis (Merchant, Acquirer, Card Network, Issuing Bank, Fraud Engine, Webhook Service) | Should | Analysis §2 | | | |
| DG-28 | Invalid state transitions shown as explicit reject (not silent no-op) | Should | BR-07, NFR-05 | | | |
| DG-29 | Webhook retry with exponential backoff and max-retry-exhausted path shown | Should | US-08, OA-04 | | | |
| DG-30 | Direct charge shows transient `Authorized` as internal (not exposed to merchant as visible state) | Should | BR-12, US-02 | | | |

---

## BR evidence table (required in the design pack)

Copy into the design pack. Reviewer fails DG-26 if any Evidence cell is empty.

| BR | Rule (short) | Evidence (diagram / section name) |
|---|---|---|
| BR-01 | Fraud gate after validation, before acquirer; auth only | |
| BR-02 | Fraud block → Declined, no acquirer call | |
| BR-03 | Issuer decline → Declined, no capture | |
| BR-04 | Same idem key → cached result, no second acquirer call | |
| BR-05 | Different idem key → new operation | |
| BR-06 | Acquirer timeout → idempotent retry, not new transaction | |
| BR-07 | State transitions enforced; invalid rejected | |
| BR-08 | Void valid only on Authorized | |
| BR-09 | Refund valid only on Captured; amount ≤ remaining | |
| BR-10 | Partial refund: Captured + refundedAmount; full → Refunded | |
| BR-11 | Capture valid only on Authorized; amount ≤ auth | |
| BR-12 | Direct charge: auth + capture; capture fail → remains Authorized | |
| BR-13 | Webhook async, not blocking payment response | |
| BR-14 | Webhook at-least-once with retry | |
| BR-15 | Webhook HMAC signature | |
| BR-16 | Query from gateway store, no external call | |
| BR-17 | Invalid card data rejected before acquirer | |
| BR-18 | Fraud gate NOT on capture/void/refund | |
