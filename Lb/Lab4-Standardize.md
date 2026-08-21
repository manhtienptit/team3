# Lab 4 — Standardize Following Modeling-Driven Design

**R:** SA · **A:** EA

---

## 1. Overview

Lab 4 produces the **after pack** by restyling the same views from the before pack using the Guide adopted in Lab 7. The before pack is archived unchanged. This document contains:

1. After pack reference (restyled views)
2. Name-identity check
3. Language check
4. Defect list (before pack)
5. Comparison note

---

## 2. Before Pack (Archived — DO NOT EDIT)

The before pack consists of the original documents drawn before Lab 7 modeling adoption:

| Lab | Before artifact | Location (archived) |
|-----|-----------------|---------------------|
| Lab 1 | Scope (original format) | Before: embedded in payment-gateway-design.md §1–3 |
| Lab 2 | Requirements & Analysis | Before: payment-gateway-design.md §3, Analysis.md |
| Lab 5 | UML sequences | Before: payment-gateway-design.md §5.2–5.3 |
| Lab 6 | Integration | Before: payment-gateway-design.md §5.4, §5.5 |
| Lab 8 | Architecture views | Before: Architecture.md (C4 + deployment mixed) |
| Lab 9 | C4 diagrams | Before: Architecture.md §1–2 |
| Lab 10 | UML detail | Before: Design.md sequences |

**These files are preserved unchanged at their original locations in the workspace root.**

---

## 3. After Pack Reference

The after pack is the set of Lab 7 deliverables (restyled per Guide):

| Lab | After artifact | File |
|-----|----------------|------|
| Lab 1 | Scope (I-1 to I-11 complete) | Lab1-Scopes.md |
| Lab 2 | Requirements + G1–G6 gate register | Lab2-Requirements.md |
| Lab 5 | UML Sequence/Activity/State + G6 | Lab5-UML-LowLevel.md |
| Lab 6 | Integration ecosystem (modeled) | Lab6-Integration-Ecosystem.md |
| Lab 7 | Adoption record | Lab7-Adoption.md |
| Lab 8 | 4 ArchiMate views (Motivation, Process, App Coop, Technology) | Lab8-ArchiMate.md |
| Lab 9 | C4 Context + Container + Component | Lab9-C4.md |
| Lab 10 | UML sequences with component detail | Lab10-UML-Named-UseCases.md |

Each after-pack view carries the **diagram header** with Title, Viewpoint, Layer, RACI, Version, Legend, Scope.

---

## 4. Name-Identity Check

Every box/lifeline string in the after pack = Lab 1 Input index. No forks.

| Name (Lab 1 index) | Used in Lab 8 | Used in Lab 9 | Used in Lab 5/10 Lifeline | Consistent? |
|---------------------|:---:|:---:|:---:|:---:|
| Merchant | ✓ (Process) | ✓ (Context, Container) | ✓ (actor) | ✓ |
| API Gateway | ✓ (App Coop) | ✓ (Container) | ✓ (participant) | ✓ |
| Payment Orchestrator | ✓ (App Coop) | ✓ (Container, Component) | ✓ (participant box) | ✓ |
| Fraud Engine | ✓ (App Coop) | ✓ (Container) | ✓ (participant, auth only) | ✓ |
| Idempotency Store | ✓ (App Coop) | ✓ (Container) | ✓ (participant) | ✓ |
| Payment Store | ✓ (App Coop, Tech) | ✓ (Container) | ✓ (participant) | ✓ |
| Query Store | ✓ (App Coop, Tech) | ✓ (Container) | — (not in write sequences) | ✓ |
| Message Queue | ✓ (App Coop) | ✓ (Container) | ✓ (participant) | ✓ |
| Webhook Service | ✓ (App Coop) | ✓ (Container) | — (async, not in payment seq) | ✓ |
| Expiry Job | ✓ (App Coop, Tech) | ✓ (Container) | — (background, separate) | ✓ |
| Vietcombank Acquirer | ✓ (App Coop) | ✓ (Context, Container) | ✓ (participant) | ✓ |
| NAPAS Switch | — | ✓ (Context) | — | ✓ |
| Issuing Bank | — | ✓ (Context) | — | ✓ |

