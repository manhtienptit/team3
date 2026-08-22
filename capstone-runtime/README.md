# Capstone runtime — Payment Gateway (I-11 slice)

Implementation of what Labs 1–10 designed. **Scope is I-11 only**: the three
named use cases — **Authorize Payment**, **Capture Payment**, **Refund
Payment** — each with its happy path **and** the `alt` named in I-11. This
folder is a sibling of the modelling packs (`Lb/`); nothing here lives inside
the before pack, the after pack, or the Lab 7 file, and no Lab 1–10 file was
edited to match the code.

**RACI (capstone sitting):** Dev **R** Kim Đức Minh · SA **A** Nguyễn Quang Huy · Test **C** Trần Quốc Đạt

---

## Run

```bash
cd capstone-runtime
python3 -m unittest discover -s tests -t . -v   # 39 tests, all must pass
python3 -m payment_gateway.demo                 # 10-minute demo script
```

Python 3 standard library only — no dependencies, no cluster, no live host.

## What is here

| File that counts | Where |
|---|---|
| Runnable I-11 (sibling folder/repo) | `payment_gateway/` (composition root: `payment_gateway/runtime.py`) |
| OpenAPI (committed file — G4) | `openapi.json` |
| Automated tests | `tests/` (39 tests: I-11 paths, G5 compensation, I-5/I-9 negative, FRAUD-05 sum, engine transitions, OpenAPI drift) |
| Name-identity map (module/package → I-4, collapse + ASSUMPTION rows) | `name-map.md` |
| Spec-trace (path → OpenAPI operation → test id, G5, G6, N/A) | `spec-trace.md` |
| I-3 mock list | §”I-3 mocks” below |

Runtime shape: `PaymentGatewayRuntime.handle(method, path, body) → (status, body)`
is the Merchant-facing surface described by `openapi.json`; the async half is
`drain_webhooks()`, which delivers queued events — never inside the sync
response (I-5).

## I-3 mocks (no real host, no production credentials)

| Mock | Stands for (I-3 name) | Kind | Notes |
|---|---|---|---|
| `payment_gateway/mocks.py :: AcquirerHostStub` | **AcquirerHost** | stub | Records every call so tests assert “no acquirer call” (CON.3, G5). Internally stands for the AcquirerHost → **NAPAS Switch** → **Issuing Bank** chain — those names stay labels; the stub never opens a socket |
| `payment_gateway/mocks.py :: MerchantPlatformFake` | **Merchant Platform** | in-process fake | Receives webhook deliveries and verifies HMAC-SHA256; `fail_first_n` scripts CON.7 retries; holds **no reference** to the acquirer (I-9) |
| `tests/support.py :: make_card` | simulated card data | generator | Luhn-valid generated PANs — no real customer data |

The webhook signing secret (`simulated-webhook-secret`) is a simulated value
(name-map §4, ASSUMPTION), not a production credential; no secret is read from
source into any real system.

## Collapse (documented in `name-map.md` §2)

One process · in-memory stores · in-process bus. `PaymentGatewayRuntime`
stands for the I-9 locations (Application / Cache / Database / Queue / Worker
Tier); every I-4 container keeps its exact Lab 1 string and its module
boundaries inside the process. Sync = direct in-process call; async =
`publish()` → `drain()`. **Query Store** and **Expiry Job** are N/A — not
built, with reasons, on `name-map.md` §3 and `spec-trace.md` §3–§4.

## Demo script (order per capstone)

`python3 -m payment_gateway.demo` prints, in order:

1. **I-1 goal** — exact Lab 1 strings (goal + measurable outcome)
2. **One I-11 sequence on screen** — Authorize Payment, Lab 10 §1 participant names
3. **Live happy path** — authorize → 201, persisted state, async webhook with valid HMAC
4. **Live named `alt` / CON.\*** — fraud block (FRAUD-02) → Declined with zero acquirer calls (G5)
5. **Test report** — the full unittest suite result

## SA acceptance (Human A accepts)

The runtime traces to Labs 1–10 + `openapi.json` + the G6 rows on
`spec-trace.md`; the drift test (`OpenApiContractTests`) pins the document to
the running API in both directions.

| Role | Person | Sign-off |
|---|---|---|
| Dev (R) | Kim Đức Minh | ☑ built; all tests green 2026-08-22 |
| SA (A) | Nguyễn Quang Huy | ☑ accepted the runtime against the after pack — 2026-08-22 |
| Test (C) | Trần Quốc Đạt | ☑ test report reviewed (39/39 OK) — 2026-08-22 |
