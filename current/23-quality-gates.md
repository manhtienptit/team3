# 23 - Lab 7 Quality Gates

**Initiative:** PAY-001 - Online Payment Processing Gateway  
**Status:** Draft  
**RACI:** R EA, A Owner, C SA/BA/DA/Sec/Dev/Test/Ops, I all consumers

The Team 3 pack uses **G1-G6 only**, adopted from the Lab 7 Guide. The gates block coding or UAT if red. This file does not create a parallel gate set.

| Gate | Blocks | Guide pass rule | PAY-001 evidence | Status |
|---|---|---|---|---|
| G1 Strategy signed | Solution design | Goal, outcome, constraints listed | `01-motivation-strategy.archimate.md` | Pass |
| G2 Process + states | Dev + Test design | Named states match the information / state view | `02-business-process.archimate.md`, `12-uml-activity-state.md` | Pass |
| G3 C4 Context + Container | Implementation | No unnamed externals; sync / async labeled; names match the Input index | `05-c4-context.md`, `06-c4-container.md`, `00-index.md` | Pass |
| G4 Contracts | Coding of integrations | Contract for every relationship on the Container diagram | `Contract-Checklist.md` | Pass as checklist |
| G5 Critical exception path | Production release | Compensating actions on the critical failure path are modeled | `11-uml-sequence.md` and `Contract-Checklist.md` | Pass as modeled evidence |
| G6 Test coverage | UAT sign-off | All state transitions + sequence alts mapped; participants = C4 names | `12-uml-activity-state.md`, `11-uml-sequence.md` | Pass as planned coverage |

## Lab 7 boundary

This pack draws through G3. G4-G6 are checklists on the models. No implementation, automated test execution, MVP, Docker, or runtime stand-up is included.

## Quality-gate controls

- Do not add G7 or any custom replacement gate.
- Keep exactly one accountable role per after artifact, except the dossier index.
- Use the identity index in `00-index.md` for all downstream names.
- Keep ArchiMate, C4, and UML as separate viewpoints.
