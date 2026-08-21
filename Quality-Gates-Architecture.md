# Quality gates — Architecture

**Unused — Lab 7 G1–G6 only.** Team 3 adopted the Guide's G1–G6 gates in `Lb/Lab7-Adoption.md`; this AG-\* checklist is a competing gate list and is not applied. Kept for reference only.

---

Reviewer checklist for an **architecture** pack (C4 context / container / optional component, system boundary, integration). UML sequences, state machines, and class design are gated by [Quality-Gates-Design.md](Quality-Gates-Design.md). Architecture may **reference** those diagrams; it must not replace them.

**Source of truth.** [Domain.md](Domain.md), [Requirements.md](Requirements.md) (US-01…US-09, NFR-01…NFR-05), [Analysis.md](Analysis.md) (BR-01…BR-18, OA-01…OA-10).

**When applied.** Before accepting `Architecture.md` or any C4 / integration pack for this prototype.

**Pass rule.** The pack **fails** if any **Must** row is Fail, if any automatic-fail anti-pattern is present, or if an open assumption (OA-*) is treated as a decided product rule. **Should** rows do not block; they must still be marked Pass, Fail, or N/A with a comment.

Notation (C4-PlantUML, Mermaid C4, Structurizr, or other) is free. Content is not. Do not invent latency, availability, or acquirer SLA numbers.

---

## Sign-off

**Pack title:** _______________  
**Author:** _______________  
**Reviewer:** _______________  
**Date:** _______________

**Approval:** [ ] Approved  [ ] Changes requested

---

## Required contents

The architecture pack must contain all of the following. Missing a section is Fail for the matching Must row.

| # | Section / artifact | Must show |
|---|---|---|
| A1 | System context (C4 L1) | Person: Merchant. System-in-focus: Payment Gateway. Externals **only**: Acquirer, Card Network, Issuing Bank. No card issuing, recurring billing, dispute management, 3DS, POS |
| A2 | Container view (C4 L2) | API layer; Payment Orchestrator (command); Fraud Engine (auth path only); Payment Store (write); Query Store or read model (read); Webhook Service (async); Message Queue between payment path and webhook. Acquirer/Network/Issuer remain external |
| A3 | Fraud gate position | Fraud Engine is one container on the **authorization** path only, **after** validation, **before** acquirer routing. Not on capture/void/refund (BR-01, BR-18, NFR-04) |
| A4 | Two-phase flow visibility | Authorization and Capture are distinct operations with separate container interactions. Not one "process payment" box (US-01, US-03, Domain two-phase) |
| A5 | Post-auth operations | Void (on Authorized) and Refund (on Captured) shown as separate paths to Acquirer without Fraud Engine (BR-08, BR-09, BR-18) |
| A6 | Webhook async boundary | Message Queue / event bus between payment processing and Webhook Service. Webhook does NOT block payment response (NFR-02, BR-13) |
| A7 | Integration notes | Sync acquirer calls for auth/capture/void/refund; acquirer timeout + retry (idempotent); webhook async via queue |
| A8 | Cross-cutting | Idempotency key dedup before external calls; state machine enforcement; HMAC signature on webhooks (NFR-01, NFR-05, BR-15) |
| A9 | NFR section | **Only** NFR-01…NFR-05. No invented latency, availability, TPS, or acquirer SLA |
| A10 | Open assumptions | OA-01…OA-10 listed as open, or closed only with an explicit requirement change |
| A11 | Traceability | Table: containers / paths → US-01…US-09 |
| A12 | Optional component (C4 L3) | If present: drill-down of **one** container (prefer Payment Orchestrator). Must still obey A3–A6. Absence of L3 is not Fail |

---

## Automatic Fail (anti-patterns)

Any one of these is Fail for the whole pack, even if other rows pass.

- Card Issuing, Recurring Billing, Dispute/Chargeback, 3DS/ACS, POS/ATM, KYC/AML, SWIFT as participants or containers
- Fraud Engine on capture, void, or refund path
- One "Process Payment" container handling auth + capture + void + refund without distinct paths
- Webhook Service on the synchronous payment response path (blocking)
- Payment query calling Acquirer or Card Network in real time
- Invented numeric SLAs (latency P95, TPS, availability %) not in Requirements or Domain
- OA-01 (acquirer timeout), OA-03 (fraud thresholds), OA-04 (webhook intervals), or OA-09 (rate limits) closed with specific numbers without a requirement change
- `PendingApproval`, manual review queue, staff actor, or approval workflow
- Settlement timing or batch frequency presented as an architecture decision without requirement basis

---

## Review checklist

Mark Pass or Fail. Comment is required on Fail.

