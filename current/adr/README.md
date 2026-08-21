# Architecture Decision Records (ADR)

**Pack:** Cover / governance  
**Handbook:** §3.1  
**Glossary:** [../20-appendix.md](../20-appendix.md) (ADR)

The `adr/` folder is **always present**. An empty folder is not a substitute for N/A on a **required** decision — record that in [00-index.md](../00-index.md) N/A register.

## Numbering

Copy [ADR-template.md](ADR-template.md) to:

```
adr/ADR-NNN-short-title.md
```

| Item | Rule | Example |
| --- | --- | --- |
| Number | Three digits, sequential in this dossier | `001`, `002` |
| Title | Lowercase kebab-case, decision not topic | `shared-primary-store` |
| Status | Proposed / Accepted / Superseded / Deprecated | |

Do not check in a filled sample ADR unless that decision is actually taken.

## Index of ADRs

| ID | Title | Status | Date | Links to views |
| --- | --- | --- | --- | --- |
| | | | | |

## Rules

- One decision per file.
- Context / Decision / Consequences / alternatives required.
- Do not treat vendor, HA, or RPO/RTO as product fact unless this initiative owns that assumption.
