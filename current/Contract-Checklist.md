# Payment API and Webhook Contract Checklist

Status: Draft checklist only; no implementation is included.  
Source: [Requirements.md](Requirements.md), [Modeling-Pack.md](Modeling-Pack.md)  
RACI: R SA  A SA  C DA, Sec, Dev, Test  I Owner, BA, Ops

## Synchronous Payment API relationships

| Relationship | Contract surface | Mode | Required rule |
|---|---|---|---|
| Merchant -> Payment API | `POST /payments` | Sync | `capture` selects authorization or direct charge; idempotency key required. |
| Merchant -> Payment API | `POST /payments/{id}/capture` | Sync | Only `Authorized`; amount <= authorized amount; idempotent. |
| Merchant -> Payment API | `POST /payments/{id}/void` | Sync | Only `Authorized`; no Fraud Engine; idempotent. |
| Merchant -> Payment API | `POST /payments/{id}/refund` | Sync | Only `Captured`; amount <= remaining refundable amount; idempotent. |
| Merchant -> Payment API | `GET /payments/{id}` | Sync | Reads Query Store; no Acquirer, Card Network, or Issuing Bank call. |
| Merchant -> Payment API | `GET /payments` | Sync | Status/date/amount filters and pagination; reads Query Store. |
| Payment Orchestrator -> Fraud Engine | Authorization evaluation | Sync | After validation and idempotency check; pass/block only; not on capture, void, or refund. |
| Acquirer Connector -> Acquirer | Authorization | Sync | Same external reference on retry or status poll. |
| Acquirer Connector -> Acquirer | Capture / void / refund | Sync | Operation-specific command and same-reference idempotency. |
| Acquirer -> Card Network -> Issuing Bank | Payment routing | Sync | External chain; gateway does not own issuer decision. |

## Asynchronous Webhook relationships

| Relationship | Contract surface | Mode | Required rule |
|---|---|---|---|
| Payment Orchestrator -> Webhook Event Queue | Status-change event | Async | Publish after Payment Store status change; does not delay API response. |
| Webhook Event Queue -> Webhook Service | Event consumption | Async | At-least-once handling; duplicate event delivery is possible. |
| Webhook Service -> Merchant | Signed webhook POST | Async | HMAC signature; 2xx marks delivered; failure retries under open policy; exhausted delivery is `failed_delivery`. |

## Contract evidence checklist

- [ ] Request schemas define payment amount, payment method, capture option, metadata, and idempotency key.
- [ ] Response schemas expose only the seven allowed Payment statuses.
- [ ] Capture, void, and refund reject invalid state transitions at the API boundary.
- [ ] Refund responses distinguish partial refund (`Captured`) from full refund (`Refunded`).
- [ ] Acquirer timeout behavior reuses the same external reference; no invented timeout duration or retry count.
- [ ] Webhook payload includes event type, payment data, and HMAC signature.
- [ ] Webhook retry schedule and maximum remain open assumptions until specified.
- [ ] Query responses are backed by Query Store and do not require external payment-system calls.

G4 status: Pass as a contract-design checklist. Contract implementation is outside this drawing pack.
