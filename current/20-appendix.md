# 20 — Appendix: concepts and short references

**Pack:** Cover / glossary  
**Handbook:** §1.4 (relationship legend), Appendix A (print legend), §2 (Alignment Gap)  
**Status:** Always present. Copy this file; add initiative-only terms in §4. Product-specific names belong on [00-index.md](00-index.md).

This appendix **explains** modeling and bank terms. It is not a diagram. Do not treat PCI-DSS, SBV, or Kubernetes as required product actors unless they apply.

A **Daily Transaction Banking** worked sample (closed names, NFRs) is in **§5** — copy those strings into `00-index` only when that is the product.

---

## 1. Short references (A–Z)

| Term | Expands to | Meaning in a dossier | See also |
| --- | --- | --- | --- |
| ADM | Architecture Development Method | TOGAF phases used to tag viewpoints (A–G) | Handbook §1.6 |
| ADR | Architecture Decision Record | Dated note of a significant choice: context, decision, consequences | [adr/](adr/) |
| API | Application Programming Interface | Contract on a C4 container / ArchiMate Application Interface | [08](08-application-cooperation.archimate.md) |
| ArchiMate | ArchiMate 3.2 | Enterprise notation: why / who / capability / layer | Handbook §1 |
| BA | Business Analyst | Owns process, product, use cases | [19](19-role-handoff.md) |
| BFF | Backend for Frontend | Channel-facing API facade (name it on 00-index) | [06](06-c4-container.md) |
| C4 | Context, Container, Component, Code | Software architecture levels L1–L3 used here (Code unused) | [05](05-c4-context.md)–[09](09-c4-component.md) |
| DA | Data Architect | Owns Information Structure and SoT | [04](04-information-structure.archimate.md) |
| DDD | Domain-Driven Design | Aggregates/entities on the UML class view — names must match Information Structure | [10](10-uml-domain-class.md) |
| Dev | Developer | Design pack: C4 L3 + UML | [09](09-c4-component.md)–[12](12-uml-activity-state.md) |
| E2E | End to end | Business-process / UAT tests mapped in traceability | [18](18-traceability.md) |
| EA | Enterprise Architect | Motivation, capabilities, plateaus, dossier governance | [01](01-motivation-strategy.archimate.md), [16](16-migration-plateau.archimate.md) |
| EOD | End of day | Often out of customer-product scope unless stated | |
| G1–G6 | Handoff quality gates | Block coding/UAT if red | [19](19-role-handoff.md) |
| HA | High availability | Runtime metric — product fact only if listed as NFR | [17](17-nfr-and-constraints.md) |
| HTTPS | Hypertext Transfer Protocol Secure | Typical channel protocol on C4 L2 (sync) | [06](06-c4-container.md) |
| ICT | Indochina Time | `Asia/Ho_Chi_Minh` when a Vietnam business-day clock applies | |
| IPC | Inter-process communication | Runtime calls between containers | [06](06-c4-container.md), [07](07-c4-deployment.md) |
| JDBC | Java Database Connectivity | Typical datastore access (label on C4, not ArchiMate) | [06](06-c4-container.md) |
| K8s | Kubernetes | Optional C4 Deployment; not a required product cluster | [07](07-c4-deployment.md) |
| L1 / L2 / L3 | C4 Context / Container / Component | Architecture owns L1–L2; Design owns L3 | Pack split |
| LPAR | Logical partition | Mainframe-style host node | [13](13-technology-deployment.archimate.md) |
| MFE | Micro-frontend | UI remote hosted by a shell (name it on 00-index) | |
| MOT.* | Motivation IDs | `MOT.DRV`, `MOT.GOAL`, `MOT.OUT`, `MOT.REQ`, `MOT.CON` | [01](01-motivation-strategy.archimate.md) |
| mTLS | Mutual TLS | One possible in-transit flavour | [15](15-risk-compliance.archimate.md) |
| NFR | Non-functional requirement | Product constraints with stable IDs | [17](17-nfr-and-constraints.md) |
| OA | Open assumption | Decision not closed on the product model | ADR / 00-index |
| Ops | DevOps / SRE / Infrastructure | C4 Deployment and ArchiMate Technology | [07](07-c4-deployment.md), [13](13-technology-deployment.archimate.md) |
| OTP | One-time password | Authn mechanism — draw only if in product scope | |
| PCI-DSS | Payment Card Industry Data Security Standard | Governance placeholder; only if card data is in scope | [15](15-risk-compliance.archimate.md) |
| PO | Product Owner | With BA on process and product | [03](03-organization-product.archimate.md) |
| QA | Tester / QA | State, sequence alts, coverage | [12](12-uml-activity-state.md) |
| RACI | Responsible, Accountable, Consulted, Informed | Who draws vs who approves | Handbook §6.2 |
| REST | Representational State Transfer | Typical HTTP API style on C4 L2 | [06](06-c4-container.md) |
| RPO | Recovery Point Objective | Operations metric unless listed as NFR | [17](17-nfr-and-constraints.md) |
| RTO | Recovery Time Objective | Operations metric unless listed as NFR | [17](17-nfr-and-constraints.md) |
| SA | Solution Architect | Architecture pack; **A** on L3 and sequences | [05](05-c4-context.md)–[08](08-application-cooperation.archimate.md) |
| SBV | State Bank of Vietnam | Ngân hàng Nhà nước — governance placeholder, not a posting actor | [15](15-risk-compliance.archimate.md) |
| Sec | Security Architect / Compliance / Risk | Trust boundaries, in-transit | [15](15-risk-compliance.archimate.md) |
| SLI | Service Level Indicator | Measured signal for an SLO | [17](17-nfr-and-constraints.md) |
| SLO | Service Level Objective | Target for an SLI | [17](17-nfr-and-constraints.md) |
| SoT | Source of truth | Which store or system owns a data object | [04](04-information-structure.archimate.md) |
| STR.CAP.* | Strategy capability IDs | Capabilities on the Motivation / Strategy view | [01](01-motivation-strategy.archimate.md) |
| SWIFT | Society for Worldwide Interbank Financial Telecommunication | Cross-border messaging — in scope only if listed | |
| TOGAF | The Open Group Architecture Framework | ADM alignment of viewpoints | Handbook §1.6 |
| TPS | Transactions per second | Throughput metric | [17](17-nfr-and-constraints.md) |
| UML | Unified Modeling Language | Sequence, state, activity, class | [10](10-uml-domain-class.md)–[12](12-uml-activity-state.md) |
| VCB | Vietcombank | Bank in the course samples | |
| VND | Vietnamese đồng | Currency — product fact only if listed | |
| VPN | Virtual private network | Possible in-transit flavour | [15](15-risk-compliance.archimate.md) |
| WAN | Wide area network | Path between sites / hosts | [13](13-technology-deployment.archimate.md) |

