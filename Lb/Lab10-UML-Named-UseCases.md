# Lab 10 — UML Low-Level Design for Named C4 Use Cases

**R:** Dev (Kim Đức Minh) · **A:** SA (Nguyễn Quang Huy) · **C:** Test, BA

---

## 1. Sequence — Authorize Payment (with Component internals)

```
Title:      Authorize Payment — Sequence with Component Detail
Viewpoint:  UML Sequence
Layer(s):   Delivery
As-Is | To-Be | Transition:  To-Be
Owner:      Role Dev  Name Kim Đức Minh
RACI:       R Dev  A SA (Nguyễn Quang Huy)  C Test, BA  I Ops
Version:    v1.0  Date 2026-08-20  Status Approved
Legend:      → sync; --→ async; alt = exception; note = CON.*; component modules inside Payment Orchestrator only
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: Authorize Payment use case (I-11) / out-of-scope: capture, void, refund
```

### Participants

All participants ⊆ I-4 / I-2 / I-3 (Lab 9 Container names). Component modules shown only inside Payment Orchestrator (the one selected container).

```plantuml
@startuml
participant "Merchant Platform" as Merchant
participant "API Gateway" as APIGW
box "Payment Orchestrator" #LightBlue
  participant "Request Handler" as ReqHandler
  participant "Input Validator" as Validator
  participant "Idempotency Manager" as IdempMgr
  participant "Fraud Gate" as FraudGate
  participant "State Machine Engine" as StateMachine
  participant "Acquirer Client" as AcqClient
  participant "Persistence Manager" as PersistMgr
  participant "Event Publisher" as EventPub
end box
participant "Idempotency Store" as Redis
participant "AcquirerHost" as Acquirer
database "Payment Store" as PG
queue "Message Queue" as MQ
participant "Webhook Service" as Webhook

== Happy Path ==

Merchant -> APIGW : POST /v1/payments\n{amount:500000, card, idempotency_key, capture:false}

APIGW -> ReqHandler : forward (validated TLS, rate-limited)

ReqHandler -> Validator : validate(amount, card)
note right: [CON.1] 10,000 ≤ amount ≤ 500,000,000 VND\nLuhn check, card not expired
Validator --> ReqHandler : valid

ReqHandler -> IdempMgr : check(idempotency_key)
IdempMgr -> Redis : GET idempotency:{key}
Redis --> IdempMgr : miss
IdempMgr -> Redis : SET idempotency:{key}:lock 1 EX 35 NX
note right: [CON.2] 48h TTL, max 64 chars
Redis --> IdempMgr : OK (lock acquired)
IdempMgr --> ReqHandler : proceed (new request)

ReqHandler -> FraudGate : evaluate(card, amount, merchant_id)
note right: [CON.3] 5 rules, < 50ms, auth only, first-block-wins (in-process)\nvelocity / high-value / merchant velocity / BIN country / daily cumulative
FraudGate -> Redis : GET fraud counters (velocity, daily)
Redis --> FraudGate : counter values
FraudGate --> ReqHandler : pass

ReqHandler -> StateMachine : validateTransition(null → Pending)
StateMachine --> ReqHandler : valid

ReqHandler -> AcqClient : authorize(card_ref, amount)
note right: [CON.6] 30s timeout + 1 retry after 5s
AcqClient -> Acquirer : HTTPS authorize\n(transactionRef, amount, card)
Acquirer --> AcqClient : APPROVE {auth_code}
AcqClient --> ReqHandler : approved(auth_code)

ReqHandler -> PersistMgr : persist(Payment{status:Authorized, auth_code, expiresAt:now+7d})
note right: [CON.4] 7 calendar days
PersistMgr -> PG : INSERT Payment
PG --> PersistMgr : OK
PersistMgr --> ReqHandler : persisted

ReqHandler -> IdempMgr : cache(key, response)
IdempMgr -> Redis : SET idempotency:{key} {response} EX 172800
Redis --> IdempMgr : OK

ReqHandler -> EventPub : publish(payment.authorized)
EventPub -> MQ : produce event
note right: within 1s of status change
MQ --> EventPub : ack
EventPub --> ReqHandler : published

ReqHandler --> APIGW : 201 {id, status:"authorized", auth_code}
APIGW --> Merchant : 201 Authorized
MQ -> Webhook : consume payment.authorized (async)
Webhook -> Merchant : POST webhook, HMAC-SHA256 (async)

== alt: Direct Charge (capture:true) [immediate capture] ==

Acquirer --> AcqClient : APPROVE {auth_code}
AcqClient --> ReqHandler : approved(auth_code)
ReqHandler -> AcqClient : capture(payment_ref, amount)
AcqClient -> Acquirer : HTTPS capture
Acquirer --> AcqClient : CAPTURE_OK
AcqClient --> ReqHandler : captured
ReqHandler -> PersistMgr : persist(Payment{status:Captured, capturedAmount:amount})
PersistMgr -> PG : INSERT Payment
ReqHandler -> IdempMgr : cache(key, response)
ReqHandler -> EventPub : publish(payment.captured)
EventPub -> MQ : produce event
ReqHandler --> APIGW : 200 {id, status:"captured"}
APIGW --> Merchant : 200 Captured
note right: Merchant Platform sees Pending → Captured directly;\nintermediate Authorized is not exposed

== alt: Fraud Block [CON.3] ==

FraudGate --> ReqHandler : blocked(high-value)
ReqHandler -> PersistMgr : persist(Payment{status:Declined, fraud_rule:"high-value"})
PersistMgr -> PG : INSERT
ReqHandler -> IdempMgr : cache(key, declined_response)
ReqHandler -> EventPub : publish(payment.declined)
ReqHandler --> APIGW : 200 {status:"declined", decline_reason:"fraud_rule"}
APIGW --> Merchant : 200 Declined
note right: No acquirer call made

== alt: Issuer Decline ==

Acquirer --> AcqClient : DECLINE {reason_code}
AcqClient --> ReqHandler : declined(reason_code)
ReqHandler -> PersistMgr : persist(Payment{status:Declined, decline_reason:"issuer_decline"})
PersistMgr -> PG : INSERT
ReqHandler -> IdempMgr : cache(key, declined_response)
ReqHandler -> EventPub : publish(payment.declined)
ReqHandler --> APIGW : 200 {status:"declined", decline_reason:"issuer_decline"}
APIGW --> Merchant : 200 Declined

== alt: Acquirer Timeout [CON.6] ==

AcqClient -> Acquirer : HTTPS authorize (attempt 1)
note right: timeout after 30s
AcqClient -> AcqClient : wait 5s
AcqClient -> Acquirer : HTTPS authorize (retry, same reference)
note right: timeout after 30s (retry also fails)
AcqClient --> ReqHandler : timeout_exhausted
ReqHandler -> PersistMgr : persist(Payment{status:Failed})
ReqHandler -> IdempMgr : cache(key, failed_response)
ReqHandler -> EventPub : publish(payment.failed)
ReqHandler --> APIGW : 200 {status:"failed"}
APIGW --> Merchant : 200 Failed

== alt: Idempotency Duplicate [CON.2] ==

IdempMgr -> Redis : GET idempotency:{key}
Redis --> IdempMgr : hit (cached response exists)
IdempMgr --> ReqHandler : return_cached(response)
ReqHandler --> APIGW : cached HTTP status + body
APIGW --> Merchant : 200 (original response)
note right: No fraud, no acquirer, no persist

== alt: Concurrent Same Key [CON.2] ==

IdempMgr -> Redis : GET idempotency:{key}
Redis --> IdempMgr : lock detected (in-flight)
IdempMgr -> Redis : BLPOP idempotency:{key}:done 5
note right: wait up to 5s
Redis --> IdempMgr : timeout (5s elapsed)
IdempMgr --> ReqHandler : conflict
ReqHandler --> APIGW : 409 idempotency_conflict
APIGW --> Merchant : 409

@enduml
```

