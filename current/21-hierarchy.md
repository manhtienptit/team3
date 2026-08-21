# 21 - Lab 7 Hierarchy

**Initiative:** PAY-001 - Online Payment Processing Gateway  
**Status:** Draft  
**RACI:** R EA, A Owner, C SA/BA/DA/Sec/Dev/Test/Ops, I all consumers

## Adoption record

Team 3 adopts the Lab 7 Guide in `lab7/list.md` as written. ArchiMate aligns the enterprise, C4 aligns the build, and UML aligns behavior and tests. The upper level constrains the lower level; the lower level realizes the upper level.

## Three levels of design

| Level | Language | Focus | Readers | PAY-001 views |
|---|---|---|---|---|
| Top - enterprise | ArchiMate | Governance, strategy, process | EA, Owner, Risk, BA | `01`, `02` |
| Middle - solution | C4 plus ArchiMate Application / Technology | System boundary and runnable containers | SA, DA, Security | `05`, `06`, `08`, `13` |
| Base - delivery | UML plus one optional C4 Component | Messages, states, and exact types | Dev, Test, Ops | `10`, `11`, `12` |

## Nesting thread

`Payment lifecycle capability` -> `Online Payment Gateway` -> `Payment API`, `Payment Orchestrator`, `Payment Store`, `Query Store`, `Fraud Engine`, `Acquirer Connector`, `Webhook Event Queue`, and `Webhook Service` -> Payment messages and Payment states.

The optional C4 L3 drill-down is omitted. No second enterprise story or new external system is introduced at lower levels.

## Bridge

`ArchiMate enterprise` -> `C4 solution` -> `UML delivery` -> as-built feedback to SA -> landscape update.

## Binding rules

- ArchiMate is not used for protocol, container, or sequence grain.
- C4 Context contains no internals; C4 Container contains runnable units and sync/async labels.
- UML sequences use Merchant plus exact C4 container names.
- The UML state machine contains one object: `Payment`.