**Result:** No forked names. All strings match Lab 1 I-2/I-3/I-4. ✓

---

## 5. Language Check

One viewpoint per canvas. No mixed relationships.

| After View | Language | Viewpoint | Mixed? |
|------------|----------|-----------|--------|
| Lab 8 View 1 — Motivation | ArchiMate | Motivation | No ✓ |
| Lab 8 View 2 — Business Process | ArchiMate | Business Process | No ✓ |
| Lab 8 View 3 — Application Cooperation | ArchiMate | Application Cooperation | No ✓ |
| Lab 8 View 4 — Technology | ArchiMate | Technology | No ✓ |
| Lab 9 — C4 Context | C4 | Context (L1) | No ✓ |
| Lab 9 — C4 Container | C4 | Container (L2) | No ✓ |
| Lab 9 — C4 Component | C4 | Component (L3) | No ✓ |
| Lab 5/10 — Sequences | UML | Sequence | No ✓ |
| Lab 5 — Activity | UML | Activity | No ✓ |
| Lab 5 — State Machine | UML | State Machine | No ✓ |

**Result:** One language per diagram. No mixed notation. ✓

---

## 6. Defect List (Before Pack)

Failures found on the before pack (Architecture.md, payment-gateway-design.md, Design.md), each with the Guide rule it violates.

| # | Defect | Before file | Guide rule violated | Severity | Owner to fix |
|---|--------|-------------|---------------------|----------|-------------|
| D1 | C4 Context and Container mixed on same document (§1 + §2 Architecture.md) without clear separation | Architecture.md | "Do not mix L1+L2+L3 on one canvas" | High | SA |
| D2 | Missing diagram header (Title, Viewpoint, RACI, Legend) on all views | Architecture.md, Design.md | "Diagram header (every after view)" | High | SA |
| D3 | No RACI assignment on any artifact | All before files | "RACI per artifact" | High | SA |
| D4 | ArchiMate and C4 concepts mixed — Application Cooperation not separated from C4 Container | Architecture.md §2 | "One language per diagram" | Medium | SA |
| D5 | Deployment details (Redis cluster nodes, PostgreSQL replica) appear on Container view | Architecture.md §2, §8 | "No pods/deployment on Container" | Medium | Ops/SA |
| D6 | Sequence diagrams use generic names ("Orchestrator") not identical to Container names ("Payment Orchestrator") | payment-gateway-design.md §5.2 | "Name identity: lifeline = C4 Container name" | Medium | Dev |
| D7 | No explicit Motivation/Strategy view (goal, constraints not in ArchiMate notation) | All before files | "Motivation view required" | High | EA |
| D8 | Business Process not in ArchiMate — described as text-only numbered steps | payment-gateway-design.md §Domain | "Business Process view required" | Medium | BA |
| D9 | State machine not separated as standalone UML diagram — embedded in text | payment-gateway-design.md §3.4 | "One object per state machine; UML notation" | Low | Test |
| D10 | No Quality Gates G1–G6 applied (custom gate tables used instead) | Quality-Gates-Architecture.md, Quality-Gates-Design.md | "Do not invent a second gate set" | High | EA |
| D11 | Product names (Kong, Kafka, Redis, PostgreSQL) appear as container names, not labels | Architecture.md §2 | "Product names as labels only" | Low | SA |
| D12 | Missing Legend on all diagrams | All before files | "Missing legend = automatic fail" | High | SA |
| D13 | Internals (Fraud Engine as in-process module) shown on Context level | Architecture.md §1 (implicit) | "No internals on Context" | Medium | SA |
| D14 | No sync/async labels on relationships in text-based diagrams | payment-gateway-design.md §5.1 | "G3: sync/async labeled" | Medium | SA |
| D15 | Multiple objects implied on state discussion (Payment + WebhookEvent lifecycle) without separation | Quality-Gates-Design.md D4, D12 | "One object per state machine" | Low | Test |