---

## 2. Sequence — Capture Payment (with Component internals)

```
Title:      Capture Payment — Sequence with Component Detail
Viewpoint:  UML Sequence
Layer(s):   Delivery
As-Is | To-Be | Transition:  To-Be
Owner:      Role Dev  Name Kim Đức Minh
RACI:       R Dev  A SA (Nguyễn Quang Huy)  C Test, BA  I Ops
Version:    v1.0  Date 2026-08-20  Status Approved
Legend:      → sync; alt = exception; component modules inside Payment Orchestrator only
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: Capture Payment use case (I-11) / out-of-scope: authorize, void, refund
```

### Participants

```plantuml
@startuml
participant "Merchant Platform" as Merchant
participant "API Gateway" as APIGW
box "Payment Orchestrator" #LightBlue
  participant "Request Handler" as ReqHandler
  participant "Idempotency Manager" as IdempMgr
  participant "State Machine Engine" as StateMachine
  participant "Acquirer Client" as AcqClient
  participant "Persistence Manager" as PersistMgr
  participant "Event Publisher" as EventPub
end box
participant "Idempotency Store" as Redis
participant "AcquirerHost" as Acquirer
database "Payment Store" as PG
queue "Message Queue" as MQ
participant "Webhook Service" as Webhook

note over ReqHandler: Fraud module [CON.3] — not on capture path

== Happy Path ==

Merchant -> APIGW : POST /v1/payments/{id}/capture\n{amount:500000, idempotency_key}

APIGW -> ReqHandler : forward

ReqHandler -> IdempMgr : check(idempotency_key)
IdempMgr -> Redis : GET idempotency:{key}
Redis --> IdempMgr : miss
IdempMgr -> Redis : SET lock
IdempMgr --> ReqHandler : proceed

ReqHandler -> PersistMgr : load(payment_id)
PersistMgr -> PG : SELECT Payment WHERE id = {id}
PG --> PersistMgr : Payment{status:Authorized, expiresAt, authorizedAmount}
PersistMgr --> ReqHandler : payment

ReqHandler -> StateMachine : validateTransition(Authorized → Captured)
note right: Check: status=Authorized, expiresAt>now, amount≤authorized
StateMachine --> ReqHandler : valid

ReqHandler -> AcqClient : capture(payment_ref, amount)
note right: [CON.6] 30s timeout + 1 retry
AcqClient -> Acquirer : HTTPS capture
Acquirer --> AcqClient : CAPTURE_OK
AcqClient --> ReqHandler : captured

ReqHandler -> PersistMgr : update(status=Captured, capturedAmount=amount)
PersistMgr -> PG : UPDATE Payment
PG --> PersistMgr : OK

ReqHandler -> IdempMgr : cache(key, response)
IdempMgr -> Redis : SET idempotency:{key} {response} EX 172800

ReqHandler -> EventPub : publish(payment.captured)
EventPub -> MQ : produce
MQ --> EventPub : ack

ReqHandler --> APIGW : 200 {status:"captured", capturedAmount}
APIGW --> Merchant : 200 Captured
MQ -> Webhook : consume payment.captured (async)
Webhook -> Merchant : POST webhook, HMAC-SHA256 (async)

== alt: Authorization Expired [CON.4] ==

StateMachine -> StateMachine : expiresAt ≤ now
StateMachine --> ReqHandler : invalid (authorization_expired)
ReqHandler --> APIGW : 409 authorization_expired
APIGW --> Merchant : 409

== alt: Amount Exceeds Authorized ==

StateMachine -> StateMachine : amount > authorizedAmount
StateMachine --> ReqHandler : invalid (amount_exceeds_authorized)
ReqHandler --> APIGW : 400 amount_exceeds_authorized
APIGW --> Merchant : 400

== alt: Invalid State (status ≠ Authorized) ==

StateMachine -> StateMachine : status ≠ Authorized
StateMachine --> ReqHandler : invalid (invalid_state_transition)
ReqHandler --> APIGW : 409 invalid_state_transition
APIGW --> Merchant : 409

== alt: Partial Capture (amount < authorized) ==

AcqClient --> ReqHandler : captured
ReqHandler -> PersistMgr : update(capturedAmount=partial)
ReqHandler -> AcqClient : void_remainder(authorized - partial)
AcqClient -> Acquirer : HTTPS void(remainder)
Acquirer --> AcqClient : VOID_OK
ReqHandler -> PersistMgr : update(remainderVoided=true)
ReqHandler -> EventPub : publish(payment.captured)
ReqHandler --> APIGW : 200 {capturedAmount:partial, remainderVoided:true}

@enduml
```

