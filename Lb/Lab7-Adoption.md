# Lab 7 — Hierarchy, Focus Matrix, Quality Gates, RACI

**R:** EA · **A:** Owner

---

## 1. Adoption Record

The team adopts the **Guide** (from list.md) as written. G1–G6 and the RACI table are used without modification. No competing gate list, no parallel RACI.

**Statement:** Team 3 adopts the modeling guide as the single standard for the after pack. All after-pack diagrams will carry the diagram header with RACI letters. Quality gates G1–G6 are the only gates applied — `Quality-Gates-Architecture.md` and `Quality-Gates-Design.md` at the repo root are unused from this sitting onward. The RACI table from the Guide governs artifact ownership, copied as written (no rows re-assigned).

**Owner role.** No separate business owner is available for this exercise. Ninh Mạnh Tiến (EA, team lead) also plays **Owner** — the **A** on Motivation, Business Process, and C4 Context — acting as facilitator.

---

## 2. Group Roster — Role Assignments

| Person | Role(s) | Owns (output) |
|--------|---------|---------------|
| Ninh Mạnh Tiến | EA | Motivation / Strategy (Lab 8 View 1) |
| Nguyễn Quang Huy | SA | C4 Context + Container (Lab 9), Application Cooperation (Lab 8 View 3) |
| Kim Đức Minh | Dev | C4 Component (Payment Orchestrator), UML Sequence (Lab 5/10) |
| Trần Quốc Đạt | Test | UML State (Payment object), G6 coverage checklist |

*One person may hold two roles; the artifact still has one R and one A.*

---

## 3. Hierarchy (adopted from Guide)

| Level | Language | Focus | Readers | Typical views |
|-------|----------|-------|---------|---------------|
| **Top** — enterprise | ArchiMate | Governance, strategy, process | EA, Owner, Risk, BA | Motivation, Strategy, Business Process |
| **Middle** — solution | C4 (+ ArchiMate Application / Technology) | System boundary, containers | SA, DA, Security | C4 Context, C4 Container, Application Cooperation, Technology |
| **Base** — delivery | UML (+ one C4 Component) | Sequence, states, types | Dev, Test, Ops | C4 Component (one container), Sequence, Activity, State |

**Nesting thread:** Capability (ArchiMate Motivation) → System-in-focus (C4 Context) → Runnable container (C4 Container) → Module inside Payment Orchestrator (C4 Component) → Messages/states (UML Sequence, State).

---

## 4. Focus Matrix (adopted from Guide)

| | ArchiMate — landscape | C4 — bridge | UML — deployable behavior |
|---|---|---|---|
| **Focus** | Why / who / capability / layer | Which system, container, component | How it behaves; exact types |
| **Zoom** | Enterprise | Solution (L1–L2) and one-container design (L3) | Delivery |
| **Audience** | EA, Owner, Risk, BA | SA, DA, Security; Dev on L3 | Dev, Test, Ops |
| **Pack** | Architecture | Architecture owns L1–L2; Design owns L3 | Design |
| **Fail if** | JDBC or pods on Motivation / Process | Internals on Context; mixed L1+L2+L3 on one canvas | Lifelines that are not C4 names; several objects on one state machine |

---

## 5. Quality Gates G1–G6 (adopted from Guide)

| Gate | Blocks | Pass Rule (Payment Gateway) | Evidence | Pass? |
|------|--------|------------------------------|----------|:---:|
| **G1** Strategy signed | Solution design | Goal (merchant card payments), outcome (500 TPS, P95<2s, 99.9%), CON.1–CON.8 listed | Lab 8 View 1: Motivation | |
| **G2** Process + states | Dev + Test design | Payment states (7) match I-6; process shows CON.* on branches | Lab 8 View 2 + Lab 1 I-6 / Lab 3 test spec (until Lab 5 is Done, then + Lab 5 State) | |
| **G3** C4 Context + Container | Implementation | No unnamed externals; sync/async labeled; names = Lab 1 index | Lab 9 | |
| **G4** Contracts | Coding of integrations | OpenAPI for every Container relationship | Checklist (not drawn) | |
| **G5** Critical exception path | Production release | Fraud block, acquirer timeout, idemp conflict, auth expiry modeled | Lab 3 exception spec (until Lab 5 is Done, then + Lab 5/10 Sequence alts) | |
| **G6** Test coverage | UAT sign-off | All transitions + alts mapped; participants = C4 names | Lab 3 test spec (until Lab 5 is Done, then + Lab 5/10 G6 checklist) | |

**This pack draws through G3.** G4–G6 are checklists on the models. **Pass?** stays blank until Labs 8–10 exist — this sitting only registers the gates, it does not check them off.

---

## 6. RACI (adopted from Guide — per artifact)

| Artifact | EA | SA | BA/PO | DA | Sec | Dev | Test | Ops | Owner |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Motivation / Strategy | **R** | C | C | I | C | I | I | I | **A** |
| Business Process | C | C | **R** | I | C | I | C | I | **A** |
| C4 Context | C | **R** | C | I | C | I | I | I | **A** |
| C4 Container | **A** | **R** | I | C | C | C | I | C | I |
| C4 Component | I | **A** | I | C | C | **R** | C | I | I |
| Application Cooperation | **A** | **R** | I | C | C | C | I | I | I |
| UML Sequence | I | **A** | C | I | C | **R** | C | I | I |
| UML Activity / State | I | C | **A** | I | C | C | **R** | I | I |
| Technology / Deployment | I | **A** | I | I | C | C | I | **R** | I |

---

## 7. RACI Line Template (for every after diagram header)

```
Title:      ________________________________
Viewpoint:  ArchiMate / C4 / UML ___________
Layer(s):   Strategy / Business / App / Tech
As-Is | To-Be | Transition:  _______________
Owner:      Role ________  Name ____________
RACI:       R ____  A ____  C ____  I ____
Version:    v____  Date ________  Status Draft|Review|Approved
Legend:     relationships listed
RACI legend: R = draws · A = approves · C = consulted · I = informed
Scope:      in-scope / out-of-scope
```

---

## 8. Role Input → Output (Handoff)

| Role | Minimum input to start | Minimum output to hand off | Next consumer |
|------|------------------------|---------------------------|---------------|
| EA | Strategy, as-is landscape | Motivation, capabilities, principles | SA, BA, Owner |
| BA/PO | Goals, journeys | Process, product, use cases, activity | SA, Test, Owner |
| SA | EA + BA packs | C4 L1–L2, app cooperation, interfaces, NFRs | Dev, DA, Sec, Ops, Test |
| DA | Business objects + containers | Information structure, source of truth | Dev, Test, Sec |
| Sec | Constraints + C4 + data | Risk view, trust boundaries | Dev, Test, SA |
| Dev | C4 L2, contracts, sequence, states | C4 L3, as-built sequence | Test, Ops, SA |
| Test | Process, state, sequence, C4, constraints | Scenario catalog, coverage | Dev, SA, Owner |
| Ops | Tech view, containers, NFRs | Deployment, paths | Dev, SA, Test |

---

## 9. Automatic Fail Conditions (After Pack)

- Mixed languages on one diagram
- Forked names (box/lifeline string ≠ Lab 1 Input index)
- Missing legend
- Missing RACI letters on header
- Two **A**s on one artifact
- Internals on C4 Context
- Sequence participants that are not C4 Container names
