# 00 - Dossier Index

**Pack:** Current Lab 4 after pack  
**Initiative:** PAY-001  
**Product:** Online Payment Processing Gateway  
**Title:** Online Payment Gateway - Modeling-Driven Design  
**Version:** v1.0.0  
**Status:** Draft  
**Date:** 2026-08-21

## Owners

| Role | Name | Notes |
|---|---|---|
| EA | Tien | Motivation / strategy and governance |
| SA | Huy | C4 and application cooperation |
| BA / PO | Team 3 | Process and requirements |
| DA | Team 3 | Source-of-truth review |
| Sec | Team 3 | Constraints and webhook integrity |
| Dev | Minh | UML sequences and design |
| Test | Dat | State, activity, and G6 coverage |
| Ops | Team 3 | Technology view |
| Business Owner | Team 3 | Approval |

## Name identity

ArchiMate Application Component **is** the C4 Container **is** the UML sequence participant **is** the test SUT.

| Kind | Names |
|---|---|
| Person / Business Actor | Merchant; Customer |
| System-in-focus | Online Payment Gateway |
| External systems | Acquirer; Card Network; Issuing Bank |
| Containers | Payment API; Payment Orchestrator; Payment Store; Query Store; Fraud Engine; Acquirer Connector; Webhook Event Queue; Webhook Service |
| Key data objects | Payment; PaymentMethod; WebhookEvent; FraudRule |

## File inventory

| File | Status | Owner |
|---|---|---|
| 00-index.md | Draft | EA |
| 01-motivation-strategy.archimate.md | Draft | EA |
| 02-business-process.archimate.md | Draft | BA / PO |
| 03-organization-product.archimate.md | N/A - not in Lab 4 named set | BA / PO |
| 04-information-structure.archimate.md | N/A - domain identity recorded in 10 | DA |
| 05-c4-context.md | Draft | SA |
| 06-c4-container.md | Draft | SA |
| 07-c4-deployment.md | N/A - no runtime deployment in drawing pack | Ops |
| 08-application-cooperation.archimate.md | Draft | SA |
| 09-c4-component.md | N/A - optional L3 omitted | Dev |
| 10-uml-domain-class.md | Draft | Dev |
| 11-uml-sequence.md | Draft - named use cases | Dev |
| 12-uml-activity-state.md | Draft | Test |
| 13-technology-deployment.archimate.md | Draft | Ops |
| 14-layered-realization.archimate.md | N/A - not required by Lab 4 | SA |
| 15-risk-compliance.archimate.md | N/A - no additional risk view required | Sec |
| 16-migration-plateau.archimate.md | N/A - simulated To-Be model only | EA |
| 17-nfr-and-constraints.md | Draft | SA |
| 18-traceability.md | Draft | SA |
| 19-role-handoff.md | Draft | EA |
| 20-appendix.md | Draft | EA |
| 21-hierarchy.md | Draft - Lab 7 | EA |
| 22-focus-matrix.md | Draft - Lab 7 | EA |
| 23-quality-gates.md | Draft - Lab 7; G1-G6 only | EA |
| 24-raci.md | Draft - Lab 7 | EA |
| adr/ | Present; no ADR required | EA |

## Cross-language consistency

| Check | Result |
|---|---|
| C4 people and externals have matching identity entries | Pass |
| Sequence participants are actors or I-4 containers | Pass |
| Payment is the one state-machine object | Pass |
| Protocol labels occur only on C4 Container | Pass |
| Constraints appear on Motivation and decision branches | Pass |
| Every after view has header, legend, scope, and RACI | Pass |

Before archive: [../before](../before)  
PlantUML sources: [views](views)