---

## 3. Sequence — Refund Payment (with Component internals)

```
Title:      Refund Payment — Sequence with Component Detail
Viewpoint:  UML Sequence
Layer(s):   Delivery
As-Is | To-Be | Transition:  To-Be
Owner:      Role Dev  Name Kim Đức Minh
RACI:       R Dev  A SA (Nguyễn Quang Huy)  C Test, BA  I Ops
Version:    v1.0  Date 2026-08-20  Status Approved
Legend:      → sync; alt = exception; component modules inside Payment Orchestrator only
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: Refund Payment use case (I-11) / out-of-scope: authorize, capture, void
```

### Participants

```plantuml
@startuml
participant "Merchant Platform" as Merchant
participant "API Gateway" as APIGW
box "Payment Orchestrator" #LightBlue
  participant "Request Handler" as ReqHandler
  participant "Idempotency Manager" as IdempMgr
  participant "State Machine Engine" as StateMachine
  participant "Acquirer Client" as AcqClient
  participant "Persistence Manager" as PersistMgr
  participant "Event Publisher" as EventPub
end box
participant "Idempotency Store" as Redis
participant "AcquirerHost" as Acquirer
database "Payment Store" as PG
queue "Message Queue" as MQ
participant "Webhook Service" as Webhook

note over ReqHandler: Fraud module [CON.3] — not on refund path

== Happy Path (Partial Refund) ==

Merchant -> APIGW : POST /v1/payments/{id}/refund\n{amount:100000, idempotency_key}

APIGW -> ReqHandler : forward

ReqHandler -> IdempMgr : check(idempotency_key)
IdempMgr -> Redis : GET idempotency:{key}
Redis --> IdempMgr : miss
IdempMgr -> Redis : SET lock
IdempMgr --> ReqHandler : proceed

ReqHandler -> PersistMgr : load(payment_id)
PersistMgr -> PG : SELECT Payment WHERE id = {id}
PG --> PersistMgr : Payment{status:Captured, capturedAmount:500000,\nrefundedAmount:0, refundCount:0, capturedAt}
PersistMgr --> ReqHandler : payment

ReqHandler -> StateMachine : validateRefund(payment, amount:100000)
note right
  [CON.5] Check ALL:
  • status = Captured
  • amount ≤ (capturedAmount - refundedAmount) = 500000
  • refundCount < 10
  • capturedAt + 180d > now
end note
StateMachine --> ReqHandler : valid

ReqHandler -> AcqClient : refund(payment_ref, amount:100000)
note right: [CON.6] 30s timeout + 1 retry
AcqClient -> Acquirer : HTTPS refund
Acquirer --> AcqClient : REFUND_OK
AcqClient --> ReqHandler : refunded

ReqHandler -> PersistMgr : update(refundedAmount+=100000, refundCount+=1)
PersistMgr -> PG : UPDATE Payment SET\nrefundedAmount=100000, refundCount=1
note right: refundedAmount(100000) < capturedAmount(500000)\n→ status stays Captured
PG --> PersistMgr : OK

ReqHandler -> IdempMgr : cache(key, response)
IdempMgr -> Redis : SET idempotency:{key} {response} EX 172800

ReqHandler -> EventPub : publish(payment.refunded)
EventPub -> MQ : produce
MQ --> EventPub : ack

ReqHandler --> APIGW : 200 {status:"captured", refundedAmount:100000, refundCount:1}
APIGW --> Merchant : 200
MQ -> Webhook : consume payment.refunded (async)
Webhook -> Merchant : POST webhook, HMAC-SHA256 (async)

== alt: Full Refund (refundedAmount = capturedAmount) ==

PersistMgr -> PG : UPDATE Payment SET\nrefundedAmount=500000, refundCount=5, status=Refunded
note right: refundedAmount = capturedAmount → Refunded (terminal)
ReqHandler -> EventPub : publish(payment.refunded)
ReqHandler --> APIGW : 200 {status:"refunded"}

== alt: Max Refunds Exceeded [CON.5] ==

StateMachine -> StateMachine : refundCount ≥ 10
StateMachine --> ReqHandler : invalid (max_refunds_exceeded)
ReqHandler --> APIGW : 400 max_refunds_exceeded
APIGW --> Merchant : 400

== alt: Refund Window Expired [CON.5] ==

StateMachine -> StateMachine : capturedAt + 180d ≤ now
StateMachine --> ReqHandler : invalid (refund_window_expired)
ReqHandler --> APIGW : 409 refund_window_expired
APIGW --> Merchant : 409

== alt: Amount Exceeds Refundable ==

StateMachine -> StateMachine : amount > (capturedAmount - refundedAmount)
StateMachine --> ReqHandler : invalid (amount_exceeds_refundable)
ReqHandler --> APIGW : 400 amount_exceeds_refundable
APIGW --> Merchant : 400

== alt: Invalid State (status ≠ Captured) ==

StateMachine -> StateMachine : status ≠ Captured
StateMachine --> ReqHandler : invalid (invalid_state_transition)
ReqHandler --> APIGW : 409 invalid_state_transition
APIGW --> Merchant : 409

@enduml
```

