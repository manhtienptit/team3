# Lab 6 — Integration Ecosystem (Model, Do Not Build)

Current style. No Guide, no diagram header block, no C4/ArchiMate viewpoint claim — those start at Lab 7 / Lab 8 / Lab 9. Drawn by SA, reviewed by Sec/Ops.

Scope: integration patterns from Lab 1 I-8. Out of scope: internal component logic (that is Lab 3 / Lab 9 Component / Lab 10).

---

## 1. Ecosystem Overview

Boxes are I-4 containers and I-3 externals, drawn plainly (no C4/ArchiMate notation). Product names appear as **labels only** — nothing is installed.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Payment Gateway (System Boundary)                      │
│                                                                                 │
│  ┌──────────────────┐         ┌───────────────────────────────┐                 │
│  │   API Gateway    │  sync   │     Payment Orchestrator      │                 │
│  │  [label: Nginx   │────────▶│     (core logic, state        │                 │
│  │   or Kong]       │ HTTP/   │      machine, fraud           │                 │
│  │                  │ gRPC    │      module in-process)        │                 │
│  └────────┬─────────┘         └───────┬───────┬───────┬───────┘                 │
│           │                           │       │       │                         │
│           │                     sync  │  sync │       │ sync                    │
│           │                     Redis │  SQL  │       │ HTTP                    │
│           │                           │       │       │                         │
│           │                    ┌──────▼──┐  ┌─▼──────┐│                         │
│           │                    │Idempot- │  │Payment ││                         │
│           │                    │ency     │  │Store   ││                         │
│           │                    │Store    │  │(Write) ││                         │
│           │                    │[Redis   │  │[Post-  ││                         │
│           │                    │ 7.x]    │  │greSQL] ││                         │
│           │                    └─────────┘  └────────┘│                         │
│           │                                           │                         │
│           │ sync                              async   │ publish                  │
│           │ SQL (read)                        event   │                         │
│           │                                           ▼                         │
│    ┌──────▼─────────┐                   ┌─────────────────────┐                 │
│    │  Query Store   │                   │   Message Queue     │                 │
│    │  (Read)        │                   │   [label: Kafka     │                 │
│    │  [PostgreSQL   │                   │    or SQS]          │                 │
│    │   Replica]     │                   └──────────┬──────────┘                 │
│    └────────────────┘                              │ async                      │
│                                                    │ consume                    │
│                                              ┌─────▼──────────────┐             │
│                                              │  Webhook Service   │             │
│                                              │  (HMAC-SHA256,     │             │
│                                              │   retry delivery)  │             │
│                                              └─────────┬──────────┘             │
│                                                        │                        │
│    ┌────────────────┐                                  │                        │
│    │  Expiry Job    │ sync SQL                         │                        │
│    │  [cron hourly] │──────────▶ Payment Store         │                        │
│    └────────────────┘                                  │                        │
│                                                        │                        │
└────────────────────────────────────────────────────────┼────────────────────────┘
                                                         │
                          async HTTPS POST               │
                          (HMAC-SHA256, 10s timeout)      │
                          ┌──────────────────────────────┘
                          ▼
               ┌─────────────────────┐
               │  Merchant Platform  │
               │  (webhook receiver) │
               └─────────────────────┘


         sync HTTPS (30s timeout + 1 retry)
┌─────────────────────────────────┐
│  Payment Orchestrator           │─────────────────▶ ┌─────────────────────────┐
│                                 │                   │  AcquirerHost           │
└─────────────────────────────────┘                   │  (External)             │
                                                      └────────────┬────────────┘
                                                                   │ ISO 8583
                                                      ┌────────────▼────────────┐
                                                      │  NAPAS Switch           │
                                                      │  (External)             │
                                                      └────────────┬────────────┘
                                                                   │ ISO 8583
                                                      ┌────────────▼────────────┐
                                                      │  Issuing Bank           │
                                                      │  (External)             │
                                                      └─────────────────────────┘
