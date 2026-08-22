# Lab 8 — ArchiMate Views (Named Set)

**R:** EA (Motivation/Strategy) · BA (Process) · SA (Application Cooperation) · Ops (Technology)  
**A:** Owner (Motivation, Process) · EA (Application Cooperation) · SA (Technology)

---

## View 1 — Motivation

```
Title:      Payment Gateway — Motivation
Viewpoint:  ArchiMate Motivation
Layer(s):   Strategy
As-Is | To-Be | Transition:  To-Be
Owner:      Role EA  Name Ninh Mạnh Tiến
RACI:       R EA  A Owner  C SA, BA, Sec  I Dev, Test, Ops
Version:    v1.0  Date 2026-08-20  Status Approved
Legend:      ──▶ realization; ──▷ influence; ──association
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: Goal, Outcome, Constraints (CON.1–CON.8) / out-of-scope: container internals
```

### Diagram (ArchiMate Motivation Viewpoint)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MOTIVATION                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         «Stakeholder»                                │    │
│  │                          Merchant                                    │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │ has                                       │
│                                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           «Driver»                                   │    │
│  │         Need for real-time online card payment acceptance            │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
│                                  │ motivates                                │
│                                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                            «Goal»                                    │    │
│  │   Enable merchants to accept online card payments (Visa/MC) via a   │    │
│  │   single API with fraud protection and reliable webhook notification │    │
│  └────────────┬──────────────────┬─────────────────────────────────────┘    │
│               │                  │                                           │
│               │ realized by      │ measured by                               │
│               ▼                  ▼                                           │
│  ┌────────────────────┐   ┌───────────────────────────────────────────┐    │
│  │    «Requirement»   │   │              «Outcome»                     │    │
│  │  Payment Gateway   │   │  • 500 TPS sustained authorization        │    │
│  │  API v1            │   │  • P95 < 2,000 ms                         │    │
│  │                    │   │  • 99.9% availability                     │    │
│  └────────────────────┘   │  • Zero duplicate charges (idempotency)   │    │
│                           └───────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         «Constraints»                                │    │
│  │                                                                     │    │
│  │  CON.1  Single currency VND only (10,000–500,000,000)               │    │
│  │  CON.2  Idempotency key required (max 64 chars, 48h TTL, 5s wait)  │    │
│  │  CON.3  Fraud gate on authorization path only (5 rules, < 50ms)    │    │
│  │  CON.4  Authorization expires after 7 calendar days                 │    │
│  │  CON.5  Max 10 partial refunds per payment within 180 days          │    │
│  │  CON.6  Acquirer timeout 30s + 1 retry after 5s                     │    │
│  │  CON.7  Webhook: 7 attempts, HMAC-SHA256, 30d event TTL            │    │
│  │  CON.8  Single acquirer AcquirerHost via NAPAS Switch (domestic Visa/MC) │  │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│               ──▷ constrains                                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         «Principle»                                   │    │
│  │                                                                     │    │
│  │  • Idempotency before any external call                             │    │
│  │  • Fraud evaluation only on authorization path                      │    │
│  │  • Webhook never blocks synchronous response                        │    │
│  │  • Query path never calls external systems                          │    │
│  │  • State machine enforced before acquirer call                      │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**G1 Evidence:** Goal, outcome (measurable), constraints CON.1–CON.8 listed. ✓

**Must NOT show:** Protocol, pods, JDBC, container internals. ✓ (none present)

---

## View 2 — Business Process

```
Title:      Payment Gateway — Authorization Business Process
Viewpoint:  ArchiMate Business Process
Layer(s):   Business
As-Is | To-Be | Transition:  To-Be
Owner:      Role BA  Name Ninh Mạnh Tiến
RACI:       R BA  A Owner  C SA, Sec  I Dev, Test
Version:    v1.0  Date 2026-08-20  Status Approved
Legend:      → flow; ◆ decision (CON.* labeled); ○ event
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: authorization happy path (I-5) with CON.* branches / out-of-scope: capture, void, refund detail
```

