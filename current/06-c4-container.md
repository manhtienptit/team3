# 06 - C4 Container (L2)

**Title:** C4 Container - Online Payment Gateway  
**Viewpoint:** C4 Container  
**Layer(s):** Application  
**As-Is | To-Be | Transition:** To-Be  
**Owner:** SA - Team 3  
**RACI:** R SA, A SA, C DA/Sec/Dev/Ops, I Owner/BA/Test  
**Version:** v1.0.0  **Date:** 2026-08-21  **Status:** Draft  
**Legend:** solid edges are sync; dashed edges are async; protocol labels are shown only on this C4 view.  
**Scope:** eight internal containers and three named external payment systems.

```mermaid
flowchart LR
  merchant([Merchant]) -->|HTTPS sync commands and queries| api[Payment API]
  subgraph gateway[Online Payment Gateway]
    api -->|sync| orch[Payment Orchestrator]
    orch -->|sync persist| store[(Payment Store)]
    orch -->|sync project| query[(Query Store)]
    orch -->|sync auth only| fraud[Fraud Engine]
    orch -->|sync operations| connector[Acquirer Connector]
    orch -.->|async status event| queue[[Webhook Event Queue]]
    queue -.->|async consume| webhook[Webhook Service]
  end
  connector -->|sync idempotent reference| acquirer[[Acquirer]]
  acquirer -->|sync route| network[[Card Network]]
  network -->|sync decision| issuer[[Issuing Bank]]
  webhook -.->|async signed retryable delivery| merchant
```

Fraud Engine is absent from capture, void, and refund paths. Query Store has no external payment dependency. Source: [payment-container.puml](views/payment-container.puml).
