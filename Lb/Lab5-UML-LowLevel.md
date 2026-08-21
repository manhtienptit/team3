# Lab 5 — Low-Level Design (UML)

**R:** Dev (sequence) · Test (activity/state) · **A:** SA (sequence) · BA (activity/state)

---

## 1. UML Sequence — Authorize Payment

```
Title:      Authorize Payment — Happy Path + Exception
Viewpoint:  UML Sequence
Layer(s):   Delivery
As-Is | To-Be | Transition:  To-Be
Owner:      Role Dev  Name Kim Đức Minh
RACI:       R Dev  A SA  C Test, BA  I Ops
Version:    v1.0  Date 2026-08-20  Status Draft
Legend:      →  sync call; --→  async; alt = exception branch
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: US Authorize Payment / out-of-scope: capture, void, refund
```

### Participants (⊆ I-4 containers + I-3 externals)

- Merchant Platform
- API Gateway
- Payment Orchestrator (fraud module evaluates in-process — not a separate participant)
- Idempotency Store
- AcquirerHost
- Payment Store
- Message Queue

### Sequence

```plantuml
@startuml
actor "Merchant Platform" as Merchant
participant "API Gateway" as APIGW
participant "Payment Orchestrator" as Orch
participant "Idempotency Store" as Redis
participant "AcquirerHost" as Acquirer
database "Payment Store" as PG
queue "Message Queue" as MQ

Merchant -> APIGW : POST /v1/payments\n{amount, card, idempotency_key, capture:false}
APIGW -> APIGW : Validate input\n(amount 10K–500M, Luhn, expiry)

alt amount < 10,000 or > 500,000,000 or Luhn fail
    APIGW --> Merchant : 400 Bad Request
else valid input
    APIGW -> Orch : Forward validated request
end

Orch -> Redis : GET idempotency:{key}

alt idempotency hit (key exists, not in-flight)
    Redis --> Orch : cached response
    Orch --> APIGW : cached HTTP status + body
    APIGW --> Merchant : 200 (cached)
else concurrent same-key (in-flight lock exists)
    Redis --> Orch : lock detected
    Orch -> Redis : BLPOP idempotency:{key}:done 5s
    alt timeout after 5s
        Orch --> APIGW : 409 idempotency_conflict
        APIGW --> Merchant : 409 Conflict
    else first request completes
        Orch -> Redis : GET idempotency:{key}
        Redis --> Orch : cached response
        Orch --> APIGW : cached HTTP status + body
        APIGW --> Merchant : 200 (cached)
    end
else new key (miss)
    Redis --> Orch : miss
    Orch -> Redis : SET idempotency:{key}:lock 1 EX 35 NX
end

Orch -> Orch : evaluate fraud rules (in-process)\n(card, amount, merchant)
note right of Orch : 5 rules, < 50ms\nFRAUD-01→05\nFirst-block-wins

alt fraud block (any rule triggers)
    Orch -> PG : INSERT Payment(status=Declined,\ndecline_reason=fraud_rule, fraud_rule_id)
    Orch -> Redis : SET idempotency:{key} {response} EX 172800
    Orch -> MQ : publish payment.declined
    Orch --> APIGW : 200 {status: "declined"}
    APIGW --> Merchant : 200 Declined
else fraud pass
end

Orch -> Acquirer : authorize(amount, card_ref)\ntimeout=30s

alt acquirer timeout
    Orch -> Acquirer : retry (same reference)\ntimeout=30s, after 5s wait
    alt retry also times out
        Orch -> PG : INSERT Payment(status=Failed)
        Orch -> Redis : SET idempotency:{key} {response} EX 172800
        Orch -> MQ : publish payment.failed
        Orch --> APIGW : 200 {status: "failed"}
        APIGW --> Merchant : 200 Failed
    end
else issuer declines
    Acquirer --> Orch : DECLINE {reason_code}
    Orch -> PG : INSERT Payment(status=Declined,\ndecline_reason=issuer_decline)
    Orch -> Redis : SET idempotency:{key} {response} EX 172800
    Orch -> MQ : publish payment.declined
    Orch --> APIGW : 200 {status: "declined"}
    APIGW --> Merchant : 200 Declined
else issuer approves
    Acquirer --> Orch : APPROVE {auth_code}
    Orch -> PG : INSERT Payment(status=Authorized,\nauth_code, expiresAt=now+7d)
    Orch -> Redis : SET idempotency:{key} {response} EX 172800
    Orch -> MQ : publish payment.authorized
    Orch --> APIGW : 201 {status: "authorized", id, auth_code}
    APIGW --> Merchant : 201 Authorized
end

@enduml
```