### Diagram (ArchiMate Business Process)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BUSINESS PROCESS: Payment Authorization                    │
│                                                                             │
│  «Business Actor»          «Business Process»                               │
│   Merchant                                                                  │
│      │                                                                      │
│      │ triggers                                                             │
│      ▼                                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                                                                    │     │
│  │  ○ Start                                                           │     │
│  │  │                                                                 │     │
│  │  ▼                                                                 │     │
│  │  [1. Submit Payment Request]                                       │     │
│  │  │                                                                 │     │
│  │  ▼                                                                 │     │
│  │  [2. Validate Input]                                               │     │
│  │  │                                                                 │     │
│  │  ◆─── amount < 10K or > 500M? [CON.1] ──▶ Reject (400) ──▶ ○ End │     │
│  │  │ no                                                              │     │
│  │  ▼                                                                 │     │
│  │  [3. Check Idempotency]                                            │     │
│  │  │                                                                 │     │
│  │  ◆─── duplicate key? [CON.2] ──▶ Return Cached ──▶ ○ End          │     │
│  │  │ no                                                              │     │
│  │  ◆─── concurrent same key? [CON.2] ──▶ Wait 5s                    │     │
│  │  │ no                              │                               │     │
│  │  │                                 ◆── timeout? ──▶ 409 ──▶ ○ End │     │
│  │  ▼                                                                 │     │
│  │  [4. Evaluate Fraud Rules]                                         │     │
│  │  │                                                                 │     │
│  │  ◆─── rule blocks? [CON.3] ──▶ Declined (fraud) ──▶ ○ End        │     │
│  │  │ pass                                                            │     │
│  │  ▼                                                                 │     │
│  │  [5. Route to Acquirer]                                            │     │
│  │  │                                                                 │     │
│  │  ◆─── timeout 30s? [CON.6] ──▶ Retry (1x after 5s)               │     │
│  │  │ response                    │                                   │     │
│  │  │                             ◆── still timeout? ──▶ Failed ──▶○ │     │
│  │  ▼                                                                 │     │
│  │  ◆─── issuer declines? ──▶ Declined (issuer) ──▶ ○ End           │     │
│  │  │ approves                                                        │     │
│  │  ▼                                                                 │     │
│  │  [6. Persist Payment (Authorized, +7d)] [CON.4]                    │     │
│  │  │                                                                 │     │
│  │  ▼                                                                 │     │
│  │  [7. Publish Event]                                                │     │
│  │  │                                                                 │     │
│  │  ▼                                                                 │     │
│  │  [8. Deliver Webhook] [CON.7]                                      │     │
│  │  │                                                                 │     │
│  │  ▼                                                                 │     │
│  │  ○ End (Authorized)                                                │     │
│  │                                                                    │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  «Business Object»: Payment                                                 │
│  (moves through the process, states: Pending → Authorized/Declined/Failed)  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**G2 Evidence:** Named states (Authorized, Declined, Failed) match I-6. Process matches I-5. CON.* on every decision branch. ✓

**Must NOT show:** C4 containers as process boxes; sync/async protocol labels. ✓ (none present)

---

## View 3 — Application Cooperation

```
Title:      Payment Gateway — Application Cooperation
Viewpoint:  ArchiMate Application Cooperation
Layer(s):   Application
As-Is | To-Be | Transition:  To-Be
Owner:      Role SA  Name Nguyễn Quang Huy
RACI:       R SA  A EA  C DA, Sec  I Dev, Test
Version:    v1.0  Date 2026-08-20  Status Approved
Legend:      ─── flow; names = I-4 containers (same strings as C4 Container)
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: internal containers cooperation / out-of-scope: UML messages, C4 notation
```

