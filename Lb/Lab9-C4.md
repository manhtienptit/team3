# Lab 9 — C4 Context and Container

**R:** SA · **A:** Owner (Context) · EA (Container) · Dev **R** / SA **A** (optional Component)

---

## 1. C4 Context (Level 1)

```
Title:      Payment Gateway — C4 System Context
Viewpoint:  C4 Context (L1)
Layer(s):   Application
As-Is | To-Be | Transition:  To-Be
Owner:      Role SA  Name Nguyễn Quang Huy
RACI:       R SA  A Owner  C BA, Sec  I Dev, Test, Ops
Version:    v1.0  Date 2026-08-20  Status Approved
Legend:      [Person] = stick figure; [System] = box; [External] = dashed box; → relationship (what happens)
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: system-in-focus + actors + externals / out-of-scope: containers, databases, pods, event buses
```

### Diagram

```mermaid
C4Context
  title System Context — Payment Gateway

  Person(merchant, "Merchant", "Business owner of the merchant account; does not call the API directly")

  System(gateway, "Payment Gateway", "Processes authorization, capture, void, refund for domestic card transactions (VND only)")

  System_Ext(merchantPlatform, "Merchant Platform", "Merchant's backend system; calls the API and receives webhook notifications")
  System_Ext(acquirer, "AcquirerHost", "Routes transactions to card network; returns approve/decline")
  System_Ext(napas, "NAPAS Switch", "Domestic card network connecting acquirer to issuing bank")
  System_Ext(issuer, "Issuing Bank", "Customer's bank; approves or declines; holds/releases funds")

  Rel(merchant, merchantPlatform, "Owns and operates")
  Rel(merchantPlatform, gateway, "Submits payment requests; queries status")
  Rel(gateway, merchantPlatform, "Delivers webhook events")
  Rel(gateway, acquirer, "Sends authorization, capture, void, refund")
  Rel(acquirer, napas, "Routes card transactions")
  Rel(napas, issuer, "Forwards auth/capture/void/refund")
```

### Context Elements

| Element | Type | Name (= Lab 1 index) |
|---------|------|----------------------|
| Person | Actor | Merchant |
| System-in-focus | Internal | Payment Gateway |
| External System | External | Merchant Platform |
| External System | External | AcquirerHost |
| External System | External | NAPAS Switch |
| External System | External | Issuing Bank |

### Relationships (what happens, not protocol)

| From | To | Description |
|------|----|-------------|
| Merchant | Merchant Platform | Owns and operates |
| Merchant Platform | Payment Gateway | Submits payment requests (auth, capture, void, refund); queries payment status |
| Payment Gateway | Merchant Platform | Delivers webhook events on status change |
| Payment Gateway | AcquirerHost | Sends authorization, capture, void, refund requests |
| AcquirerHost | NAPAS Switch | Routes card transactions |
| NAPAS Switch | Issuing Bank | Forwards authorization/capture/void/refund |

### NOT on Context (forbidden)

- ✗ Containers (API Gateway, Orchestrator, Redis, PostgreSQL, Kafka)
- ✗ Databases
- ✗ Pods / deployment nodes
- ✗ Event buses / message queues
- ✗ Class names / protocol details (30s timeout, HMAC, etc.)
- ✗ Unnamed externals

**G3 Evidence (Context):** No unnamed externals; names = Lab 1 (I-1, I-2, I-3). ✓

---

## 2. C4 Container (Level 2)

```
Title:      Payment Gateway — C4 Container
Viewpoint:  C4 Container (L2)
Layer(s):   Application
As-Is | To-Be | Transition:  To-Be
Owner:      Role SA  Name Nguyễn Quang Huy
RACI:       R SA  A EA  C DA, Sec, Dev, Ops  I Test
Version:    v1.0  Date 2026-08-20  Status Approved
Legend:      [Container] = box; [External] = dashed; ─── sync; ═══ async; protocol labeled
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: I-4 containers + externals; sync/async labeled / out-of-scope: container internals
```

### Diagram