---

## 2. UML Sequence — Capture Payment

```
Title:      Capture Payment — Happy Path + Exception
Viewpoint:  UML Sequence
Layer(s):   Delivery
As-Is | To-Be | Transition:  To-Be
Owner:      Role Dev  Name Kim Đức Minh
RACI:       R Dev  A SA  C Test, BA  I Ops
Version:    v1.0  Date 2026-08-20  Status Draft
Legend:      →  sync call; alt = exception branch
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: US Capture Payment / out-of-scope: authorize, void, refund
```

### Participants

- Merchant Platform
- API Gateway
- Payment Orchestrator
- Idempotency Store
- Payment Store
- AcquirerHost
- Message Queue

### Sequence

```plantuml
@startuml
actor "Merchant Platform" as Merchant
participant "API Gateway" as APIGW
participant "Payment Orchestrator" as Orch
participant "Idempotency Store" as Redis
database "Payment Store" as PG
participant "AcquirerHost" as Acquirer
queue "Message Queue" as MQ

Merchant -> APIGW : POST /v1/payments/{id}/capture\n{amount, idempotency_key}
APIGW -> Orch : Forward request

Orch -> Redis : GET idempotency:{key}

alt idempotency hit
    Redis --> Orch : cached response
    Orch --> APIGW : cached
    APIGW --> Merchant : 200 (cached)
else new key
    Redis --> Orch : miss
    Orch -> Redis : SET lock
end

Orch -> PG : SELECT Payment WHERE id={id}

alt status ≠ Authorized
    Orch --> APIGW : 409 invalid_state_transition
    APIGW --> Merchant : 409
else expiresAt ≤ now
    Orch --> APIGW : 409 authorization_expired
    APIGW --> Merchant : 409
else amount > authorizedAmount
    Orch --> APIGW : 400 amount_exceeds_authorized
    APIGW --> Merchant : 400
else valid (Authorized + not expired + amount ≤ auth)
    Orch -> Acquirer : capture(payment_ref, amount)\ntimeout=30s
    
    alt acquirer approves capture
        Acquirer --> Orch : CAPTURE_OK
        Orch -> PG : UPDATE Payment SET status=Captured,\ncapturedAmount={amount}
        
        alt partial capture (amount < authorized)
            Orch -> Acquirer : void_remainder(payment_ref, authorized - amount)
            Orch -> PG : UPDATE remainderVoided=true
        end
        
        Orch -> Redis : SET idempotency:{key} {response} EX 172800
        Orch -> MQ : publish payment.captured
        Orch --> APIGW : 200 {status: "captured"}
        APIGW --> Merchant : 200 Captured
    else acquirer timeout (after retry)
        Orch -> PG : (no status change, remains Authorized)
        Orch --> APIGW : 200 {status: "failed"}
        APIGW --> Merchant : 200 Failed
    end
end

@enduml
```

---

## 3. UML Sequence — Refund Payment

```
Title:      Refund Payment — Happy Path + Exception
Viewpoint:  UML Sequence
Layer(s):   Delivery
As-Is | To-Be | Transition:  To-Be
Owner:      Role Dev  Name Kim Đức Minh
RACI:       R Dev  A SA  C Test, BA  I Ops
Version:    v1.0  Date 2026-08-20  Status Draft
Legend:      →  sync call; alt = exception branch
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: US Refund Payment / out-of-scope: authorize, capture, void
```

### Participants

- Merchant Platform
- API Gateway
- Payment Orchestrator
- Idempotency Store
- Payment Store
- AcquirerHost
- Message Queue

### Sequence