---

## 4. UML State — Payment (reference from Lab 5)

The state machine is defined in Lab 5. Per the Guide: "one object per machine; states = I-6."

**Object:** Payment  
**States:** Pending, Authorized, Captured, Voided, Refunded, Declined, Failed  
**Terminal:** Voided, Refunded, Declined, Failed

See [Lab5-UML-LowLevel.md](Lab5-UML-LowLevel.md) §5 for full diagram.

---

## 5. Participant = SUT Map

| Sequence Lifeline | I-4 / I-2 / I-3 Match | Container or Actor |
|-------------------|------------------------|--------------------|
| Merchant Platform | I-3 | External System |
| API Gateway | I-4 | Container |
| Payment Orchestrator (box) | I-4 | Container (drilled to components; fraud module lives in Fraud Gate) |
| Idempotency Store | I-4 | Container |
| AcquirerHost | I-3 | External System |
| Payment Store | I-4 | Container |
| Message Queue | I-4 | Container |
| Webhook Service | I-4 | Container (async, happy path of all three use cases) |

**Component modules (inside Payment Orchestrator only):**
- Request Handler, Input Validator, Idempotency Manager, Fraud Gate, State Machine Engine, Acquirer Client, Persistence Manager, Event Publisher

These are internal to the **one selected container** (Payment Orchestrator) per Lab 9 C4 Component.

