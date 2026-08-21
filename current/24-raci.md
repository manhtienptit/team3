# 24 - Lab 7 RACI

**Initiative:** PAY-001 - Online Payment Processing Gateway  
**Status:** Draft  
**RACI:** R EA, A Owner, C SA/BA/DA/Sec/Dev/Test/Ops, I all consumers

RACI is per artifact, not per job title. One person may hold two roles, but each artifact has one R and one A. The Guide meanings are adopted as written.

## Adoption record

Team 3 adopts the Lab 7 Guide in `lab7/list.md` as written. G1-G6 are the only quality gates, and the Guide RACI is used without a competing gate or responsibility model.

| Guide role | Team member | Adoption responsibility |
|---|---|---|
| EA | Tien | Owns hierarchy, focus matrix, quality-gate adoption, and governance. |
| SA | Huy | Owns solution architecture and approves design handoffs. |
| Dev | Minh | Owns named UML sequence design and delivery detail. |
| Test | Dat | Owns Payment state/activity modeling and planned G6 coverage. |

One person may hold more than one Guide role; this roster assigns one primary person to each role for Lab 7. `Owner` remains the approving business role in the Guide.

| Letter | Meaning | PAY-001 action |
|---|---|---|
| R | Responsible - draws | Produce the view and preserve identity names. |
| A | Accountable - approves | Accept or reject; exactly one on each after view. |
| C | Consulted - two-way before freeze | Review and constrain. |
| I | Informed - one-way after accept | Read; do not redraw. |

## Role abbreviations

| Abbr. | Role |
|---|---|
| Owner | Business Owner |
| PO | Product Owner |
| BA | Business Analyst |
| EA | Enterprise Architect |
| DA | Domain / Data Architect |
| SA | Solution Architect |
| Sec | Security / Compliance / Risk |
| Dev | Software engineer |
| Test | Quality engineer |
| Ops | DevOps engineer |

## Guide RACI matrix

| Artifact | EA | SA | BA / PO | DA | Sec | Dev | Test | Ops | Owner |
|---|---|---|---|---|---|---|---|---|---|
| Motivation / Strategy | R | C | C | I | C | I | I | I | A |
| Business Process | C | C | R | I | C | I | C | I | A |
| C4 Context | C | R | C | I | C | I | I | I | A |
| C4 Container | I | R | I | C | C | C | I | C | I |
| C4 Component | I | A | I | C | C | R | C | I | I |
| Application Cooperation | C | R | I | C | C | C | I | I | I |
| UML Sequence | I | A | C | I | C | R | C | I | I |
| UML Activity / State | I | C | A | I | C | C | R | I | I |
| Technology / Deployment | I | A | I | I | C | C | I | R | I |

## Header line for every current after view

```text
RACI: R ____  A ____  C ____  I ____
RACI legend: R = draws · A = approves · C = consulted · I = informed
```

## PAY-001 artifact assignments

| Current artifact | R | A | C | I |
|---|---|---|---|---|
| `01-motivation-strategy.archimate.md` | EA | Owner | SA, BA, Sec | Dev, Test, Ops |
| `02-business-process.archimate.md` | BA / PO | Owner | EA, SA, Sec, Test | Dev, Ops |
| `05-c4-context.md` | SA | Owner | EA, BA, Sec | Dev, Test, Ops |
| `06-c4-container.md` | SA | SA | DA, Sec, Dev, Ops | Owner, BA, Test |
| `08-application-cooperation.archimate.md` | SA | Owner | EA, DA, Sec, Dev | BA, Test, Ops |
| `11-uml-sequence.md` | Dev | SA | BA, Sec, Test | Owner, Ops |
| `12-uml-activity-state.md` | Test | BA | Dev, SA, Sec | Owner, Ops |
| `13-technology-deployment.archimate.md` | Ops | SA | Sec, Dev | Owner, BA, Test |
| `21-hierarchy.md` | EA | Owner | SA, BA, DA, Sec, Dev, Test, Ops | all consumers |
| `22-focus-matrix.md` | EA | Owner | SA, BA, Dev, Test | all consumers |
| `23-quality-gates.md` | EA | Owner | SA, BA, Dev, Test, Sec, Ops | all consumers |
| `24-raci.md` | EA | Owner | all role owners | all consumers |
