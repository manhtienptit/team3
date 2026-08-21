# Lab 4 — Standardize Labs 1–3 (Own Method)

**R:** SA · **A:** EA

---

## 1. Overview

Lab 4 is the first cleanup pass on Labs 1–3, using **our own method** — not the Guide (that is adopted in Lab 7) and no ArchiMate / C4 / UML notation (that starts at Lab 5/8/9/10). This document contains:

1. Before pack (frozen copies of Lab 1–3 as they stood at the start of this sitting)
2. Cleaned pack (Lab 1–3 as they now stand, forks resolved)
3. Name-identity check (Lab 2 and Lab 3 strings against the Lab 1 index)
4. Defect list (how Lab 1–3 were first written)
5. Comparison note (what got cleaned, what we still don't know how to standardize)

---

## 2. Before Pack (Archived — DO NOT EDIT)

Frozen at the start of this sitting, before the fixes in §3 below.

| Lab | Before artifact | Location (archived) |
|-----|-----------------|----------------------|
| Lab 1 | Scope (I-1 to I-11) | `Lb/before/Lab1-Scopes.md` |
| Lab 2 | Requirements and Analysis | `Lb/before/Lab2-Requirements.md` |
| Lab 3 | Design and Test Evidence | `Lb/before/Lab3-Design-Test.md` |

---

## 3. Cleaned Pack

Same three artifacts, live at `Lb/Lab1-Scopes.md`, `Lb/Lab2-Requirements.md`, `Lb/Lab3-Design-Test.md`. Leftover forks resolved this sitting:

| # | Fork | Fix |
|---|------|-----|
| 1 | Lab 3 used both `FRAUD-01→05` (rule range) and `FRAUD-XX` (placeholder) for the same concept | Standardized on `FRAUD-01→05`; the alt-fragment placeholder now reads `fraud_rule_id — one of FRAUD-01→05` |
| 2 | CON.8 (single acquirer, BIN=VN fraud block) had no requirement tracing to it in Lab 2 | REQ-08 and REQ-15 (fraud block requirements) now trace to `CON.3, CON.8` in both the Requirements List and the Trace Table |
| 3 | Lab 3's Authorize Payment sequence stopped at "publish event" — never showed `Webhook Service` delivering to `Merchant Platform`, even though that hop is Lab 1 I-5 steps 8–9 | Added steps 15–16: `Message Queue → Webhook Service` (consume, async) and `Webhook Service → Merchant Platform` (deliver, async) |

---

## 4. Name-Identity Check

Every string in Lab 2 and Lab 3 checked against the Lab 1 I-2 / I-3 / I-4 index. No forks found beyond the three fixed in §3.

| Lab 1 Index | Used in Lab 2 | Used in Lab 3 | Match? |
|-------------|:---:|:---:|:---:|
| Merchant (I-2) | ✓ (user-story prose only) | — | ✓ |
| Merchant Platform (I-3) | ✓ | ✓ | ✓ |
| AcquirerHost (I-3) | ✓ | ✓ | ✓ |
| NAPAS Switch (I-3) | — | ✓ | ✓ |
| Issuing Bank (I-3) | — | — | ✓ (not needed on this sitting's flow) |
| API Gateway (I-4) | — | ✓ | ✓ |
| Payment Orchestrator (I-4) | ✓ | ✓ | ✓ |
| Idempotency Store (I-4) | ✓ | ✓ | ✓ |
| Payment Store (I-4) | ✓ | ✓ | ✓ |
| Query Store (I-4) | ✓ | — | ✓ (not needed on this sitting's flow) |
| Message Queue (I-4) | ✓ | ✓ | ✓ |
| Webhook Service (I-4) | ✓ | ✓ (after §3 fix) | ✓ |
| Expiry Job (I-4) | ✓ | ✓ | ✓ |

**Fraud Gate vs Fraud Engine.** `Fraud Engine` is not in the I-4 index — Lab 1 fixed that already. Lab 2 refers to it at capability level ("Payment Orchestrator, in-process fraud module"); Lab 3 names the module `Fraud Gate` at component level. Same concept, two zoom levels, not a fork.

**I-8 edges.** Every producer/consumer pair Lab 3's contract register uses (§4 of Lab 3) is a Lab 1 I-8 row. No new edges introduced.

**Result:** No forked names between Lab 2, Lab 3, and the Lab 1 index.

---

## 5. Defect List — How Lab 1–3 Were First Written

Failures found on Lab 1–3 as originally drafted, before this and earlier sittings' fixes. Own-method defects, not Guide-rule violations.

| # | Defect | Owner to fix |
|---|--------|--------------|
| D1 | I-3 used a real bank identity (`VietinBank Acquirer`, later `Vietcombank Acquirer`) instead of a simulated name | SA |
| D2 | I-5 and I-11 used abbreviations not in the index (`API GW`, `Orchestrator`, `Redis idemp`, bare `Acquirer`, bare `NAPAS`) | SA |
| D3 | `Fraud Engine` was listed as its own I-4 container while also described as co-located inside `Payment Orchestrator` — carried into later labs as a standalone box | SA / Dev |
| D4 | I-2 Person `Merchant` was also used as the literal HTTP caller and webhook recipient, instead of a distinct I-3 external (`Merchant Platform`) | BA / SA |
| D5 | I-7 said Webhook Event's source of truth is `Payment Store`; I-9's forbidden path said Webhook Service must not write to `Payment Store` at all — contradiction | SA |
| D6 | I-1 Group used a placeholder (`Team Payment`) instead of the real team name and members | Owner |
| D7 | Lab 2 carried a G1–G6 gate register — gates are Lab 7 (Guide adoption), not Lab 2 | EA |
| D8 | Lab 3 was skipped as `Lab3-NA.md` ("drawing pack, no implementation") — Lab 3 is required design evidence, not an exemption | Dev / Test |
| D9 | Direct Charge stayed in-scope (I-1) but I-6 had no `Pending → Captured` transition for it | Test |
| D10 | `FRAUD-01→05` and `FRAUD-XX` used inconsistently for the same concept within Lab 3 | Dev |
| D11 | CON.8 had no requirement tracing to it in Lab 2 | BA |
| D12 | Lab 3's Authorize sequence never showed `Webhook Service` delivering to `Merchant Platform` | Dev |

---

## 6. Comparison Note

### 6.1 What we cleaned in Lab 1–3

| Aspect | Before | After |
|--------|--------|-------|
| External identity | Real bank name (D1) | Simulated `AcquirerHost` |
| Process/use-case names | Abbreviations forked from the index (D2) | Full I-3/I-4 strings throughout I-5, I-11 |
| Fraud module | Double-modeled as container + co-located module (D3) | One thing: in-process module of `Payment Orchestrator` |
| Technical caller | `Merchant` (Person) used as HTTP/webhook endpoint (D4) | `Merchant Platform` (I-3) carries every protocol-level relationship |
| Source-of-truth rule | Contradicted the forbidden-write rule (D5) | Webhook Service writes only its own `webhook_event` rows |
| Team identity | Placeholder (D6) | Real team and member names |
| Gates | G1–G6 register inside Lab 2 (D7) | Removed; gates stay in Lab 7 |
| Lab 3 | Skipped as N/A (D8) | Six design artifacts, current-style |
| State coverage | Direct Charge had no transition (D9) | `Pending → Captured` added to I-6 |
| Fraud ID notation | Two forms for one concept (D10) | One form, `FRAUD-01→05` |
| Requirement traceability | CON.8 untraced (D11) | Traced from REQ-08 and REQ-15 |
| Sequence completeness | Webhook delivery hop missing (D12) | Added to Lab 3's sequence |

### 6.2 What we still don't know how to standardize

This is expected at this sitting — Lab 7 teaches the standard next.

- No agreed notation or diagram-header format yet (ArchiMate vs C4 vs UML, RACI legend, versioning). Deferred to Lab 7's Guide adoption.
- No agreed rule for validating component-level names (e.g. `Fraud Gate`, `Request Handler`) against the I-2/I-3/I-4 index — only container-level names have a check so far.
- No agreed severity or threshold model behind "5 fraud rules" — the specific velocity/amount/geo thresholds are not written anywhere in Lab 1–3 and stay open.

---

**Labs 5–10 are not touched in this sitting.** They still carry Guide-style diagram headers from earlier work; that gets stripped when we reach Lab 5, after Lab 4 is accepted.