---

## 6. Coverage Note (G6)

### All state transitions mapped

| # | Transition | Covered in sequence |
|---|-----------|---------------------|
| 1 | Pending → Authorized | Authorize §1 (happy path) |
| 2 | Pending → Captured (Direct Charge) | Authorize §1 (alt: Direct Charge) |
| 3 | Pending → Declined (fraud) | Authorize §1 (alt: Fraud Block) |
| 4 | Pending → Declined (issuer) | Authorize §1 (alt: Issuer Decline) |
| 5 | Pending → Failed | Authorize §1 (alt: Acquirer Timeout) |
| 6 | Authorized → Captured | Capture §2 (happy path) |
| 7 | Authorized → Voided | (Void flow — same pattern as Capture without fraud) |
| 8 | Authorized → Failed (expired) | (Expiry Job — Lab 5 §5 note) |
| 9 | Captured → Refunded | Refund §3 (alt: Full Refund) |
| 10 | Captured → Captured (partial) | Refund §3 (happy path) |

### All sequence alt fragments mapped

| # | Alt | Use Case | Sequence section |
|---|-----|----------|-----------------|
| 1 | Direct Charge → Captured (immediate capture) | Authorize | §1 alt: Direct Charge |
| 2 | Fraud block → Declined | Authorize | §1 alt: Fraud Block |
| 3 | Issuer decline → Declined | Authorize | §1 alt: Issuer Decline |
| 4 | Idempotency duplicate → cached | Authorize | §1 alt: Idempotency Duplicate |
| 5 | Concurrent same-key → 409 | Authorize | §1 alt: Concurrent Same Key |
| 6 | Acquirer timeout → Failed | Authorize | §1 alt: Acquirer Timeout |
| 7 | Auth expired → 409 | Capture | §2 alt: Authorization Expired |
| 8 | Amount exceeds authorized → 400 | Capture | §2 alt: Amount Exceeds |
| 9 | Invalid state → 409 | Capture | §2 alt: Invalid State |
| 10 | Partial capture → void remainder | Capture | §2 alt: Partial Capture |
| 11 | Max refunds → 400 | Refund | §3 alt: Max Refunds Exceeded |
| 12 | Refund window → 409 | Refund | §3 alt: Refund Window Expired |
| 13 | Amount exceeds refundable → 400 | Refund | §3 alt: Amount Exceeds |
| 14 | Invalid state → 409 | Refund | §3 alt: Invalid State |
| 15 | Full refund → Refunded | Refund | §3 alt: Full Refund |