---

## 2. Business concepts (generic)

**Product vs variant.** Name **one** product on 00-index. Channels, rails, or brands are not extra products unless the owner says they are.

**Name identity.** ArchiMate Application Component **is** the C4 Container **is** the UML sequence participant **is** the test SUT. List the strings once on [00-index.md](00-index.md). Do not fork names across views.

**Source of truth.** Each data object has one SoT. A read model is not a second ledger.

**Statuses.** List allowed states on [12](12-uml-activity-state.md) for **one** object. Testers cover every transition.

---

## 3. Technology / modeling concepts

**Alignment Gap.** ArchiMate is the landscape (why / who / capability). C4 is the bridge (which system, container, component). UML is behaviour and types. One language per diagram.

**Architecture pack vs Design pack.** Architecture: ArchiMate + C4 L1/L2 (`01`–`08`, `13`–`17`). Design: C4 L3 + UML (`09`–`12`). Dev **R** on L3; SA **A**.

**ArchiMate relationships (short).** Do not invent “uses”, “calls”, or “depends”. Full table: handbook **§1.4**.

| Name | One-line | Not for |
| --- | --- | --- |
| Serving | Provides to | Data read |
| Access | Read/write an object | Component-to-component call |
| Triggering | Causal / sequence | Sync API dependency |
| Realization | Lower makes upper real | Deploying a JAR (that is Assignment) |
| Assignment | Actor does process; node runs component | HTTP call |
| Flow | Information or value | Control flow (use Triggering) |

Composition, Aggregation, Influence, Specialization, Association: see §1.4.

**Layered realization.** A business service is realized by application services, then technology services on nodes — not “hosted on Kubernetes” in one skip. File [14](14-layered-realization.archimate.md).

**Plateau / Gap / Work Package.** Baseline → Gap → Target; work packages fund the move. File [16](16-migration-plateau.archimate.md).

**C4 Deployment (`07`) vs ArchiMate Technology (`13`).** `07` is runtime topology. `13` is logical nodes, environments, middleware. Do not merge languages.

---

## 4. Adding an initiative-only term

Add a row to §1 (or a short paragraph under §2 / §3). Put **closed names** on [00-index.md](00-index.md), not on every view.

---

## 5. Course sample — Daily Transaction Banking (optional)

Use this block **only** when the product is same-day domestic VND credit (handbook sample). Paste the closed names into 00-index.

**DTB** = Daily Transaction Banking. Initiative prefix `DTB-<nnn>`. **NAPAS** = National Payment Corporation of Vietnam (interbank rail, not a second product).

**Closed names:** Customer; AppShell; TransferMFE; HistoryMFE; ChannelBFF; PaymentOrchestration; LimitService; LimitStore; HistoryService; HistoryStore; CoreAdapter; NAPASAdapter; CoreBanking; NAPASSwitch.

**Product vs rail.** One product: Daily VND credit transfer. Internal (VCB→VCB) and NAPAS (VCB→other bank) are rails.

**Shared gate.** 50,000,000 VND volume **AND** 10 quantity, keyed by source account and 00:00 Asia/Ho_Chi_Minh. Gate **before** rail split.

**Objects.** `Transfer`, `DailyLimitBucket`, `HistoryRecord`. CoreBanking is the ledger; history is a read model.

**Statuses.** `Initiated`, `Pending`, `Completed`, `Failed` only. `Pending` = NAPAS in flight. Immediate release on `Failed` after a reservation.

**NFR-01…NFR-06** (do not invent more as product fact for this sample): atomic reserve; idempotencyKey; history does not call NAPAS; 00:00 ICT; subjectKey = source account; NAPAS wait ≤ 30s then reverse + release.

**OA-04/05/07/09/10/11** stay open. OA-10: vendor/HA/RTO. OA-11: in-transit required, flavour open.

**Nesting thread:** Daily limit enforcement → DailyTransactionBanking → LimitService → VolumeCheck AND QuantityCheck AND AtomicReserveRelease → reserve-before-rail.

**Mandatory sequences for this sample:** Internal (no NAPAS), NAPAS (30s + reverse/release), inquiry (no NAPAS). L3 drill-down: LimitService.
