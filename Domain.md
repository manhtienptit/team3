# Domain:
Online Payment Processing

## Online Payment Processing

**What it is.** This prototype's bounded context is an online payment gateway that processes credit/debit card transactions and digital wallet payments on behalf of merchants. "Payment processing" here means the real-time authorization, capture, and settlement of customer payments — not lending, issuing, acquiring infrastructure, or treasury.

**In / out boundary.** In: payment initiation (authorize), capture, void, refund, transaction status lifecycle, and merchant webhook notification. Out: anything that is not a real-time online payment transaction initiated by a merchant on behalf of a customer (see Out of scope).

**Actors and systems.** Merchant (initiator via API); Customer (cardholder/payer); Acquirer (merchant's bank that processes the transaction); Card Network (Visa/Mastercard routing); Issuing Bank (customer's bank that approves/declines); Webhook Delivery (async notification).

**Happy path.** Merchant submits a payment request → fraud rules pass → system routes to acquirer → acquirer forwards to card network → issuing bank authorizes → response propagates back → merchant receives authorization result → merchant captures when ready → settlement occurs.

**Reject / fail / edge cases.** Issuing bank declines (insufficient funds, stolen card, expired). Acquirer timeout — must not double-charge. Network errors between gateway and acquirer require idempotent retry. Partial capture and partial refund. 3DS authentication challenge interrupts the synchronous flow. Duplicate requests with same idempotency key must return original result.

**Why it matters for modeling.** Context and container diagrams must show the gateway as orchestrator between merchant and the acquiring/network/issuing chain. Two-phase flow (authorize then capture) is distinct from one-phase (direct charge). Void and refund are separate post-authorization operations with different rules.

# Scope:
- Payment Authorization
- Payment Capture
- Void & Refund
- Transaction Status Lifecycle
- Webhook Notification

## Payment Authorization

**What it is.** A request to verify and reserve funds on the customer's payment method. No money moves yet — only a hold is placed on the cardholder's available balance at the issuing bank.

**In / out boundary.** In: merchant API call with payment details, fraud rule check, routing to acquirer, acquirer-to-network-to-issuer flow, authorization response (approved/declined), idempotency enforcement. Out: actual fund movement (that is Capture), recurring billing setup, 3DS enrollment (simplified out for this prototype).

**Actors and systems.** Merchant (caller); Gateway Orchestrator; Fraud Engine (rule-based); Acquirer; Card Network; Issuing Bank.

**Happy path.**

1. Merchant submits POST /payments with `capture: false` (or `capture: true` for direct charge).
2. Gateway validates request and checks idempotency key.
3. Fraud rules evaluate (velocity, amount threshold, geo).
4. Gateway routes to appropriate Acquirer.
5. Acquirer forwards to Card Network → Issuing Bank.
6. Issuing Bank approves, returns auth code.
7. Gateway persists transaction as `Authorized`.
8. Webhook fires `payment.authorized`.

**Reject / fail / edge cases.** Fraud rule block → `Declined` (no acquirer call). Issuer decline → `Declined` with reason code. Acquirer timeout → retry with same reference; if still fails, `Failed`. Invalid card → `Failed` before acquirer. Duplicate idempotency key → return existing result.

**Why it matters for modeling.** Authorization is the critical real-time path with the strictest latency requirement. It must be idempotent and must not proceed to acquirer if fraud rules block. The auth code from the issuer is required for subsequent capture/void.

## Payment Capture

**What it is.** Converting a previous authorization hold into an actual fund transfer. The merchant "captures" the authorized amount (full or partial) to initiate settlement.

**In / out boundary.** In: capture request referencing an existing authorized payment, full or partial amount, transition from `Authorized` to `Captured`, settlement queue. Out: authorization (already done), refund (separate operation post-capture).

**Actors and systems.** Merchant (caller); Gateway Orchestrator; Acquirer (receives capture instruction); Settlement Service (batches for clearing).

**Happy path.**

1. Merchant submits POST /payments/{id}/capture with optional amount (defaults to full auth amount).
2. Gateway validates: payment exists, status is `Authorized`, capture amount ≤ authorized amount.
3. Gateway sends capture to Acquirer.
4. Acquirer confirms capture.
5. Payment status → `Captured`.
6. Transaction queued for settlement.
7. Webhook fires `payment.captured`.

**Reject / fail / edge cases.** Payment not in `Authorized` status → reject. Capture amount exceeds auth amount → reject. Auth expired (issuer-defined window, typically 7 days) → capture may fail at acquirer. Partial capture: remaining auth amount may be voided or left to expire. Acquirer timeout on capture → retry; payment stays `Authorized` until confirmed.

**Why it matters for modeling.** Capture is less latency-sensitive than auth but must be reliable. Partial capture introduces amount tracking (captured vs remaining). The auth-to-capture window is an external constraint from the issuer/network.

## Void & Refund

**What it is.** Two distinct reversal operations. **Void** cancels an authorization before capture (no money moved, release the hold). **Refund** returns money after capture (money already moved, push funds back).

