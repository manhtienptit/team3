# 17 - NFR and Constraints

**Title:** NFR and Constraints - Online Payment Processing  
**Viewpoint:** Architecture constraints  
**Layer(s):** Strategy / Application  
**As-Is | To-Be | Transition:** To-Be  
**Owner:** SA - Team 3  
**RACI:** R SA, A Business Owner, C Ops/Sec, I EA/Dev/Test  
**Version:** v1.0.0  **Date:** 2026-08-21  **Status:** Draft  
**Legend:** NFRs are product requirements; no SLO, TPS, latency, RPO, or RTO is invented.  
**Scope:** NFR-01 through NFR-05 only.

| ID | Statement | Evidence |
|---|---|---|
| NFR-01 | Same idempotency key must not duplicate external calls or charges. | C4 Container; sequence alternatives |
| NFR-02 | Webhook delivery must not block synchronous payment response. | Queue boundary; webhook sequence |
| NFR-03 | Queries use gateway-owned data without external payment calls. | Query sequence |
| NFR-04 | Fraud runs after validation and before routing, authorization only. | Motivation; authorization sequence |
| NFR-05 | Payment transitions are enforced and invalid transitions rejected. | Payment state machine |

| ID | Constraint |
|---|---|
| CON.1 | Idempotent writes. |
| CON.2 | Fraud after validation before routing. |
| CON.3 | Defined Payment states only. |
| CON.4 | Async signed webhooks. |
| CON.5 | Queries use gateway-owned data. |

Open: acquirer timeout/retry policy, authorization expiry, fraud thresholds, webhook intervals/max, settlement timing, partial-capture remainder, supported networks, onboarding, rate limits, and currency.
