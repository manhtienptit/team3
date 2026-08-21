# 18 - Traceability

**Title:** Requirements to Modeling Traceability  
**Viewpoint:** Governance  
**Layer(s):** All modeled layers  
**As-Is | To-Be | Transition:** To-Be  
**Owner:** SA - Team 3  
**RACI:** R SA, A EA, C Test, I Owner  
**Version:** v1.0.0  **Date:** 2026-08-21  **Status:** Draft

| Requirement | Viewpoint / file | Element or path | Planned evidence |
|---|---|---|---|
| US-01 Authorize | 05, 06, 11 | API -> Orchestrator -> Fraud Engine -> Acquirer Connector | Auth approved, blocked, declined, timeout |
| US-02 Direct charge | 06, 11 | Auth path + immediate capture | Auth fail skips capture; capture fail retains Authorized |
| US-03 Capture | 06, 11 | Orchestrator -> Acquirer Connector | Authorized guard and amount guard |
| US-04 Void | 06, 11 | Orchestrator -> Acquirer Connector | Authorized-only transition |
| US-05 Refund | 06, 11 | Orchestrator -> Acquirer Connector | Partial/full and remaining amount |
| US-06 Lifecycle | 12 | Payment state machine | Seven statuses and transitions |
| US-07 Idempotency | 06, 11 | Orchestrator dedup | Duplicate key returns original result |
| US-08 Webhook | 06, 08, 11 | Queue -> Webhook Service -> Merchant | Async signature/retry |
| US-09 Query | 06, 11 | API -> Query Store | No external call |
| NFR-01..05 | 01, 06, 12, 17 | Constraints and paths | G1-G6 review |