**In / out boundary.** In: void of `Authorized` payments, full/partial refund of `Captured` payments, status transitions, acquirer communication. Out: chargeback (initiated by issuer, not merchant), dispute management.

**Actors and systems.** Merchant (caller); Gateway Orchestrator; Acquirer; Card Network (for refund processing); Issuing Bank (releases hold on void, credits on refund).

**Happy path (Void).**

1. Merchant submits POST /payments/{id}/void.
2. Gateway validates: payment is `Authorized`.
3. Void sent to Acquirer → Network → Issuer releases hold.
4. Payment status → `Voided`.
5. Webhook fires `payment.voided`.

**Happy path (Refund).**

1. Merchant submits POST /payments/{id}/refund with amount.
2. Gateway validates: payment is `Captured`, refund amount ≤ (captured - already refunded).
3. Refund sent to Acquirer.
4. Acquirer processes refund through network.
5. Payment status → `Refunded` (full) or remains `Captured` with refunded amount tracked (partial).
6. Webhook fires `payment.refunded`.

**Reject / fail / edge cases.** Void on already-captured payment → reject (use refund instead). Refund exceeding captured amount → reject. Multiple partial refunds allowed up to captured amount. Acquirer timeout on refund → retry; refund is idempotent per refund reference.

**Why it matters for modeling.** Void and refund have different preconditions (status gates) and different settlement implications. They are separate API operations, not one "cancel" endpoint. Partial refund requires tracking cumulative refunded amount.

## Transaction Status Lifecycle

**What it is.** The defined set of states a payment can be in, and the allowed transitions between them. This is the single source of truth for "what happened to this payment."

**In / out boundary.** In: status transitions driven by authorization, capture, void, refund outcomes. Out: settlement status (separate from payment status), dispute/chargeback status.

**Status set:**

| Status | Meaning |
|---|---|
| `Pending` | Request received, processing not started or in flight to acquirer |
| `Authorized` | Issuer approved; funds held but not captured |
| `Captured` | Funds captured; queued for settlement |
| `Voided` | Authorization cancelled before capture |
| `Refunded` | Full refund processed after capture |
| `Declined` | Issuer or fraud rules rejected |
| `Failed` | System error; no successful authorization |

**Why it matters for modeling.** State machine must be explicit. Invalid transitions (e.g., void a captured payment) must be rejected at the API level. Each transition maps to exactly one API operation.

## Webhook Notification

**What it is.** Asynchronous notification to the merchant when a payment status changes. The merchant registers a webhook URL; the gateway delivers event payloads with retry on failure.

**In / out boundary.** In: event generation on status change, delivery with exponential backoff retry, signature verification. Out: synchronous API response (that is the primary response), merchant pull-based polling (supported but separate from push).

**Actors and systems.** Gateway (event producer); Webhook Service (delivery with retry); Merchant endpoint (consumer).

**Happy path.**

1. Payment status changes (e.g., `Authorized`).
2. Event created: `{ event: "payment.authorized", data: {...} }`.
3. Webhook Service delivers POST to merchant URL with HMAC signature.
4. Merchant returns 2xx → delivery complete.

**Reject / fail / edge cases.** Merchant endpoint down → retry with exponential backoff (e.g., 1m, 5m, 30m, 2h, 24h). Max retries exhausted → event marked `failed_delivery`. Merchant must verify HMAC signature to prevent spoofing. Duplicate delivery possible (at-least-once); merchant must handle idempotently.

**Why it matters for modeling.** Webhook is asynchronous and decoupled from the payment processing path. It must not block authorization latency. Delivery reliability is its own concern with its own retry/failure model.

# Out of scope:
- Card Issuing
- Recurring Billing / Subscriptions
- Dispute & Chargeback Management
- 3D Secure Authentication
- Multi-currency / FX
- Physical POS / In-store Payments
- KYC / AML

Each item below is excluded from this prototype. Do not add it to context, sequence, or C4 diagrams unless the domain sketch is explicitly extended.

## Card Issuing

**What it is.** Creating and managing payment cards (virtual or physical) on behalf of customers.

**Why excluded.** Different bounded context — issuing is liability management, not transaction processing. The gateway processes payments on existing cards; it does not create them.

**Modeling pitfall.** Do not draw a card issuance flow or BIN management on the payment processing sequence.

## Recurring Billing / Subscriptions

**What it is.** Scheduled, automatic charges based on a billing plan (monthly, annual, usage-based).

**Why excluded.** Adds scheduling, plan management, dunning, and retry logic that is a separate domain. Individual charges from a subscription would use this gateway, but the subscription engine itself is out.

**Modeling pitfall.** Do not add a scheduler, billing plan entity, or "next charge date" to the payment model.

## Dispute & Chargeback Management

**What it is.** When a cardholder disputes a charge through their issuing bank, triggering a chargeback process with evidence submission and arbitration.