```mermaid
C4Container
  title Container View — Payment Gateway

  Person(merchant, "Merchant")

  Container_Boundary(gw, "Payment Gateway") {
    Container(api, "API Gateway", "Nginx/Kong", "TLS termination, rate limiting, routing, input validation")
    Container(orch, "Payment Orchestrator", "Java/Go", "Core payment logic, state machine, in-process fraud module, acquirer communication")
    Container(redis, "Idempotency Store", "Redis 7.x", "Idempotency entries (48h TTL), fraud velocity counters, 5s concurrent wait")
    Container(pgwrite, "Payment Store", "PostgreSQL 16 Primary", "Payment records, webhook events, status (write)")
    Container(pgread, "Query Store", "PostgreSQL 16 Replica", "Read-only payment queries, cursor pagination")
    Container(queue, "Message Queue", "Kafka/SQS", "Payment events for webhook delivery (at-least-once)")
    Container(webhook, "Webhook Service", "Async worker", "HMAC-SHA256 signing, retry delivery (7 attempts, 1m/5m/30m/2h/12h/24h)")
    Container(cron, "Expiry Job", "Scheduled hourly", "Transitions expired auths (7d) to Failed")
  }

  System_Ext(merchantPlatform, "Merchant Platform", "Calls the API; receives webhooks")
  System_Ext(acquirer, "AcquirerHost", "Card transaction processing")
  System_Ext(napas, "NAPAS Switch", "Domestic card network")
  System_Ext(issuer, "Issuing Bank", "Approve/decline")

  Rel(merchant, merchantPlatform, "Owns and operates")
  Rel(merchantPlatform, api, "POST/GET /v1/payments/*", "HTTPS/TLS [sync]")
  Rel(api, orch, "Forward validated requests", "HTTP/gRPC [sync]")
  Rel(api, pgread, "Query payments", "SQL [sync]")
  Rel(orch, redis, "Check/set idempotency; read fraud counters", "Redis protocol [sync]")
  Rel(orch, acquirer, "Auth/capture/void/refund", "HTTPS, 30s timeout + 1 retry [sync]")
  Rel(orch, pgwrite, "Persist payment state", "SQL [sync]")
  Rel(orch, queue, "Publish payment event", "Producer API [async]")
  Rel(queue, webhook, "Consume events", "Consumer API [async]")
  Rel(webhook, merchantPlatform, "Deliver webhook", "HTTPS POST, HMAC-SHA256, 10s timeout [async]")
  Rel(cron, pgwrite, "Find expired → update status", "SQL [sync]")
  Rel(cron, queue, "Publish payment.failed event", "Producer API [async]")
  Rel(acquirer, napas, "Route", "ISO 8583 [sync]")
  Rel(napas, issuer, "Forward", "ISO 8583 [sync]")
```

### Container Elements (= I-4 exactly)

| Container Name | Technology | Sync/Async role |
|----------------|------------|-----------------|
| API Gateway | Nginx / Kong | Sync entry point |
| Payment Orchestrator | Java / Go (incl. in-process fraud module) | Sync orchestrator |
| Idempotency Store | Redis 7.x | Sync data store |
| Payment Store | PostgreSQL 16 Primary | Sync write |
| Query Store | PostgreSQL 16 Replica | Sync read |
| Message Queue | Kafka / SQS | Async bridge |
| Webhook Service | Async worker | Async delivery |
| Expiry Job | Scheduled (hourly) | Sync batch |

### Relationship Labels (all have sync/async)

| # | From | To | Protocol | Sync/Async |
|---|------|----|----------|------------|
| 1 | Merchant Platform | API Gateway | HTTPS/TLS | Sync |
| 2 | API Gateway | Payment Orchestrator | HTTP/gRPC | Sync |
| 3 | API Gateway | Query Store | SQL | Sync |
| 4 | Payment Orchestrator | Idempotency Store | Redis GET/SET/BLPOP | Sync |
| 5 | Payment Orchestrator | AcquirerHost | HTTPS (30s + 1 retry) | Sync |
| 6 | Payment Orchestrator | Payment Store | SQL | Sync |
| 7 | Payment Orchestrator | Message Queue | Publish event | Async |
| 8 | Message Queue | Webhook Service | Consume event | Async |
| 9 | Webhook Service | Merchant Platform | HTTPS POST (HMAC, 10s) | Async |
| 10 | Expiry Job | Payment Store | SQL batch | Sync |
| 11 | Expiry Job | Message Queue | Publish event | Async |
| 12 | AcquirerHost | NAPAS Switch | ISO 8583 | Sync |
| 13 | NAPAS Switch | Issuing Bank | ISO 8583 | Sync |

### NOT on Container (forbidden)

- ✗ Exploding every container (no component details)
- ✗ Unnamed externals
- ✗ Mixed L1 + L2 + L3 on one canvas

