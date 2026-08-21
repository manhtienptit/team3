# PAY-001 Current Pack

This folder is the Lab 4 standardized after pack for Online Payment Processing. It was created from `templates/` and uses the Guide in `lab7/list.md`.

- `../before/` is the unchanged archive of the original team pack.
- This folder contains the current template-shaped documentation.
- `views/` contains the current payment PlantUML views.
- No implementation, automated tests, Docker, or runtime is included.

**Folder convention (handbook §3.1):** [ArchiMate-daily-transaction-banking.md](../Archimate/ArchiMate-daily-transaction-banking.md) shows one product’s copy path. Replace the slug to match this initiative.

## Copy

```
templates/  →  docs/architecture/<initiative-id>-<product-slug>/
```

Examples: `docs/architecture/DTB-042-daily-transaction-banking/`, `docs/architecture/LND-042-digital-lending/`.

1. Fill [00-index.md](00-index.md) first (initiative ID, product, owners, version, **name-identity list**).
2. Fill each view using those names. Missing views are explicit **N/A** with owner sign-off — not omitted.
3. Use [20-appendix.md](20-appendix.md) for acronyms. Add initiative-only terms there; do not redefine them on every view.

## Pack split

| Pack | Files | Owner |
| --- | --- | --- |
| Cover / governance | `00-index.md`, `adr/`, `18`, `19`, `20` | EA **A**, SA **R** on index |
| Business (ArchiMate) | `01`–`04` | EA / BA |
| Solution (C4) | `05` Context L1, `06` Container L2, `07` Deployment | SA (Ops **R** on `07`) |
| Architecture (ArchiMate app/tech) | `08` Application Cooperation, `13` Technology, `14` Layered realization | SA / EA |
| Design (C4 L3 + UML) | `09`–`12` | Dev **R**, SA **A** on L3 and sequence |
| Governance / implementation | `15` Risk, `16` Migration, `17` NFR | Sec / EA / SA |

**`07` vs `13`:** C4 Deployment (`07`) is runtime topology (nodes, networks, regions). ArchiMate Technology (`13`) is logical nodes, environments, and middleware. One language per file.

## Rename and copy

| Template | How to use |
| --- | --- |
| [09-c4-component.md](09-c4-component.md) | Copy to `09-c4-component-<container>.md` (one touched container). |
| [11-uml-sequence.md](11-uml-sequence.md) | Copy once per critical-path use case to `11-uml-sequence-<use-case>.md`. |
| [adr/ADR-template.md](adr/ADR-template.md) | Copy to `adr/ADR-NNN-short-title.md`. Numbering: [adr/README.md](adr/README.md). |

## Rules

- One language per diagram (ArchiMate relationships vs C4 protocol labels vs UML messages).
- Name identity: ArchiMate Application Component = C4 Container = UML participant = test SUT. List the strings once on [00-index.md](00-index.md).
- Do not fork names across views (e.g. one `Channel` box vs several channel containers).
- Paste the diagram header on every view.
- Product facts, NFRs, and closed names for a **course sample** (Daily Transaction Banking) live in [20-appendix.md](20-appendix.md) §5 — copy them into `00-index` only when that is the product.
