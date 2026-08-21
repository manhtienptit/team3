# Online Payment Processing Modeling Pack

Status: Draft for review  
Source of truth: [Domain.md](Domain.md), [Requirements.md](Requirements.md), [Analysis.md](Analysis.md)  
Guide: [lab7/list.md](../lab7/list.md), adopted as written

## Lab 1 - Scope and identity index

### I-1 Team and topic

| Field | Value |
|---|---|
| Group | Team 3 |
| Topic / initiative name | Online Payment Processing |
| System-in-focus | Online Payment Gateway |
| Goal | Give merchants one reliable API for authorization, capture, void, refund, status, and webhook notification. |
| Outcome (measurable) | Every in-scope write operation has an enforced lifecycle state and idempotency result, and every status change produces a queryable webhook event. |
| Product | Online Payment Processing Gateway |
| Contract | Payment API and Webhook Contract |
| Baseline -> target | Baseline: fragmented payment operations and unclear status ownership -> Target: one gateway-owned lifecycle, idempotent writes, local queries, and asynchronous signed notifications. |
| In scope | Payment Authorization; Payment Capture; Void & Refund; Transaction Status Lifecycle; Webhook Notification; payment detail and list queries. |
| Out of scope | Card Issuing; Recurring Billing / Subscriptions; Dispute & Chargeback Management; 3D Secure Authentication; Multi-currency / FX; Physical POS / In-store Payments; KYC / AML. |

### I-2 Actors

| Name | ArchiMate | C4 | Role in process |
|---|---|---|---|
| Merchant | Business Actor | Person | Initiates payment operations and receives webhooks. |
| Customer | Business Actor | Person | Cardholder / payer. |
| Acquirer contact | Business Role | — | External payment processor contacted by the gateway. |
| Merchant webhook consumer | Business Role | — | Merchant-side responsibility for receiving webhook events. |

### I-3 External systems

| Name | Responsibility |
|---|---|
| Acquirer | Receives authorization, capture, void, and refund instructions. |
| Card Network | Routes instructions and responses. |
| Issuing Bank | Decides authorization and handles the customer funds hold or credit. |

The external-system list is deliberately limited to systems outside Online Payment Gateway. Fraud Engine and Webhook Service are internal supporting services and are defined only in I-4.

### I-4 Internal containers

| Name | Responsibility |
|---|---|
| Payment API | Validates merchant requests, exposes payment commands and queries, and returns synchronous responses. |
| Payment Orchestrator | Enforces idempotency and state transitions and coordinates authorization, capture, void, and refund. |
| Payment Store | Source of truth for Payment and PaymentMethod write state. |
| Query Store | Gateway-owned read model for payment detail and paginated queries. |
| Fraud Engine | Evaluates rule-based authorization pass/fail after validation. |
| Acquirer Connector | Sends idempotent synchronous commands to Acquirer and handles response correlation. |
| Webhook Event Queue | Asynchronous buffer for status-change events. |
| Webhook Service | Signs, delivers, retries, and records webhook outcomes. |

These names are the internal application/container identity set for the before pack. The before pack permits the current drawing style, but downstream diagrams must use these exact strings once a container view is drawn.

### I-5 Business process

Business object: Payment

1. Merchant submits an idempotent payment operation.
2. Payment API validates the request and Payment Orchestrator checks the idempotency key and current state.
3. For authorization, Fraud Engine evaluates the request after validation and before routing.
4. Payment Orchestrator sends the authorized operation to Acquirer Connector, which calls Acquirer.
5. Payment Store records the outcome and Query Store projects the current payment view.
6. Payment Orchestrator publishes a status-change event to Webhook Event Queue.
7. Webhook Service delivers the signed event to Merchant asynchronously.

Capture, void, and refund are separate operations. Capture requires `Authorized`; void requires `Authorized`; refund requires `Captured`. Queries use Query Store and do not call external payment systems.

**Principle / hard rules**

- The same idempotency key never creates a second operation or external charge.
- Fraud Engine runs only after validation and only on authorization paths.
- Invalid state or amount transitions are rejected explicitly.
- Webhook delivery never blocks the synchronous payment response.
- Payment queries never call Acquirer, Card Network, or Issuing Bank.