### Participants = C4 Container names ✓

All lifelines verified against Lab 1 I-4 / I-2 / I-3. Component modules only inside the one selected container (Payment Orchestrator).

**G6 passed:** All transitions + all alts mapped; participants = C4 names. ✓

---

## 7. Comparison Note — Lab 5 vs This Sitting

Lab 10 restyles Lab 5's three use-case sequences against the Guide, using Lab 9's Container/Component names. `Lb/Lab5-UML-LowLevel.md` is left as written — nothing there was edited to look like this file.

### 7.1 Names

| Aspect | Lab 5 (current style) | Lab 10 (this sitting) |
|--------|------------------------|-------------------------|
| Container-level participants | `Merchant Platform`, `API Gateway`, `Payment Orchestrator`, `Idempotency Store`, `AcquirerHost`, `Payment Store`, `Message Queue`, `Webhook Service` — same I-2/I-3/I-4 strings as Lab 1 | Identical strings, no forks |
| Fraud handling | A self-call on `Payment Orchestrator` (no separate lifeline) | Exploded one level further into a named component, `Fraud Gate`, per Lab 9 §3 — still not a container |
| `Payment Orchestrator` detail | One box, opaque | Drilled into 8 components (Request Handler, Input Validator, Idempotency Manager, Fraud Gate, State Machine Engine, Acquirer Client, Persistence Manager, Event Publisher) — the same 8 named in Lab 9 C4 Component |
| Merchant Platform PlantUML type | `actor` (a UML actor stereotype used loosely) | `participant` — `Merchant Platform` is an I-3 external system, not an I-2 person, so it does not get the actor stick-figure |

### 7.2 Language / header

Lab 5 has no diagram header — plain title, a one-line scope note, `plantuml` fences. That is correct for its sitting (current style, pre-Lab 7).

Lab 10 adds, per canvas: `Title / Viewpoint / Layer(s) / As-Is|To-Be|Transition / Owner / RACI / Version / Legend / Scope`, matching the Guide template from Lab 7 §7. This is the only structural difference between the two files — the message-level logic is the same story, told once in plain UML and once through the Guide's packaging.

### 7.3 What this sitting corrected relative to Lab 5

- **Webhook hop.** Lab 5's Authorize sequence already ends `Message Queue → Webhook Service → Merchant Platform` (async). Lab 10 initially stopped at `publish event` on all three use cases; this sitting added the same async hop to Capture and Refund too, so every happy path now ends the way I-11 describes it.
- **Direct Charge alt.** Lab 5's state machine allows `Pending → Captured`, but neither Lab 5 nor the first cut of Lab 10 drew the sequence for it. Added as an `alt: Direct Charge` branch on Authorize.
- **Issuer Decline alt.** Lab 5 draws this as an `else` branch inside the acquirer-call `alt`. The first cut of Lab 10 only referenced it as "implied in Lab 5" in the coverage table without drawing it. Added as its own `alt: Issuer Decline` block.
- **Module boxes inside Payment Orchestrator.** Lab 5 treats `Payment Orchestrator` as one opaque participant. Lab 10 is where the component detail is introduced (per Lab 9 C4 Component) — this is new content in Lab 10, not a fix to Lab 5.