```

---

## 2. Integration Patterns (from I-8)

| Pattern | Mechanism | Containers Involved | Protocol | Product Label |
|---------|-----------|---------------------|----------|---------------|
| **Sync** | Request-Response | API Gateway → Payment Orchestrator | Internal HTTP / gRPC | Nginx or Kong |
| **Sync** | Request-Response | Payment Orchestrator → AcquirerHost | HTTPS REST, 30s timeout, 1 retry after 5s | — |
| **Sync** | Key-Value lookup | Payment Orchestrator → Idempotency Store | Redis GET/SET/BLPOP | Redis 7.x |
| **Sync** | SQL query | Payment Orchestrator → Payment Store | PostgreSQL wire protocol | PostgreSQL 16 |
| **Sync** | SQL read | API Gateway → Query Store | PostgreSQL wire protocol (read replica) | PostgreSQL 16 |
| **Async** | Event publish | Payment Orchestrator → Message Queue | Producer API | Kafka or SQS |
| **Async** | Event consume | Message Queue → Webhook Service | Consumer API | Kafka or SQS |
| **Async** | Webhook delivery | Webhook Service → Merchant Platform | HTTPS POST, HMAC-SHA256, 10s timeout | — |
| **Sync** | Scheduled SQL | Expiry Job → Payment Store | PostgreSQL (batch update) | cron |

The fraud rule check is an in-process call inside `Payment Orchestrator` (Lab 1 I-4 note) — not a container-to-container edge, so it has no row here.

---

## 3. Edge Labels Summary

| From | To | Label | Sync/Async |
|------|----|-------|------------|
| Merchant Platform | API Gateway | HTTPS/TLS, POST/GET /v1/* | Sync |
| API Gateway | Payment Orchestrator | Internal HTTP/gRPC | Sync |
| API Gateway | Query Store | SQL (read), cursor pagination | Sync |
| Payment Orchestrator | Idempotency Store | Redis GET/SET/BLPOP (48h TTL, 5s wait) | Sync |
| Payment Orchestrator | AcquirerHost | HTTPS, 30s timeout + 1 retry | Sync |
| Payment Orchestrator | Payment Store | SQL (write) | Sync |
| Payment Orchestrator | Message Queue | Publish event (within 1s) | Async |
| Message Queue | Webhook Service | Consume event | Async |
| Webhook Service | Merchant Platform | HTTPS POST, HMAC-SHA256, 10s timeout | Async |
| Expiry Job | Payment Store | SQL batch (hourly, Authorized → Failed) | Sync |
| AcquirerHost | NAPAS Switch | ISO 8583 | Sync |
| NAPAS Switch | Issuing Bank | ISO 8583 | Sync |

---

## 4. Event Names (Message Queue)

| Event | Trigger | Publisher | Consumer |
|-------|---------|-----------|----------|
| payment.authorized | Issuer approves authorization | Payment Orchestrator | Webhook Service |
| payment.captured | Capture succeeds | Payment Orchestrator | Webhook Service |
| payment.voided | Void succeeds | Payment Orchestrator | Webhook Service |
| payment.refunded | Refund succeeds (full or partial) | Payment Orchestrator | Webhook Service |
| payment.declined | Fraud block or issuer decline | Payment Orchestrator | Webhook Service |
| payment.failed | Acquirer timeout or auth expired | Payment Orchestrator / Expiry Job | Webhook Service |

---

## 5. AuthN / Security Note

Authentication and rate limiting reside on the **API Gateway** container. There is **no separate IAM product** added as a new system — AuthN is a responsibility of the existing API Gateway container.

| Security concern | Handled by | Mechanism |
|------------------|------------|-----------|
| Merchant Platform authentication | API Gateway | API key / Bearer token in header |
| Rate limiting | API Gateway | Per-merchant throttle |
| TLS termination | API Gateway | TLS 1.2+ |
| Webhook integrity | Webhook Service | HMAC-SHA256 signature |
| Acquirer communication | Payment Orchestrator | HTTPS (mutual TLS if required by AcquirerHost) |

---

## 6. Negative Evidence

| Prohibited | Status |
|------------|--------|
| Docker installed or running | ✗ Not done |
| Kong / Nginx actually deployed | ✗ Not done |
| Kafka / SQS cluster stood up | ✗ Not done |
| Redis cluster provisioned | ✗ Not done |
| PostgreSQL instance running | ✗ Not done |
| Any source code or automated tests | ✗ Not done |
| IAM added as separate system (AuthN is on API Gateway) | ✗ Not done |
| Broker internals shown on Context diagram | ✗ Not done |

**All integration patterns are modeled, not built.**