**G3 Evidence (Container):** All relationships labeled sync/async; all names = Lab 1 index (I-2, I-3, I-4); no unnamed externals. ✓

---

## 3. C4 Component (Level 3) — Payment Orchestrator (Optional)

```
Title:      Payment Orchestrator — C4 Component
Viewpoint:  C4 Component (L3)
Layer(s):   Application (one container drill-down)
As-Is | To-Be | Transition:  To-Be
Owner:      Role Dev  Name Kim Đức Minh
RACI:       R Dev  A SA  C DA, Sec  I Test, Ops
Version:    v1.0  Date 2026-08-20  Status Approved
Legend:      [Component] = box inside container; [Neighbour] = grey box (black-box); → dependency
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: internals of Payment Orchestrator ONLY / out-of-scope: other containers (shown as black boxes)
```

### Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Payment Orchestrator (container drill-down)              │
│                                                                             │
│  ┌──────────────────────┐        ┌─────────────────────┐                    │
│  │ [API Gateway]        │───────▶│  Request Handler    │                    │
│  │  (neighbour — b.box) │        │  (API Controller)   │                    │
│  └──────────────────────┘        └──────────┬──────────┘                    │
│             │                                                               │
│  ┌──────────▼──────────┐                                                    │
│  │  Input Validator    │  validates amount (10K–500M), card (Luhn, expiry)  │
│  └──────────┬──────────┘                                                    │
│             │                                                               │
│  ┌──────────▼──────────┐         ┌──────────────────────┐                   │
│  │ Idempotency Manager │────────▶│ [Idempotency Store]  │ (neighbour)       │
│  │ (check/lock/cache)  │         │  Redis — black box   │                   │
│  └──────────┬──────────┘         └──────────────────────┘                   │
│             │                                                               │
│  ┌──────────▼──────────┐                                                    │
│  │   Fraud Gate        │  evaluates 5 rules in-process, < 50ms (CON.3)      │
│  │ (fraud module)      │                                                    │
│  └──────────┬──────────┘                                                    │
│             │                                                               │
│  ┌──────────▼──────────┐                                                    │
│  │ State Machine       │  enforces valid transitions; rejects invalid (409) │
│  │ Engine              │                                                    │
│  └──────────┬──────────┘                                                    │
│             │                                                               │
│  ┌──────────▼──────────┐         ┌──────────────────────┐                   │
│  │  Acquirer Client    │────────▶│ [AcquirerHost]       │ (external)        │
│  │ (30s timeout, retry)│         │  HTTPS — black box   │                   │
│  └──────────┬──────────┘         └──────────────────────┘                   │
│             │                                                               │
│  ┌──────────▼──────────┐         ┌──────────────────────┐                   │
│  │  Persistence        │────────▶│ [Payment Store]      │ (neighbour)       │
│  │  Manager            │         │  PostgreSQL — b.box  │                   │
│  └──────────┬──────────┘         └──────────────────────┘                   │
│             │                                                               │
│  ┌──────────▼──────────┐         ┌──────────────────────┐                   │
│  │  Event Publisher    │────────▶│ [Message Queue]      │ (neighbour)       │
│  │ (publish within 1s) │         │  Kafka/SQS — b.box   │                   │
│  └─────────────────────┘         └──────────────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Components (inside Payment Orchestrator)

| Component | Responsibility |
|-----------|---------------|
| Request Handler | Receives requests from API Gateway; routes to appropriate flow |
| Input Validator | Validates amount (CON.1), card data (Luhn, expiry) |
| Idempotency Manager | Check/lock/cache via Idempotency Store; 48h TTL, 5s wait (CON.2) |
| Fraud Gate | Evaluates 5 fraud rules in-process; auth path only (CON.3) |
| State Machine Engine | Enforces valid transitions; rejects invalid with 409 |
| Acquirer Client | HTTP communication with AcquirerHost; 30s timeout + 1 retry (CON.6) |
| Persistence Manager | Writes payment records to Payment Store |
| Event Publisher | Publishes events to Message Queue (within 1s of status change) |

### Neighbours (black boxes — not exploded)

| Neighbour | Type |
|-----------|------|
| API Gateway | I-4 Container |
| Idempotency Store | I-4 Container |
| AcquirerHost | I-3 External |
| Payment Store | I-4 Container |
| Message Queue | I-4 Container |

**NOT shown:** Components of other containers; these components on the Context diagram.