### I-6 Named object states

**Object:** Payment

| State | Meaning |
|---|---|
| Pending | Request received and processing is in flight. |
| Authorized | Issuer approved and funds are held. |
| Captured | Funds captured; settlement is queued. |
| Voided | Authorization cancelled and hold released. |
| Refunded | Full refund processed. |
| Declined | Issuer or fraud rules rejected the operation. |
| Failed | System or network error with no successful outcome. |

Transitions: `Pending -> Authorized`, `Pending -> Declined`, `Pending -> Failed`, `Authorized -> Captured`, `Authorized -> Voided`, `Captured -> Captured` for partial refund, and `Captured -> Refunded` for full refund. Terminal states: `Voided`, `Refunded`, `Declined`, `Failed`. Partial refund does not add a state.

### I-7 Source of truth

| Data object | Meaning | Source of truth |
|---|---|---|
| Payment | Payment identity, amounts, status, authorization and refund totals | Payment Store |
| PaymentMethod | Masked card or wallet method details | Payment Store |
| WebhookEvent | Event payload, signature, attempts, and delivery status | Webhook Service |
| FraudRule | Rule configuration used by the authorization gate | Fraud Engine |

### I-8 Integration

| Pattern | Mechanism | Example |
|---|---|---|
| Sync | Request/response API | Payment API -> Payment Orchestrator -> Acquirer Connector for authorization, capture, void, and refund. |
| Async | Event publication and delivery queue | Payment Orchestrator -> Webhook Event Queue -> Webhook Service -> Merchant. |
| Legacy / adapter | Not used | No legacy adapter is in scope. |

### I-9 Deployment

| Location | What runs there |
|---|---|
| Gateway runtime | Payment API, Payment Orchestrator, Fraud Engine, Acquirer Connector, Webhook Service |
| Gateway data storage | Payment Store and Query Store |
| Gateway messaging | Webhook Event Queue |
| External payment landscape | Acquirer, Card Network, Issuing Bank |
| Merchant environment | Merchant and its webhook endpoint |

Forbidden path: Webhook Event Queue or Webhook Service must not write Payment Store directly; Merchant queries must not route to Acquirer or Card Network.

### I-10 Constraints

| ID | Constraint | Effect on process |
|---|---|---|
| CON.1 | Idempotency is required for every write operation. | Deduplicate before fraud or external calls and return the original result on retry. |
| CON.2 | Fraud is a pass/fail gate after validation and before acquirer routing. | Fraud block becomes `Declined`; no Acquirer call is made. |
| CON.3 | Status transitions are limited to the defined Payment lifecycle. | Capture, void, and refund reject invalid state or amount requests. |
| CON.4 | Webhook delivery is asynchronous and signed. | Publish after status change; delivery retries do not block the API response. |
| CON.5 | Queries are served by gateway-owned data. | Payment API reads Query Store without real-time external calls. |

### I-11 Named use cases

| Use case | Happy path | Exception (`alt`) |
|---|---|---|
| Authorize a payment | Validate -> idempotency -> fraud pass -> Acquirer approval -> `Authorized` -> event | Fraud block, issuer decline, or timeout after idempotent retry. |
| Direct charge | Validate -> idempotency -> fraud pass -> authorize -> immediate capture -> `Captured` | Auth failure skips capture; capture failure leaves `Authorized`. |
| Capture an authorized payment | Validate `Authorized` -> amount valid -> Acquirer capture -> `Captured` | Invalid state/amount or acquirer failure leaves `Authorized`. |
| Void an authorized payment | Validate `Authorized` -> Acquirer void -> `Voided` | Captured or other state is rejected. |
| Refund a captured payment | Validate `Captured` -> remaining amount valid -> Acquirer refund | Excess amount rejected; partial refund remains `Captured`. |
| Deliver a payment webhook | Status change -> queue -> signed delivery -> merchant 2xx | Delivery failure retries; exhausted delivery is `failed_delivery`. |
| Query payment details | Payment API -> Query Store -> payment object or page | Unknown payment ID returns a not-found error; no external call. |