---

## 7. Comparison Note — What Modeling Changed

### 7.1 Summary of Changes

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Names** | Inconsistent (e.g., "Orchestrator" vs "Payment Orchestrator", "Redis" vs "Idempotency Store") | Single name-identity index (Lab 1 I-4); all views use same strings | Traceability; no ambiguity |
| **Languages** | Mixed C4 + ArchiMate + informal text on same pages | One language per view; cross-referenced via mapping table | Clarity; reviewable; fail-safe |
| **Diagram headers** | None | Every view has Title, Viewpoint, Layer, RACI, Legend, Scope | Governance; clear ownership |
| **RACI** | Absent | Per-artifact assignment (R draws, A approves, C consulted, I informed) | Accountability; no orphan artifacts |
| **Quality gates** | Custom gate tables (DG-01→38, AG-01→28) — reinvented | G1–G6 from Guide adopted as-is; product wording adjusted | Consistent process; no competing gates |
| **Hierarchy** | Flat — all levels in one document | Three-level stack (Enterprise → Solution → Delivery) with explicit language per level | Audience-appropriate views |
| **Context diagram** | Containers visible on context level | Clean L1: only Person + System-in-focus + Externals | No premature detail for Owner/BA |
| **Container diagram** | Mixed with deployment (node counts, technology versions prominent) | Pure L2: containers + sync/async relationships; tech as labels | Focus on architecture, not infra |
| **Sequences** | Generic participant names; no alt fragments documented for all exception paths | Participants = C4 Container names; all named alts with CON.* guards | Testable; G6 coverage |
| **State machine** | Inline text table | Standalone UML State diagram; one object (Payment); transitions with guards | Single source of truth for states |
| **ArchiMate** | Absent | 4 dedicated views (Motivation, Process, App Cooperation, Technology) | EA/Owner/BA get appropriate abstraction |
| **Integration** | Described in tables, not visualized with sync/async | Ecosystem diagram with labels; pattern table; negative evidence | Modeled, not just described |
| **Scope** | Spread across multiple documents | Consolidated in Lab 1 I-1→I-11; every downstream view references same index | Single source; no drift |

### 7.2 Key Structural Changes

1. **Before:** One Architecture.md contained Context + Container + Deployment + NFR + Traceability. No language discipline.  
   **After:** Separate views per language and level (Lab 8 ArchiMate, Lab 9 C4, Lab 5/10 UML). Each view one language only.

2. **Before:** Quality gates were a custom 38-row (Design) + 28-row (Architecture) checklist with different structure.  
   **After:** G1–G6 from Guide. Simple, consistent, blocks clearly defined.

3. **Before:** No explicit enterprise (ArchiMate) layer. Business motivation implied but not drawn.  
   **After:** Motivation view with Goal, Outcome, Constraints, Principles. Owner can sign G1 without reading container details.

4. **Before:** RACI not assigned. Unclear who draws, who approves.  
   **After:** Every artifact has R (draws) and A (approves) per the Guide RACI table.

5. **Before:** Name inconsistencies (Redis Cluster / Idempotency Store; PostgreSQL 16 Primary / Payment Store).  
   **After:** Technology names become labels; business-meaningful names are the identifiers.

### 7.3 What Did NOT Change

- Domain scope (in/out) remains the same
- Core business rules (CON.1–CON.8) are identical values
- Payment states (7) and transitions are unchanged
- Container decomposition is architecturally equivalent (same 9 containers)
- External systems remain the same 3
- Named use cases are the same 3

**The architecture was not redesigned. It was re-expressed in a disciplined, reviewable, traceable format.**