**Why excluded.** Chargeback is an issuer-initiated flow with different timelines (45-120 days), actors (issuer, network arbitration), and data (evidence documents). It is not a merchant-initiated payment operation.

**Modeling pitfall.** Do not add a `Disputed` or `Chargeback` status to the payment state machine. Do not draw the issuer as an actor initiating flows in this context.

## 3D Secure Authentication

**What it is.** Cardholder authentication (3DS 1.0/2.0) where the issuer challenges the customer to verify identity before approving.

**Why excluded.** Adds a redirect/challenge flow that interrupts the synchronous auth path, introduces ACS (Access Control Server), and changes the liability model. Significant complexity for a prototype.

**Modeling pitfall.** Do not add an authentication challenge step, ACS participant, or `AwaitingAuthentication` status.

## Multi-currency / FX

**What it is.** Processing payments in one currency and settling in another, with real-time FX rate conversion.

**Why excluded.** Adds FX provider integration, rate locking, conversion fees, and settlement complexity. This prototype assumes single-currency (e.g., VND or USD).

**Modeling pitfall.** Do not add FX conversion, `presentmentCurrency` vs `settlementCurrency`, or rate provider to sequences.

## Physical POS / In-store Payments

**What it is.** Card-present transactions via POS terminals, NFC tap, chip-and-PIN.

**Why excluded.** Different channel (terminal hardware), different security model (EMV chip vs card-not-present), different certification requirements (PCI PTS).

**Modeling pitfall.** Do not draw POS terminals or card-present flows. This gateway is online/card-not-present only.

## KYC / AML

**What it is.** Know Your Customer and Anti-Money Laundering compliance checks on merchants or customers.

**Why excluded.** KYC/AML is an onboarding and ongoing monitoring concern, not a per-transaction processing concern. Merchant onboarding is assumed complete before they call the gateway.

**Modeling pitfall.** Do not add identity verification, document upload, or compliance screening to the payment flow.

# Architecture implications:
- Two-phase payment: authorize then capture is distinct from direct charge (authorize + capture in one call)
- Fraud check is a gate before acquirer routing; must not add latency if it passes
- Idempotency required on all write operations, especially authorization (must not double-charge)
- Webhook is async, decoupled from payment path; at-least-once delivery with retry

## Two-phase payment flow

**What it is.** Authorization and capture are separate steps. Merchant can authorize (hold funds) and capture later (e.g., when goods ship). Alternatively, a direct charge combines both in one API call.

**In / out boundary.** In: separate authorize and capture API calls; direct charge as a convenience; the time window between auth and capture. Out: recurring scheduling, installment plans.

**Actors and systems.** Merchant (chooses one-phase or two-phase); Gateway Orchestrator; Acquirer (supports both models).

**Happy path.** Two-phase: authorize → (hours/days pass) → capture. One-phase: authorize + capture in single request.

**Reject / fail / edge cases.** Auth expires if not captured within issuer window (typically 7 days). Partial capture leaves remaining amount. Void is only valid before capture. After capture, only refund is available.

**Why it matters for modeling.** State machine must support both flows. API design must make capture optional (default behavior configurable). Diagrams must show the two-phase flow as the primary path with direct charge as a variant.

## Fraud check as a gate

**What it is.** Rule-based fraud detection that runs after request validation but before acquirer routing. It is a pass/fail gate — not a scoring service that returns a number for human review.

**In / out boundary.** In: velocity checks (transactions per time window), amount thresholds, geo-blocking, card BIN rules. Out: ML-based scoring, manual review queues, case management.

**Actors and systems.** Gateway Orchestrator (caller); Fraud Engine (rule evaluator); the decision is binary: pass or block.

**Happy path.** Rules pass → proceed to acquirer. Rules fail → `Declined` with reason `fraud_rule`, no acquirer call.

**Why it matters for modeling.** Fraud Engine is on the authorization path only. It must not appear on capture, void, or refund sequences. It must not add significant latency — rules are evaluated in-memory or cached.

## Idempotency on write operations

**What it is.** Every mutating API call carries an idempotency key. The same key produces the same result — no double-charge, no double-refund.

**In / out boundary.** In: idempotency key on authorize, capture, void, refund; deduplication at gateway level before acquirer. Out: read operations (GET) which are naturally idempotent.

**Why it matters for modeling.** Idempotency check must happen early (before fraud check, before acquirer call). Sequence diagrams must show the "duplicate detected → return cached result" alt path. The idempotency store is a cross-cutting concern.

## Webhook decoupled from payment path

**What it is.** Webhook notification is fired after the payment operation completes. It must never block or slow down the synchronous payment response to the merchant.

**In / out boundary.** In: event published to queue after status change; webhook service consumes and delivers. Out: synchronous response to merchant (that is the API response, not webhook).

**Why it matters for modeling.** Webhook Service is a separate container consuming from a message queue. It does not appear on the critical payment processing path. Diagrams must show the async boundary (queue/event) between payment processing and webhook delivery.
