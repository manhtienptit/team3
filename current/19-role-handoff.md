# 19 - Role Handoff

**Title:** Modeling Pack Role Handoff  
**Viewpoint:** Governance  
**As-Is | To-Be | Transition:** To-Be  
**Owner:** EA - Team 3  
**RACI:** R EA, A Business Owner, C SA/BA/Dev/Test/Ops, I Owner  
**Version:** v1.0.0  **Date:** 2026-08-21  **Status:** Draft

| Role | Name | Input | Output | Consumer |
|---|---|---|---|---|
| EA | Tien | Strategy and constraints | Motivation, strategy, principles | SA, BA, Owner |
| BA / PO | Team 3 | Goals and journeys | Process and use cases | SA, Test, Owner |
| SA | Huy | Business and strategy views | C4 L1/L2, cooperation, NFRs | Dev, DA, Sec, Ops, Test |
| DA | Team 3 | Objects and containers | Source-of-truth review | Dev, Test, Sec |
| Dev | Minh | C4 L2, contracts, states | Sequences and design | Test, Ops, SA |
| Test | Dat | Process, state, sequence, constraints | G6 planned coverage | Dev, SA, Owner |
| Ops | Team 3 | Technology view and containers | Logical deployment constraints | Dev, SA, Test |

## Guide adoption

The Lab 7 Guide is adopted as written. G1-G6 are the only quality gates. Lab 3 remains N/A because this is a drawing pack with no implementation, automated tests, or runtime stand-up.

| Gate | Pass evidence | Status |
|---|---|---|
| G1 Strategy signed | 01 Motivation / Strategy | Pass |
| G2 Process + states | 02 Business Process and 12 UML Activity / State | Pass |
| G3 C4 Context + Container | 05 and 06 | Pass |
| G4 Contracts | Contract checklist in before pack / project root | Pass as checklist |
| G5 Critical exception path | 11 UML sequences | Pass |
| G6 Test coverage | 12 state/activity plus sequence alternatives | Pass as planned coverage |
