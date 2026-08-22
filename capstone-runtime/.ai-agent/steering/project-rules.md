# Payment Gateway — Capstone Runtime Rules

This project is a capstone runtime for Team 3's Payment Gateway. All code MUST follow these rules.

## Naming (Lab 1 I-6 Title Case — one spelling)

Status values in ALL response bodies, OpenAPI enums, Query Store projections, and webhook events MUST use Lab 1 Title Case:
- `Pending`, `Authorized`, `Captured`, `Voided`, `Refunded`, `Declined`, `Failed`

Never use lowercase (`authorized`, `declined`) or UPPER_CASE in status fields. The enum `.name` property gives Title Case; `.value` gives lowercase — always use `.name` for public-facing responses.

## Architecture constraints

- **One process** — no extra deployable units without a collapse row in `name-map.md`
- **I-7 ownership** — only Persistence Manager and Expiry Job may write Payment records; only Webhook Service may write Webhook Event rows
- **I-5 hard rules** — idempotency BEFORE fraud BEFORE acquirer; fraud NEVER on capture/void/refund; webhook NEVER blocks sync response; query NEVER calls acquirer
- **I-9 forbidden paths** — Webhook Service cannot write Payment; Merchant Platform cannot call AcquirerHost; Query Store cannot write Payment
- **S1** — WEBHOOK_SECRET from environment only; no hardcoded default in source

## Key files

- #[[file:openapi.json]] — G4 public contract; drift test asserts bidirectional match
- #[[file:name-map.md]] — identity map, collapse documentation, ASSUMPTION rows
- #[[file:spec-trace.md]] — every route/test must appear here; nothing off-trace is allowed

## When modifying code

1. Status strings in response bodies = Title Case (Lab 1 I-6 names)
2. Any new route must appear in `openapi.json` AND `spec-trace.md`
3. Any new test must be added to `spec-trace.md` with its test id
4. Run `python3 -m unittest discover -s tests -t .` — all 78 tests must pass
5. Do not add Tokenization, 3DS, KYC, or any Lab 1 out-of-scope item
6. Do not modify files inside modeling packs (Lb/, Lb/before/, Lab 7)