| ID | Check | Must/Should | Trace | Pass | Fail | Comment |
|---|---|---|---|---|---|---|
| AG-01 | Context: Merchant + system-in-focus (Payment Gateway) + externals Acquirer, Card Network, Issuing Bank only | Must | A1, Domain actors | | | |
| AG-02 | Context has no Card Issuing, Recurring Billing, Dispute, 3DS, POS, KYC/AML | Must | Domain out of scope | | | |
| AG-03 | Container names align with Analysis roles (Payment, FraudRule, WebhookEvent, Acquirer, Issuing Bank) | Must | Analysis §2 | | | |
| AG-04 | Fraud Engine is a container on the **auth path only**, after validation, before acquirer | Must | BR-01, BR-18, NFR-04, A3 | | | |
| AG-05 | Fraud Engine does NOT appear on capture, void, or refund container interactions | Must | BR-18, NFR-04 | | | |
| AG-06 | Authorization and Capture are visibly distinct operations/paths (not one box) | Must | A4, US-01, US-03, Domain two-phase | | | |
| AG-07 | Void path: Orchestrator → Acquirer; precondition status=Authorized; no Fraud Engine | Must | BR-08, BR-18, US-04 | | | |
| AG-08 | Refund path: Orchestrator → Acquirer; precondition status=Captured; no Fraud Engine | Must | BR-09, BR-18, US-05 | | | |
| AG-09 | Webhook Service receives events from a queue/topic, NOT called synchronously from payment path | Must | NFR-02, BR-13, A6 | | | |
| AG-10 | Message Queue / event bus shown as async boundary between payment processing and webhook | Must | A6, NFR-02 | | | |
| AG-11 | Payment query (GET) served from gateway's own store; no arrow to Acquirer or Card Network | Must | NFR-03, BR-16, US-09 | | | |
| AG-12 | Integration notes: acquirer calls are sync with timeout + idempotent retry | Must | A7, BR-06, US-07 | | | |
| AG-13 | Cross-cutting: idempotency key dedup before any external call | Must | NFR-01, BR-04, US-07, A8 | | | |
| AG-14 | Cross-cutting: state machine enforcement (invalid transitions rejected) | Must | NFR-05, BR-07, A8 | | | |
| AG-15 | NFR section contains **only** NFR-01…NFR-05; no invented latency/availability/TPS | Must | A9, Requirements NFR | | | |
| AG-16 | OA-01…OA-10 listed as open; acquirer timeout, fraud thresholds, webhook schedule not closed with numbers | Must | A10, OA-01, OA-03, OA-04 | | | |
| AG-17 | Traceability table maps containers/paths to US-01…US-09 | Must | A11 | | | |
| AG-18 | No automatic-fail anti-pattern from the list above | Must | Domain out of scope | | | |
| AG-19 | Architecture references the design pack for UML sequences/state (or states they are out of this pack) | Should | Quality-Gates-Design | | | |
| AG-20 | If C4 L3 is present, it drills one container and still shows fraud-on-auth-only + webhook-async | Should | A12 | | | |
| AG-21 | API layer, Orchestrator, stores are distinct containers (not one monolith box) | Should | A2 | | | |
| AG-22 | Direct charge shown as a variant of auth+capture, not a third payment type | Should | US-02, BR-12 | | | |
| AG-23 | Partial refund does not introduce a new status; `Captured` with tracked `refundedAmount` | Should | BR-10, US-05 | | | |
| AG-24 | HMAC signature on webhook mentioned in cross-cutting or integration notes | Should | BR-15, US-08 | | | |

---

## Traceability table (required in the architecture pack)

Copy into the architecture pack. Reviewer fails AG-19 if any story lacks a container or path.

| Story | Container(s) / path | Notes |
|---|---|---|
| US-01 Authorize | | API → Orchestrator → Fraud Engine → Acquirer |
| US-02 Direct charge | | Same as auth + immediate capture; single API call |
| US-03 Capture | | API → Orchestrator → Acquirer; no Fraud Engine |
| US-04 Void | | API → Orchestrator → Acquirer; precondition Authorized |
| US-05 Refund | | API → Orchestrator → Acquirer; precondition Captured |
| US-06 Status lifecycle | | Orchestrator enforces state machine on every write |
| US-07 Idempotency | | Cross-cutting: dedup at Orchestrator before external calls |
| US-08 Webhook | | Queue → Webhook Service → Merchant endpoint (async) |
| US-09 Query | | API → Query Store (read); no Acquirer/Network dependency |

---

## NFR allowed in this pack

Do not add rows beyond this table unless Requirements.md changes.

| ID | Allowed statement |
|---|---|
| NFR-01 | Same idempotency key must not produce duplicate acquirer calls or double-charges |
| NFR-02 | Webhook delivery must not block the synchronous payment response path |
| NFR-03 | Payment queries must be answerable from the gateway's own store without calling acquirer or card network |
| NFR-04 | Fraud rules execute after validation but before acquirer routing; only on authorization path |
| NFR-05 | Payment status transitions are enforced; invalid transitions rejected at API level |