```plantuml
@startuml
actor "Merchant Platform" as Merchant
participant "API Gateway" as APIGW
participant "Payment Orchestrator" as Orch
participant "Idempotency Store" as Redis
database "Payment Store" as PG
participant "AcquirerHost" as Acquirer
queue "Message Queue" as MQ

Merchant -> APIGW : POST /v1/payments/{id}/refund\n{amount, idempotency_key}
APIGW -> Orch : Forward request

Orch -> Redis : GET idempotency:{key}

alt idempotency hit
    Redis --> Orch : cached
    Orch --> APIGW : cached
    APIGW --> Merchant : 200 (cached)
else new key
    Redis --> Orch : miss
    Orch -> Redis : SET lock
end

Orch -> PG : SELECT Payment WHERE id={id}

alt status ≠ Captured
    Orch --> APIGW : 409 invalid_state_transition
    APIGW --> Merchant : 409
else amount > (capturedAmount - refundedAmount)
    Orch --> APIGW : 400 amount_exceeds_refundable
    APIGW --> Merchant : 400
else refundCount ≥ 10
    Orch --> APIGW : 400 max_refunds_exceeded
    APIGW --> Merchant : 400
else capturedAt + 180d < now
    Orch --> APIGW : 409 refund_window_expired
    APIGW --> Merchant : 409
else valid (Captured + amount ≤ remaining + count < 10 + ≤ 180d)
    Orch -> Acquirer : refund(payment_ref, amount)\ntimeout=30s
    
    alt acquirer approves refund
        Acquirer --> Orch : REFUND_OK
        Orch -> PG : UPDATE Payment SET\nrefundedAmount += amount,\nrefundCount += 1
        
        alt refundedAmount = capturedAmount (full refund)
            Orch -> PG : UPDATE status = Refunded
            Orch -> MQ : publish payment.refunded
        else partial refund
            Orch -> PG : (status remains Captured)
            Orch -> MQ : publish payment.refunded (partial)
        end
        
        Orch -> Redis : SET idempotency:{key} {response} EX 172800
        Orch --> APIGW : 200 {status, refundedAmount}
        APIGW --> Merchant : 200
    else acquirer timeout (after retry)
        Orch --> APIGW : 200 {status: "failed"}
        APIGW --> Merchant : 200 Failed
    end
end

@enduml
```

---

## 4. UML Activity — Payment Authorization Process

```
Title:      Payment Authorization Activity
Viewpoint:  UML Activity
Layer(s):   Delivery
As-Is | To-Be | Transition:  To-Be
Owner:      Role Test  Name Trần Quốc Đạt
RACI:       R Test  A BA  C Dev, SA  I Ops
Version:    v1.0  Date 2026-08-20  Status Draft
Legend:      ◆ = decision; [guard] = CON.* constraint
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: authorization happy path + decisions
```

```plantuml
@startuml
start

:Merchant Platform submits POST /v1/payments;

:API Gateway validates input;
if (amount 10K–500M VND AND Luhn pass AND card not expired?) then (yes)
else (no [CON.1])
  :Return 400 Bad Request;
  stop
endif

:Payment Orchestrator checks Idempotency Store;
if (key exists?) then (hit)
  :Return cached response;
  stop
elseif (concurrent same-key?) then (in-flight [CON.2])
  :Wait 5s (BLPOP);
  if (first completes within 5s?) then (yes)
    :Return cached response;
    stop
  else (no)
    :Return 409 idempotency_conflict;
    stop
  endif
else (miss)
  :Set in-flight lock;
endif

:Payment Orchestrator evaluates fraud rules (in-process);
note right: FRAUD-01→05\n< 50ms [CON.3]

if (any rule blocks?) then (block [CON.3])
  :Payment → Declined\n(fraud_rule, FRAUD-XX);
  :Publish payment.declined;
  stop
else (pass)
endif

:Route to AcquirerHost;
note right: 30s timeout [CON.6]

if (timeout?) then (yes)
  :Retry after 5s (same reference);
  if (retry also times out?) then (yes [CON.6])
    :Payment → Failed;
    :Publish payment.failed;
    stop
  else (no)
  endif
else (no)
endif

if (issuer approves?) then (yes)
  :Payment → Authorized\n(expiresAt = now + 7d) [CON.4];
  :Persist to Payment Store;
  :Publish payment.authorized;
  :Return 201 Authorized;
  stop
else (decline)
  :Payment → Declined\n(issuer reason code);
  :Publish payment.declined;
  :Return 200 Declined;
  stop
endif

@enduml
```

---

## 5. UML State Machine — Payment Object

```
Title:      Payment State Machine
Viewpoint:  UML State Machine
Layer(s):   Delivery
As-Is | To-Be | Transition:  To-Be
Owner:      Role Test  Name Trần Quốc Đạt
RACI:       R Test  A BA  C Dev, SA  I Ops
Version:    v1.0  Date 2026-08-20  Status Draft
Legend:      → transition; [guard]; terminal = double-circle
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope: Payment object lifecycle / out-of-scope: Webhook Event, Idempotency Entry
```

**Object:** Payment (one object per state machine)

