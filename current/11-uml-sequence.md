# 11 - UML Sequence

**Title:** Named Payment Operation Sequences  
**Viewpoint:** UML Sequence  
**Layer(s):** Application / Delivery  
**As-Is | To-Be | Transition:** To-Be  
**Owner:** Dev - Team 3  
**RACI:** R Dev, A SA, C BA/Sec/Test, I Owner/Ops  
**Version:** v1.0.0  **Date:** 2026-08-21  **Status:** Draft  
**Legend:** synchronous calls are solid; asynchronous webhook publication/delivery is dashed; every `alt` is a planned G6 test.  
**Scope:** named use cases only; participants are actors or exact C4 container names.

| Named sequence | Source | Required exception |
|---|---|---|
| Authorize a payment | [payment-sequences.puml](views/payment-sequences.puml) | Fraud block, issuer decline, timeout, duplicate key |
| Direct charge | [payment-sequences.puml](views/payment-sequences.puml) | Auth failure skips capture; capture failure retains Authorized |
| Capture an authorized payment | [payment-sequences.puml](views/payment-sequences.puml) | Invalid state/amount and acquirer failure |
| Void an authorized payment | [payment-sequences.puml](views/payment-sequences.puml) | Invalid state |
| Refund a captured payment | [payment-sequences.puml](views/payment-sequences.puml) | Excess amount and partial/full branch |
| Query payment details | [payment-sequences.puml](views/payment-sequences.puml) | Local read only; no external call |

Participant = SUT map: Payment API; Payment Orchestrator; Payment Store; Query Store; Fraud Engine; Acquirer Connector; Webhook Event Queue; Webhook Service. External participants: Merchant; Acquirer; Card Network; Issuing Bank.
