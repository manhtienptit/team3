# Architecture Pack - Online Payment Processing

Title: Online Payment Gateway Architecture  
Viewpoint: C4 Context and Container with ArchiMate references  
Layer(s): Business / Application / Technology  
As-Is | To-Be | Transition: To-Be prototype architecture  
Owner: Role SA  Name Team 3  
RACI: R Team 3 SA  A Owner  C DA, Sec, Ops  I BA, Dev, Test  
Version: v1  Date 2026-08-21  Status Draft  
Legend: solid arrows are synchronous request/response; dashed arrows are asynchronous event publication or delivery; external systems are outside the Online Payment Gateway boundary.  
RACI legend: R = draws; A = approves; C = consulted; I = informed  
Scope: online authorization, capture, void, refund, lifecycle, webhooks, and payment queries; excludes card issuing, recurring billing, disputes, 3DS, multi-currency, POS, and KYC/AML.

## A1-A2 System views

PlantUML sources:

- C4 L1: `../puml/puml/payment-context.puml`
- C4 L2: `../puml/puml/payment-container.puml`
- ArchiMate application cooperation: `../puml/puml/payment-application-cooperation.puml`

### Context decision

`Online Payment Gateway` is the system-in-focus. `Merchant` and `Customer` are people. `Acquirer`, `Card Network`, and `Issuing Bank` are external systems. The context view contains no containers, databases, queues, protocols, or component internals.

### Container decision

| Container | Type | Main responsibility |
|---|---|---|
| Payment API | Application interface / runnable container | Commands and queries; request validation. |
| Payment Orchestrator | Runnable container | Idempotency, lifecycle, command coordination. |
| Payment Store | Runnable data container | Payment and PaymentMethod write source of truth. |
| Query Store | Runnable data container | Gateway-owned query projection. |
| Fraud Engine | Runnable service container | Authorization-only pass/fail rules. |
| Acquirer Connector | Runnable adapter container | Sync authorization, capture, void, refund calls. |
| Webhook Event Queue | Runnable messaging container | Async status-change buffer. |
| Webhook Service | Runnable delivery container | HMAC signing, delivery, retry, delivery records. |

The optional C4 L3 drill-down is intentionally omitted from this architecture pack; `Payment Orchestrator` is reserved for the design drill-down if needed.

## A3 Fraud gate position

Authorization path: `Payment API` validates -> `Payment Orchestrator` checks idempotency -> `Fraud Engine` evaluates -> `Acquirer Connector` routes to `Acquirer`.

A fraud block records `Declined` and publishes an event without calling `Acquirer`. Fraud Engine does not appear on capture, void, or refund paths.

## A4-A5 Payment operation paths

| Operation | Synchronous path | Preconditions / result |
|---|---|---|
| Authorization | Payment API -> Payment Orchestrator -> Fraud Engine -> Acquirer Connector -> Acquirer | New key; `Pending` to `Authorized`, `Declined`, or `Failed`. |
| Direct charge | Same authorization path, then Payment Orchestrator -> Acquirer Connector for immediate capture | One merchant call; `Authorized` is internal and not exposed as the merchant result. Capture failure leaves `Authorized`. |
| Capture | Payment API -> Payment Orchestrator -> Acquirer Connector -> Acquirer | Current state `Authorized`; amount <= authorized amount; success `Captured`. |
| Void | Payment API -> Payment Orchestrator -> Acquirer Connector -> Acquirer | Current state `Authorized`; success `Voided`. |
| Refund | Payment API -> Payment Orchestrator -> Acquirer Connector -> Acquirer | Current state `Captured`; amount <= remaining refundable amount; partial stays `Captured`, full becomes `Refunded`. |
| Query | Payment API -> Query Store | No Acquirer, Card Network, or Issuing Bank call. |

## A6-A8 Cross-cutting architecture

- Every write carries an idempotency key. The original result is stored before a retry can issue another external command.
- Unknown acquirer outcomes reuse the same external reference for status polling or retry; they never create a new transaction.
- Payment Store enforces the allowed Payment state machine. Invalid states and amounts are rejected at the API boundary.
- On every Payment status change, Payment Orchestrator publishes to Webhook Event Queue. Webhook Service consumes asynchronously, signs with HMAC, delivers to Merchant, retries on failure, and records `failed_delivery` after exhaustion. No retry schedule or maximum is invented here.
- Payment queries read Query Store, which is projected from gateway-owned data.

## A9 Non-functional requirements

Only the required NFRs apply:

| ID | Statement |
|---|---|
| NFR-01 | Same idempotency key must not produce duplicate acquirer calls, double-charges, or double-refunds. |
| NFR-02 | Webhook delivery must not block the synchronous payment response path. |
| NFR-03 | Payment queries must be answerable from the gateway's own store without calling acquirer or card network. |
| NFR-04 | Fraud rules execute after validation but before acquirer routing; only on authorization. |
| NFR-05 | Payment status transitions are enforced; invalid transitions are rejected at API level. |

## A10 Open assumptions

These remain open and are not design decisions:

| ID | Open assumption |
|---|---|
| OA-01 | Acquirer timeout duration and retry count. |
| OA-02 | Authorization expiry window. |
| OA-03 | Fraud rule thresholds and rule lists. |
| OA-04 | Webhook retry intervals and maximum count. |
| OA-05 | Settlement timing and batch frequency. |
| OA-06 | Whether partial capture voids the remainder or lets it expire. |
| OA-07 | Supported card networks. |
| OA-08 | Merchant onboarding and API-key provisioning. |
| OA-09 | Merchant rate limits. |
| OA-10 | Single currency choice. |

## A11 Traceability

| Story | Container / path | Notes |
|---|---|---|
| US-01 Authorize | Payment API -> Payment Orchestrator -> Fraud Engine -> Acquirer Connector | Fraud gate precedes Acquirer. |
| US-02 Direct charge | Authorization path + immediate Acquirer Connector capture | One merchant call; capture failure preserves `Authorized`. |
| US-03 Capture | Payment API -> Payment Orchestrator -> Acquirer Connector | No Fraud Engine. |
| US-04 Void | Payment API -> Payment Orchestrator -> Acquirer Connector | Requires `Authorized`; no Fraud Engine. |
| US-05 Refund | Payment API -> Payment Orchestrator -> Acquirer Connector | Requires `Captured`; no Fraud Engine. |
| US-06 Status lifecycle | Payment Orchestrator -> Payment Store | State machine enforced. |
| US-07 Idempotency | Payment API -> Payment Orchestrator | Dedup before fraud/external calls. |
| US-08 Webhook | Payment Orchestrator -> Webhook Event Queue -> Webhook Service -> Merchant | Asynchronous and signed. |
| US-09 Query | Payment API -> Query Store | No external real-time dependency. |

## G3 checklist

| Check | Result |
|---|---|
| Context has only people, system-in-focus, and named external systems | Pass |
| Container names equal the Lab 1 identity index | Pass |
| Sync and async relationships are labeled | Pass |
| Fraud Engine is authorization-only | Pass |
| Query path has no external payment-system call | Pass |
| Gateway, queue, and delivery are modeled, not installed | Pass |
