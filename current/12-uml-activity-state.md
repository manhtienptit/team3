# 12 - UML Activity / State

**Title:** Payment Activity and State  
**Viewpoint:** UML Activity and State  
**Layer(s):** Application / Delivery  
**As-Is | To-Be | Transition:** To-Be  
**Owner:** Test - Team 3  
**RACI:** R Test, A BA, C Dev/SA/Sec, I Owner/Ops  
**Version:** v1.0.0  **Date:** 2026-08-21  **Status:** Draft  
**Legend:** decisions show CON.*; state machine describes one object only; dashed arrows in source views indicate async webhook work.  
**Scope:** Payment workflow and Payment lifecycle.

**Object:** Payment  
**Allowed statuses:** Pending, Authorized, Captured, Voided, Refunded, Declined, Failed  
**Terminal states:** Voided, Refunded, Declined, Failed

```mermaid
flowchart TD
  a[Receive operation] --> b[Validate request and idempotency]
  b --> c{Duplicate key?}
  c -->|yes| d[Return original result]
  c -->|no| e{Authorization?}
  e -->|yes| f[Fraud gate after validation]
  f -->|block CON.2| g[Declined]
  f -->|pass| h[Call Acquirer]
  e -->|no| h
  h --> i[Apply CON.3 state transition]
  i --> j[Persist Payment and publish async event CON.4]
```

```mermaid
stateDiagram-v2
  [*] --> Pending
  Pending --> Authorized
  Pending --> Declined
  Pending --> Failed
  Authorized --> Captured
  Authorized --> Voided
  Captured --> Captured: partial refund
  Captured --> Refunded: full refund
```

Source: [payment-state-activity.puml](views/payment-state-activity.puml). Invalid transitions are explicit API rejects.