```plantuml
@startuml
[*] --> Pending : request received

Pending --> Authorized : issuer approves
Pending --> Declined : issuer declines OR fraud blocks
Pending --> Failed : acquirer timeout (30s + 1 retry exhausted)\nOR system error

Authorized --> Captured : capture succeeds\n[expiresAt > now AND amount ≤ authorized]
Authorized --> Voided : void succeeds\n[status = Authorized]
Authorized --> Failed : authorization expired\n[expiresAt ≤ now, hourly job]

Captured --> Refunded : full refund\n[refundedAmount = capturedAmount]
Captured --> Captured : partial refund\n[amount ≤ remaining AND count < 10 AND ≤ 180d]

Voided --> [*]
Refunded --> [*]
Declined --> [*]
Failed --> [*]

note right of Authorized
  Hold window: 7 calendar days [CON.4]
  Valid next: Captured, Voided, Failed (expired)
end note

note right of Captured
  Refund window: 180 days [CON.5]
  Max partial refunds: 10 [CON.5]
end note

note bottom of Declined
  Terminal. Caused by:
  - Fraud block (FRAUD-01→05)
  - Issuer decline
end note

@enduml
```

---

## 6. G6 Checklist — Test Coverage

### 6.1 State Transitions → Planned Tests

| # | From | To | Trigger | Planned Test |
|---|------|----|---------|--------------| 
| T1 | Pending | Authorized | Issuer approves | Verify status=Authorized, auth_code set, expiresAt=+7d |
| T2 | Pending | Declined | Fraud blocks | Verify Declined, fraud_rule_id set, no acquirer call |
| T3 | Pending | Declined | Issuer declines | Verify Declined, reason_code from issuer |
| T4 | Pending | Failed | Acquirer timeout exhausted | Verify Failed after 30s+retry |
| T5 | Authorized | Captured | Capture succeeds | Verify Captured, capturedAmount set |
| T6 | Authorized | Voided | Void succeeds | Verify Voided, terminal |
| T7 | Authorized | Failed | Expiry job (7d elapsed) | Verify Failed, decline_reason=authorization_expired |
| T8 | Captured | Refunded | Full refund | Verify Refunded when refundedAmount=capturedAmount |
| T9 | Captured | Captured | Partial refund | Verify stays Captured, refundedAmount += amount |
| T10 | Any invalid | — (rejected) | Invalid transition attempt | Verify 409 invalid_state_transition |

### 6.2 Sequence Alt Fragments → Planned Tests

| # | Use Case | Alt Fragment | Planned Test |
|---|----------|--------------|--------------|
| A1 | Authorize | Fraud block (FRAUD-01→05) | Verify Declined, no acquirer call, fraud_rule_id |
| A2 | Authorize | Idempotency hit | Verify cached response returned, no external calls |
| A3 | Authorize | Idempotency concurrent (5s timeout) | Verify 409 idempotency_conflict |
| A4 | Authorize | Acquirer timeout + retry timeout | Verify Failed after retry exhausted |
| A5 | Authorize | Issuer decline | Verify Declined with reason code |
| A6 | Authorize | Input validation fail (amount/Luhn) | Verify 400, no state created |
| A7 | Capture | Auth expired | Verify 409 authorization_expired |
| A8 | Capture | Amount exceeds authorized | Verify 400 amount_exceeds_authorized |
| A9 | Capture | Status ≠ Authorized | Verify 409 invalid_state_transition |
| A10 | Capture | Partial capture (remainder voided) | Verify capturedAmount < authorized, remainder voided |
| A11 | Refund | Max refunds exceeded (≥10) | Verify 400 max_refunds_exceeded |
| A12 | Refund | Refund window expired (>180d) | Verify 409 refund_window_expired |
| A13 | Refund | Amount exceeds refundable | Verify 400 amount_exceeds_refundable |
| A14 | Refund | Status ≠ Captured | Verify 409 invalid_state_transition |

### 6.3 Participant = C4 Container Name Verification

| Sequence Lifeline | Matches I-4 / I-2 / I-3? | String |
|-------------------|---------------------------|--------|
| Merchant Platform | I-3 External | ✓ Merchant Platform |
| API Gateway | I-4 Container | ✓ API Gateway |
| Payment Orchestrator | I-4 Container | ✓ Payment Orchestrator |
| Idempotency Store | I-4 Container | ✓ Idempotency Store |
| AcquirerHost | I-3 External | ✓ AcquirerHost |
| Payment Store | I-4 Container | ✓ Payment Store |
| Message Queue | I-4 Container | ✓ Message Queue |

**All participants ⊆ Lab 1 name-identity index.** ✓