Optional C4 Component container: `Payment Orchestrator`.

## Lab 7 status

N/A in the before pack. The Lab 7 Guide, G1-G6 adoption record, and standardized RACI belong to the `current` after pack.

## Lab 2 - Requirements and traceability

The requirements are maintained in [Requirements.md](Requirements.md), and their reasoning is maintained in [Analysis.md](Analysis.md). This before-pack Lab 2 uses the team's pre-Lab 7 language; it does not apply the Guide's G1-G6 register. US-01 through US-09 and NFR-01 through NFR-05 are in scope. The following trace ensures each Lab 1 goal and constraint is represented.

| Requirement | Process step | Constraint | Payment state / evidence |
|---|---|---|---|
| R-01 Authorize with fraud gate and idempotency | 1-4 | CON.1, CON.2 | `Pending -> Authorized`, `Declined`, or `Failed` |
| R-02 Direct charge captures after approval | 3-5 | CON.1, CON.3 | Internal `Authorized` then `Captured`; auth failure has no capture |
| R-03 Capture only an authorized payment | 4-5 | CON.1, CON.3 | `Authorized -> Captured` |
| R-04 Void only an authorized payment | 4-5 | CON.1, CON.3 | `Authorized -> Voided` |
| R-05 Refund only captured funds within remaining amount | 4-5 | CON.1, CON.3 | `Captured -> Captured` or `Refunded` |
| R-06 Enforce the defined lifecycle | 2-5 | CON.3 | Only seven named states |
| R-07 Make all writes idempotent | 1-2 | CON.1 | Cached original result; no second external command |
| R-08 Deliver signed events asynchronously with retry | 6-7 | CON.4 | WebhookEvent delivery states are separate from Payment |
| R-09 Serve payment queries locally | 5 | CON.5 | Query Store is the read source |

### Lab 2 analysis result

The as-is pain is fragmented payment operations and unclear status ownership. The to-be analysis identifies one gateway-owned Payment lifecycle, an authorization fraud gate, idempotent write handling, a local query source, and asynchronous webhook delivery. Exception paths are named in Analysis.md: fraud block, issuer decline, acquirer timeout, invalid transition, partial capture/refund, and failed webhook delivery.

The before pack records requirements and analysis only. Quality-gate adoption is intentionally deferred to the current after pack.

## Lab 4 - After-pack comparison

The before pack was not present in the repository at task start, so no original views were overwritten. The after pack is the normalized set of views listed below. A future before-pack archive must remain unchanged when supplied.

| Check | After-pack result |
|---|---|
| Language | One language per canvas: ArchiMate, C4, or UML. |
| Names | All application/container participants use the I-4 identity strings. |
| Context scope | People, system-in-focus, and externals only; no internals. |
| Async boundary | Webhook Event Queue separates payment response from delivery. |
| RACI and legend | Included in every PlantUML source and referenced in each view header. |
| Defects in unavailable before pack | Not assessed; archive required before comparison sign-off. |

## Architecture pack

See [Architecture.md](Architecture.md) for A1-A12 evidence, C4 context/container decisions, NFRs, open assumptions, and traceability.

## Design and test pack

See [Design-Test.md](Design-Test.md) for the domain design, named UML sequences, state/activity views, failure paths, BR evidence, and G6 planned coverage.

## Required source views

| View | Source |
|---|---|
| ArchiMate Motivation | `../puml/puml/payment-motivation.puml` |
| ArchiMate Strategy | `../puml/puml/payment-strategy.puml` |
| ArchiMate Business Process | `../puml/puml/payment-business-process.puml` |
| ArchiMate Application Cooperation | `../puml/puml/payment-application-cooperation.puml` |
| ArchiMate Technology | `../puml/puml/payment-technology.puml` |
| C4 Context | `../puml/puml/payment-context.puml` |
| C4 Container | `../puml/puml/payment-container.puml` |
| UML sequences | `../puml/puml/payment-sequences.puml` |
| UML state/activity | `../puml/puml/payment-state-activity.puml` |
