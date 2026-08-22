# Agent contract — Payment Gateway capstone runtime

Machine-readable contract a coding agent must obey when it touches `capstone-runtime/`. The spec is Labs 1–10 + `openapi.json` + `name-map.md` + `spec-trace.md` + extension S1–S11. A chat that said "add 3DS" is not a requirement.

If the agent and Lab 1 disagree, the agent is wrong. If Lab 1 is wrong, SA updates the after pack first, then the agent traces again.

---

## Identity (Lab 1 — copy)

| Lab 1 field | String the agent must use |
|-------------|---------------------------|
| System-in-focus | Payment Gateway |
| Product | Payment Gateway API v1 |
| I-6 object | Payment |
| I-6 states (Title Case on the wire) | Pending, Authorized, Captured, Voided, Refunded, Declined, Failed |
| I-11 | Authorize Payment, Capture Payment, Refund Payment |
| Extension in-scope | Void Payment, Payment Query, Expiry Job, CON.6 timeout |
| I-11 container (internals only here) | Payment Orchestrator |
| I-3 (mocked) | Merchant Platform, AcquirerHost, NAPAS Switch, Issuing Bank |
| I-4 | API Gateway, Payment Orchestrator, Idempotency Store, Payment Store, Query Store, Message Queue, Webhook Service, Expiry Job |
| Expiry Job I-9 | **Scheduler** (not Worker Tier) |
| Worker Tier | Webhook Service only |

---

## MUST

| # | The agent MUST | Source |
|---|----------------|--------|
| M1 | Edit only `capstone-runtime/` (tests, OpenAPI, name map, spec-trace, README, `AGENTS.md`) | capstone.md location |
| M2 | Use Lab 1 strings; one spelling; status **Title Case** on the wire and in OpenAPI | I-6; Capstone+ C1 |
| M3 | Keep GET `/v1/payments/{id}` on Query Store; never call AcquirerHost / NAPAS Switch on query | I-5; S4 |
| M4 | Keep fraud on authorize only; never evaluate fraud on capture / void / refund | I-5; CON.3; S5 |
| M5 | Keep Query Store read-only; Webhook Service must not write Payment | I-7; I-9; S6; S8 |
| M6 | Keep CON.6 same transaction reference; no second charge | CON.6; S11 |
| M7 | Keep `WEBHOOK_SECRET` required; no getenv default | S1 |
| M8 | Keep `card_ref` = last 4 only; no full PAN in store, Query JSON, webhook, or OpenAPI | S3 |
| M9 | Keep rate-limit ASSUMPTION `100` / merchant / `60`s → 429 | I-4; S9 |
| M10 | Add a spec-trace row before any new route, status, or test id | AI spec driven |
| M11 | Stop and ask SA if Lab 1 and the after pack disagree | Human A accepts |
| M12 | Keep Expiry Job collapse I-9 = **Scheduler** in name map **and** README | I-9; Capstone+ leftover |

---

## MUST NOT

| # | The agent MUST NOT | Source |
|---|--------------------|--------|
| N1 | Add Tokenization, 3D Secure, Card Issuing, Recurring Billing, Dispute/Chargeback, FX, POS, KYC/AML, Settlement | I-1 out of scope |
| N2 | Add Keycloak, mTLS product, WAF, OAuth, API-key vault, or an LLM / chatbot / RAG as an I-4 or route | I-4; do not invent |
| N3 | Add an I-6 state, I-11 use case, actor, or I-3 | Do not invent |
| N4 | Put implementation, OpenAPI, or tests inside `Lb/` or `Lb/before/` | Before pack is archive |
| N5 | Restyle Labs 1–6 to match the code | Before pack is archive |
| N6 | Call a real host or embed a production secret | Simulated names |
| N7 | Invent a CON id or a second rate-limit number | ASSUMPTION one string |
| N8 | Serve GET by calling Payment Orchestrator → AcquirerHost | I-5 |
| N9 | Let Query Store or Webhook Service write Payment | I-7 / I-9 |
| N10 | Accept a generated diff that has no spec-trace row | AI spec driven |

---

## Enforcement

If SA believes a new use case is required, stop. Add **one** Lab 1 I-11 row and one Lab 9 note **first**, then Dev traces. Until that exists, the agent refuses.

Attempt tests (`tests/test_agent_contract.py`) prove these rules are checkable. Fixtures under `tests/fixtures/agent/` are violation examples that must never be applied to the runtime.
