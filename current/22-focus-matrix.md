# 22 - Lab 7 Focus Matrix

**Initiative:** PAY-001 - Online Payment Processing Gateway  
**Status:** Draft  
**RACI:** R EA, A Owner, C SA/BA/DA/Sec/Dev/Test/Ops, I all consumers

| | ArchiMate - landscape | C4 - bridge | UML - deployable behavior |
|---|---|---|---|
| Focus | Why, who, capability, layer | Which system, container, component | How it behaves; exact types |
| Zoom | Enterprise | Solution L1-L2 and one-container L3 | Delivery |
| Audience | EA, Owner, Risk, BA | SA, DA, Security; Dev on L3 | Dev, Test, Ops |
| Pack | Architecture | Architecture owns L1-L2; Design owns L3 | Design |
| PAY-001 artifacts | Motivation, Strategy, Business Process, Technology | Context, Container, Application Cooperation | Domain Class, Sequence, Activity, State |
| Fail if | JDBC or pods appear on Motivation / Process | Internals appear on Context; L1/L2/L3 are mixed | Lifelines are not C4 names; several objects share one state machine |

## Language selection

| Question | Selected language | PAY-001 source |
|---|---|---|
| Why are we changing? Which capabilities? | ArchiMate | `01-motivation-strategy.archimate.md` |
| Who does the work? | ArchiMate | `02-business-process.archimate.md` |
| What systems exist and who uses them? | C4 Context | `05-c4-context.md` |
| How is the platform decomposed? | C4 Container | `06-c4-container.md` |
| What runs inside one container? | C4 Component | N/A; optional L3 omitted |
| How does one use case behave? | UML Sequence | `11-uml-sequence.md` |
| What states can Payment have? | UML State | `12-uml-activity-state.md` |
| Where does it run? | ArchiMate Technology | `13-technology-deployment.archimate.md` |

## Identity rule

ArchiMate Application Component = C4 Container = UML participant = test SUT. The authoritative names are listed once in `00-index.md`.