### Diagram (ArchiMate Application Cooperation)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      APPLICATION COOPERATION                                 │
│                                                                             │
│                        «Application Component»                               │
│                                                                             │
│   ┌───────────────┐       ┌───────────────────────────┐                    │
│   │  API Gateway  │──────▶│   Payment Orchestrator    │                    │
│   └───────┬───────┘       └───┬─────┬─────┬─────┬────┘                    │
│           │                   │     │     │     │                           │
│           │                   │     │     │     │                           │
│   ┌───────▼───────┐   ┌──────▼──┐  │  ┌──▼─────────┐                    │
│   │  Query Store  │   │Idempot- │  │  AcquirerHost│  (fraud module runs │
│   │  (Read)       │   │ency     │  │  (external)  │  in-process inside │
│   │               │   │Store    │  │              │  Payment           │
│   └───────────────┘   └─────────┘  │  └────────────┘  Orchestrator)    │
│                                     │                                       │
│                              ┌──────▼──────┐                                │
│                              │Payment Store│                                │
│                              │(Write)      │                                │
│                              └──────┬──────┘                                │
│                                     │                                       │
│                              ┌──────▼──────┐                                │
│                              │Message Queue│                                │
│                              └──────┬──────┘                                │
│                                     │                                       │
│                              ┌──────▼──────────┐                            │
│                              │Webhook Service  │                            │
│                              └──────┬──────────┘                            │
│                                     │                                       │
│                              ┌───────────────┐                              │
│                              │ Merchant      │                              │
│                              │ Platform      │                              │
│                              │ (external)    │                              │
│                              └───────────────┘                              │
│                                                                             │
│   ┌──────────────┐                                                          │
│   │  Expiry Job  │────────────▶ Payment Store                               │
│   └──────────────┘                                                          │
│                                                                             │
│  Name-identity check: all boxes = I-4 / I-2 / I-3 strings ✓                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Must NOT show:** UML messages, mixed C4 notation. ✓ (ArchiMate only)

---

## View 4 — Technology

```
Title:      Payment Gateway — Technology / Deployment
Viewpoint:  ArchiMate Technology
Layer(s):   Technology
As-Is | To-Be | Transition:  To-Be
Owner:      Role Ops  Name Nguyễn Quang Huy
RACI:       R Ops  A SA  C Sec  I Dev, Test
Version:    v1.0  Date 2026-08-20  Status Approved
Legend:      ─── deployed on; locations from I-9; no forbidden path
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: deployment locations (I-9) / out-of-scope: channel writing core DB (forbidden)
```

### Diagram (ArchiMate Technology Viewpoint)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TECHNOLOGY / DEPLOYMENT                              │
│                                                                             │
│  «Node» Load Balancer (L7)                                                  │
│  ┌─────────────────────────────────────────┐                                │
│  │  TLS termination, health checks         │                                │
│  │  [HA pair]                              │                                │
│  └─────────────────────┬───────────────────┘                                │
│                        │                                                    │
│  «Node» Application Tier (2+ nodes)                                         │
│  ┌─────────────────────▼───────────────────┐                                │
│  │  API Gateway                            │                                │
│  │  Payment Orchestrator (incl. fraud      │                                │
│  │  module, in-process)                    │                                │
│  │  [stateless, horizontal scaling]        │                                │
│  └──────┬──────────────┬──────────────┬────┘                                │
│         │              │              │                                      │
│  «Node» Cache Tier     │    «Node» Queue Tier                               │
│  ┌──────▼──────────┐   │    ┌─────────▼────────────┐                        │
│  │ Idempotency     │   │    │ Message Queue         │                        │
│  │ Store           │   │    │ [Kafka / SQS cluster] │                        │
│  │ [Redis 7.x,    │   │    └─────────┬─────────────┘                        │
│  │  3-node cluster]│   │              │                                      │
│  └─────────────────┘   │    «Node» Worker Tier (2+ nodes)                   │
│                         │    ┌─────────▼────────────┐                        │
│  «Node» Database Tier   │    │ Webhook Service      │                        │
│  ┌──────────────────────▼─┐  │ [async consumers]    │                        │
│  │ Payment Store          │  └──────────────────────┘                        │
│  │ [PostgreSQL 16 Primary]│                                                  │
│  │          │             │  «Node» Scheduler                                │
│  │          │ streaming   │  ┌──────────────────────┐                        │
│  │          ▼ replication │  │ Expiry Job           │                        │
│  │ Query Store            │  │ [hourly cron]        │                        │
│  │ [PostgreSQL 16 Replica]│  └──────────────────────┘                        │
│  └────────────────────────┘                                                  │
│                                                                             │
│  «Forbidden path»: Webhook Service ──✗──▶ Payment Store (direct write)      │
│  «Forbidden path»: Merchant Platform ──✗──▶ AcquirerHost (direct call)     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Locations match I-9.** ✓  
**Forbidden paths shown.** ✓  
**Must NOT show:** Channel writing core ledger DB directly. ✓ (forbidden path marked)
