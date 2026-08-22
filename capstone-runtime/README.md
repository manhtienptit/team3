# Capstone runtime — Payment Gateway (extended sitting)

Implementation of what Labs 1–10 designed. The first sitting covered the
**I-11 slice** (Authorize, Capture, Refund). This **extension** closes the
remaining Lab 1 in-scope items: **Void Payment**, **Payment Query**,
**Expiry Job** (CON.4), **CON.6 timeout**, and the **security properties**
(S1–S11) named in I-4 / I-5 / I-9 / CON.*. No new I-3, I-4, I-6 state,
actor, or product.

This folder is a sibling of the modelling packs (`Lb/`); nothing here lives
inside the before pack, the after pack, or the Lab 7 file, and no Lab 1–10
file was edited to match the code.

**RACI (extension sitting):** Dev **R** Kim Đức Minh · SA **A** Nguyễn Quang Huy · Test **C** Trần Quốc Đạt

---

## Run

```bash
cd capstone-runtime
WEBHOOK_SECRET=test-secret python3 -m unittest discover -s tests -t . -v  # 101 tests
WEBHOOK_SECRET=demo-secret python3 -m payment_gateway.demo                # 12-minute demo script
```

Python 3 standard library only — no dependencies, no cluster, no live host.

**S1:** `WEBHOOK_SECRET` must be set (environment variable or constructor
arg). The runtime refuses to start without it — no hardcoded default in source.

## What is here

| File that counts | Where |
|---|---|
| Runnable runtime (sibling folder) | `payment_gateway/` (composition root: `payment_gateway/runtime.py`) |
| OpenAPI (committed file — G4) | `openapi.json` |
| Automated tests | `tests/` (101 tests: I-11 paths, extension paths, G5 compensation, I-5/I-9/S1–S11 security, OpenAPI drift, agent contract A1–A10) |
| Name-identity map (module/package → I-4, collapse + ASSUMPTION rows) | `name-map.md` |
| Spec-trace (path → OpenAPI operation → test id, G5, G6, N/A) | `spec-trace.md` |
| I-3 mock list | §"I-3 mocks" below |

Runtime shape: `PaymentGatewayRuntime.handle(method, path, body) → (status, body)`
is the Merchant-facing surface described by `openapi.json`; the async half is
`drain_webhooks()`, which delivers queued events — never inside the sync
response (I-5). `tick_expiry(now)` runs the Expiry Job sweep (CON.4).

## In-scope operations (extension sitting)

| Operation | Method + Path | Use case |
|---|---|---|
| `authorizePayment` | `POST /v1/payments` | Authorize Payment (I-11) |
| `capturePayment` | `POST /v1/payments/{id}/capture` | Capture Payment (I-11) |
| `voidPayment` | `POST /v1/payments/{id}/void` | Void Payment (extension) |
| `refundPayment` | `POST /v1/payments/{id}/refund` | Refund Payment (I-11) |
| `getPayment` | `GET /v1/payments/{id}` | Payment Query (extension) |
| `receiveWebhook` | `POST /webhooks` | Webhook delivery contract (Lab 3 §4) |

## I-3 mocks (no real host, no production credentials)

| Mock | Stands for (I-3 name) | Kind | Notes |
|---|---|---|---|
| `payment_gateway/mocks.py :: AcquirerHostStub` | **AcquirerHost** | stub | Records calls; `timeout_next_n` simulates CON.6. Internally stands for AcquirerHost → **NAPAS Switch** → **Issuing Bank** chain — labels only |
| `payment_gateway/mocks.py :: MerchantPlatformFake` | **Merchant Platform** | in-process fake | Receives webhooks, verifies HMAC-SHA256 (S2); `fail_first_n` scripts CON.7 retries; holds **no reference** to the acquirer (I-9) |
| `tests/support.py :: make_card` | simulated card data | generator | Luhn-valid generated PANs — no real customer data |

## Collapse (documented in `name-map.md` §2)

One process · in-memory stores · in-process bus. `PaymentGatewayRuntime`
stands for the I-9 locations (Application / Cache / Database / Queue / Worker
Tier); every I-4 container keeps its exact Lab 1 string and its module
boundaries inside the process. Sync = direct in-process call; async =
`publish()` → `drain()`.

Extension adds:
- **Query Store** — in-memory read model of Payment Store (Database Tier read-replica)
- **Expiry Job** — in-process `tick(now)` (Scheduler)
- **Rate Limiter** — in `APIGateway` (API Gateway I-4 named responsibility)

Lab 1 **out-of-scope** items remain out: Tokenization, 3DS, KYC, etc.

## Security properties (Slice B)

| # | Property | Enforcement | Test |
|---|---|---|---|
| S1 | WEBHOOK_SECRET not in source | Runtime refuses to start without env var | `test_s1_*` |
| S2 | HMAC-SHA256 webhook signature | Wrong sig → delivery rejected | `test_s2_*` |
| S3 | No full PAN stored/returned | card_ref = last 4 only | `test_s3_*` |
| S4 | Query never calls AcquirerHost | Structural (QueryStore reads PaymentStore) | `test_s4_*` |
| S5 | Fraud never on void | CON.3 / I-5 (auth-path only) | `test_s5_*` |
| S6 | Webhook Service cannot write Payment | PermissionError (I-9) | `test_s6_*` |
| S7 | Merchant Platform cannot call AcquirerHost | Structural absence (I-9) | `test_s7_*` |
| S8 | Query Store cannot write Payment | PermissionError (I-7) | `test_s8_*` |
| S9 | Rate limiting (100 req/merchant/60s) | 429 rate_limit_exceeded | `test_s9_*` |
| S10 | Idempotency before fraud/acquirer | Order log assertion (I-5) | `test_s10_*` |
| S11 | CON.6 no duplicate charge | Same ref, Payment Failed | `test_s11_*` |

## Demo script (order per extension spec)

`WEBHOOK_SECRET=demo-secret python3 -m payment_gateway.demo` prints, in order:

1. **I-1 goal** — exact Lab 1 strings
2. **One I-11 / Lab 9 sequence on screen** — Payment Query or Expiry, Lab 10 names
3. **Live Query happy path** — GET → 200 with card_ref (last 4)
4. **Live Void happy path** — POST → 200 Voided
5. **Live Expiry Job** — tick → Authorized → Failed
6. **Live CON.6 timeout** — acquirer exhaust → Pending → Failed (same ref)
7. **Live named security attempt** — S8 Query Store write → PermissionError
8. **Test report** — the full unittest suite result

## SA acceptance (Human A accepts)

The extended runtime traces to Labs 1–10 + `openapi.json` + extension spec;
the drift test pins the document to the running API in both directions.

| Role | Person | Sign-off |
|---|---|---|
| Dev (R) | Kim Đức Minh | built; all 101 tests green 2026-08-24 |
| SA (A) | Nguyễn Quang Huy | ☑ accepted the agent-contract runtime against the after pack — 2026-08-24 |
| Test (C) | Trần Quốc Đạt | ☑ test report reviewed — 101 pass, 0 fail — 2026-08-24 |
