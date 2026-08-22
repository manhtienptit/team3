# Spec-trace — I-11 slice (in-scope path → OpenAPI operation → test id)

Every route, handler, package, and behaviour of the runtime appears on exactly one row below; anything not on a row is N/A (§4) and is not built. Test ids are `Class.method` in `tests/`; run everything with `python -m unittest discover -s tests -t .`

## 1. I-11 use cases → runtime → OpenAPI → tests

Use-case and `alt` strings are copied verbatim from Lab 1 I-11.

| # | In-scope path | OpenAPI operation | Test id |
|---|---|---|---|
| 1 | **Authorize Payment** — happy path (… Fraud pass → AcquirerHost approve → Persist Authorized → Webhook Service) | `authorizePayment` 201 | `AuthorizePaymentTests.test_authorize_happy_path_authorized` |
| 2 | Authorize Payment — `alt: Fraud blocks → Declined (no acquirer call)` (named alt) | `authorizePayment` 200 declined | `AuthorizePaymentTests.test_authorize_alt_fraud_block_declined_no_acquirer_call` |
| 3 | Authorize Payment — Direct Charge variant (`capture:true`, I-6 #2, Lab 10 §1 alt) | `authorizePayment` 200 captured | `AuthorizePaymentTests.test_authorize_direct_charge_captured` |
| 4 | Authorize Payment — Idempotency Duplicate (CON.2, Lab 10 §1 alt) | `authorizePayment` replay | `AuthorizePaymentTests.test_authorize_duplicate_key_replays_cached_response` |
| 5 | Authorize Payment — Concurrent Same Key (CON.2, Lab 10 §1 alt) | `authorizePayment` 409 | `AuthorizePaymentTests.test_authorize_concurrent_same_key_conflict_409` |
| 6 | Authorize Payment — Issuer Decline (I-6 #4, Lab 10 §1 alt) | `authorizePayment` 200 declined | `AuthorizePaymentTests.test_authorize_issuer_decline` |
| 7 | Authorize Payment — envelope checks CON.1 amount / Luhn / CON.2 key | `authorizePayment` 400 | `ConstraintTests.test_con1_amount_below_minimum_400`, `…above_maximum_400`, `…invalid_card_luhn_400`, `test_con2_missing_idempotency_key_400`, `…over_64_chars_400` |
| 8 | **Capture Payment** — happy path (Validate Authorized + not expired → acquirer capture → Persist Captured) | `capturePayment` 200 | `CapturePaymentTests.test_capture_happy_path_captured` |
| 9 | Capture Payment — `alt: Auth expired → 409 authorization_expired` (named alt) | `capturePayment` 409 | `CapturePaymentTests.test_capture_alt_authorization_expired_409_no_acquirer_call` |
| 10 | Capture Payment — Amount Exceeds Authorized (Lab 10 §2 alt) | `capturePayment` 400 | `CapturePaymentTests.test_capture_amount_exceeds_authorized_400` |
| 11 | Capture Payment — Invalid State (Lab 10 §2 alt) | `capturePayment` 409 | `CapturePaymentTests.test_capture_invalid_state_transition_409` |
| 12 | Capture Payment — Partial Capture → void remainder (Lab 10 §2 alt) | `capturePayment` 200 | `CapturePaymentTests.test_capture_partial_capture_voids_remainder` |
| 13 | Capture Payment — unknown id | `capturePayment` 404 | `CapturePaymentTests.test_capture_unknown_payment_404` |
| 14 | **Refund Payment** — happy path (Validate Captured + amount ≤ remaining + count < 10 + ≤ 180d → acquirer refund → Persist) | `refundPayment` 200 captured | `RefundPaymentTests.test_refund_partial_stays_captured` |
| 15 | Refund Payment — Full Refund → Refunded (I-6 #9, Lab 10 §3 alt) | `refundPayment` 200 refunded | `RefundPaymentTests.test_refund_full_refund_terminal_state` |
| 16 | Refund Payment — `alt: Max refunds exceeded → 400 max_refunds_exceeded` (named alt) | `refundPayment` 400 | `RefundPaymentTests.test_refund_alt_max_refunds_exceeded_400_no_acquirer_call` |
| 17 | Refund Payment — Amount Exceeds Refundable (Lab 10 §3 alt) | `refundPayment` 400 | `RefundPaymentTests.test_refund_amount_exceeds_refundable_400` |
| 18 | Refund Payment — Refund Window Expired (Lab 10 §3 alt) | `refundPayment` 409 | `RefundPaymentTests.test_refund_window_expired_409` |
| 19 | Refund Payment — Invalid State (Lab 10 §3 alt) | `refundPayment` 409 | `RefundPaymentTests.test_refund_invalid_state_transition_409` |
| 20 | Refund Payment — unknown id | `refundPayment` 404 | `RefundPaymentTests.test_refund_unknown_payment_404` |
| 21 | Webhook delivery — async hop of every happy path (sign + deliver + record) | `receiveWebhook` (POST /webhooks) | `WebhookDeliveryTests.test_webhook_signed_hmac_and_delivered`, `…retries_then_delivers`, `…failed_delivery_after_7_attempts` |
| 22 | Route guard — Void Payment / Payment Query and any unrouted path | *(no operation — guard by design)* | `ConstraintTests.test_no_out_of_scope_path_is_callable` |
| 23 | G4 drift gate — OpenAPI ↔ runtime, both directions, all operations | all | `OpenApiContractTests.test_document_has_exactly_the_in_scope_paths`, `…test_runtime_matches_openapi_both_directions`, `…test_webhook_delivery_matches_webhook_event_schema` |

## 2. G5 — exception spec for each I-11 named `alt` (trigger + compensating action + who)

| Named `alt` (Lab 1 string) | Trigger | Compensating action | Who performs it | Runtime proof (test) |
|---|---|---|---|---|
| `Fraud blocks → Declined (no acquirer call)` | any fraud rule FRAUD-01→05 blocks (Lab 3 §5, CON.3) | Payment persisted **Declined** (with fraud_rule) and **no acquirer call is made**; `payment.declined` published | Fraud Gate (Payment Orchestrator) | asserts persisted state `declined` **and** `acquirer_host.calls == []` |
| `Auth expired → 409 authorization_expired` | `expiresAt ≤ now` (CON.4) | capture rejected 409, **no acquirer capture call**, I-6 state unchanged (still Authorized) | State Machine Engine (Payment Orchestrator) | asserts 409 **and** zero capture calls **and** state still `authorized` |
| `Max refunds exceeded → 400 max_refunds_exceeded` | `refundCount ≥ 10` (CON.5) | refund rejected 400, **no acquirer refund call**, refundedAmount / refundCount / status unchanged | State Machine Engine (Payment Orchestrator) | asserts 400 **and** refund-call count flat **and** amounts/status unchanged |

Lab 3 §5 row **CON.6 (acquirer timeout → Failed)** is N/A on this slice: the AcquirerHost stub responds instantly, the alt is not named in I-11, and CON.6's 30s + 1 retry stay labels on the in-scope sync call (name-map §4).

## 3. G6 — in-scope rows of the Lab 3 §6 test spec

| # | Transition (Lab 3 §6) | SUT | Test id | Status |
|---|---|---|---|---|
| 1 | Pending → Authorized | Payment Orchestrator | `test_authorize_happy_path_authorized` | in-scope |
| 2 | Pending → Captured (Direct Charge) | Payment Orchestrator | `test_authorize_direct_charge_captured` | in-scope |
| 3 | Pending → Declined (fraud `alt`) | Payment Orchestrator | `test_authorize_alt_fraud_block_declined_no_acquirer_call` | in-scope |
| 4 | Pending → Declined (issuer declines) | Payment Orchestrator | `test_authorize_issuer_decline` | in-scope (acquirer contract returns approve **or** decline on the authorize path) |
| 5 | Pending → Failed (timeout, CON.6) | Payment Orchestrator | — | **N/A** — stub never times out; not an I-11 named alt; CON.6 labels kept (name-map §4) |
| 6 | Authorized → Captured | Payment Orchestrator | `test_capture_happy_path_captured` | in-scope |
| 7 | Authorized → Voided | Payment Orchestrator | — | **N/A** — Void is not an I-11 use case (no route); the void *call* appears only inside the Partial Capture alt (row 12) |
| 8 | Authorized → Failed (7d expiry job) | Expiry Job | — | **N/A** — Expiry Job not built; CON.4 enforced where I-11 needs it (named alt, §2) |
| 9 | Captured → Refunded | Payment Orchestrator | `test_refund_full_refund_terminal_state` | in-scope |
| 10 | Captured → Captured (partial, refundedAmount updated) | Payment Orchestrator | `test_refund_partial_stays_captured` | in-scope |

SUT names are I-4 strings; the Lab 10 §5 participant = SUT map is realized as: Payment Orchestrator → `payment_orchestrator/` package (its 8 modules), Expiry Job → not built (N/A above).

## 4. Lab 3 §4 contract register → where each row is realized

| Register row | Realized as |
|---|---|
| API Gateway → Payment Orchestrator, sync, forward validated request | `APIGateway.handle` → `RequestHandler` (in-process call, collapsed — name-map §2) |
| Payment Orchestrator → Idempotency Store, sync, GET/SET/BLPOP key | `IdempotencyManager` ↔ `stores.IdempotencyStore` |
| Payment Orchestrator → AcquirerHost, sync, authorize / capture / void / refund | `AcquirerClient` ↔ `mocks.AcquirerHostStub` (void only inside the Partial Capture alt) |
| Payment Orchestrator → Message Queue, async, publish `payment.*` | `EventPublisher` → `stores.MessageQueue.publish` |
| Message Queue → Webhook Service, async, consume `payment.*` | `MessageQueue.subscribe(WebhookService.on_event)`, drained by `runtime.drain_webhooks()` |
| Webhook Service → Merchant Platform, async, POST webhook (HMAC-SHA256) | `WebhookService` → `mocks.MerchantPlatformFake`; contract published as OpenAPI `receiveWebhook` (POST /webhooks) |

## 5. Hard-rule proofs (I-5 / I-9) — attempted, then rejected

| Rule | The test attempts… | …and asserts the runtime rejects it | Test id |
|---|---|---|---|
| I-5: idempotency check NEVER after fraud / acquirer call | observes the Authorize happy-path order; re-sends a used key with a fraud-triggering body | order log `idempotency_check → fraud_evaluate → acquirer_call`; cached replay with exactly 1 fraud evaluation and 0 acquirer calls | `I5HardRuleTests.test_i5_idempotency_check_precedes_fraud_and_acquirer`, `…test_i5_duplicate_key_attempt_to_skip_idempotency` |
| FRAUD-05: daily cumulative is a SUM of amounts (CON.8 / ASSUMPTION) | five individually legal 200M-VND authorizes on one card (1B total), then a sixth | sixth is blocked `FRAUD-05` and persisted Declined — a count-based counter would have let it through | `I5HardRuleTests.test_fraud05_daily_cumulative_is_sum_not_count` |
| I-6: every transition goes through the State Machine Engine (D6) | calls engine transitions against a payment in the wrong state (`to_declined` on Authorized, `commit_refund` on Authorized, `commit_capture` on Captured) | `InvalidTransition` each time; I-6 state unchanged; `Payment.mark_*` are engine-private | `StateMachineEngineTests.test_engine_rejects_invalid_transition_attempts` |
| I-5 / CON.3: fraud NEVER on capture, void, refund | runs capture + refund after an authorize | fraud evaluation count unchanged | `I5HardRuleTests.test_i5_fraud_gate_never_on_capture_or_refund_paths` |
| I-5: webhook NEVER blocks the sync response | reads the API response before draining | response returned with the event still queued; zero deliveries until `drain()` | `I5HardRuleTests.test_i5_webhook_delivery_never_blocks_sync_response` |
| I-9 forbidden: Webhook Service writing Payment records | `payment_store.insert_payment(webhook_service, payment)` | `PermissionError` (only Persistence Manager may write Payment records) | `I9ForbiddenPathTests.test_i9_webhook_service_cannot_write_payment_records` |
| I-9 forbidden: Merchant Platform querying AcquirerHost | Merchant Platform holds **no acquirer handle** (nothing wires one); the attempt goes through the only surface it has — `handle("POST", "/acquirer/authorize", …)` | runtime rejects `404 not_found` (no such Lab 9 relationship, no route) and `acquirer_host.calls == []` | `I9ForbiddenPathTests.test_i9_merchant_platform_cannot_call_acquirer_directly` |
| I-5 (query never calls acquirer) | — | **N/A structurally**: no query route exists (row 22 guard); the fake holds no reference to the acquirer | — |
