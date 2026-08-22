# Spec-trace — extended slice (in-scope path → OpenAPI operation → test id)

Every route, handler, package, and behaviour of the runtime appears on exactly one row below; anything not on a row is N/A (§4) and is not built. Test ids are `Class.method` in `tests/`; run everything with `python -m unittest discover -s tests -t .`

## 1. Use cases → runtime → OpenAPI → tests

Use-case and `alt` strings are copied verbatim from Lab 1 I-11 + extension spec.

### First-sitting I-11 (unchanged)

| # | In-scope path | OpenAPI operation | Test id |
|---|---|---|---|
| 1 | **Authorize Payment** — happy path (… Fraud pass → AcquirerHost approve → Persist Authorized → Webhook Service) | `authorizePayment` 201 | `AuthorizePaymentTests.test_authorize_happy_path_authorized` |
| 2 | Authorize Payment — `alt: Fraud blocks → Declined (no acquirer call)` (named alt) | `authorizePayment` 200 Declined | `AuthorizePaymentTests.test_authorize_alt_fraud_block_declined_no_acquirer_call` |
| 3 | Authorize Payment — Direct Charge variant (`capture:true`, I-6 #2, Lab 10 §1 alt) | `authorizePayment` 200 Captured | `AuthorizePaymentTests.test_authorize_direct_charge_captured` |
| 4 | Authorize Payment — Idempotency Duplicate (CON.2, Lab 10 §1 alt) | `authorizePayment` replay | `AuthorizePaymentTests.test_authorize_duplicate_key_replays_cached_response` |
| 5 | Authorize Payment — Concurrent Same Key (CON.2, Lab 10 §1 alt) | `authorizePayment` 409 | `AuthorizePaymentTests.test_authorize_concurrent_same_key_conflict_409` |
| 6 | Authorize Payment — Issuer Decline (I-6 #4, Lab 10 §1 alt) | `authorizePayment` 200 Declined | `AuthorizePaymentTests.test_authorize_issuer_decline` |
| 7 | Authorize Payment — envelope checks CON.1 amount / Luhn / CON.2 key | `authorizePayment` 400 | `ConstraintTests.test_con1_amount_below_minimum_400`, `…above_maximum_400`, `…invalid_card_luhn_400`, `test_con2_missing_idempotency_key_400`, `…over_64_chars_400` |
| 8 | **Capture Payment** — happy path (Validate Authorized + not expired → acquirer capture → Persist Captured) | `capturePayment` 200 | `CapturePaymentTests.test_capture_happy_path_captured` |
| 9 | Capture Payment — `alt: Auth expired → 409 authorization_expired` (named alt) | `capturePayment` 409 | `CapturePaymentTests.test_capture_alt_authorization_expired_409_no_acquirer_call` |
| 10 | Capture Payment — Amount Exceeds Authorized (Lab 10 §2 alt) | `capturePayment` 400 | `CapturePaymentTests.test_capture_amount_exceeds_authorized_400` |
| 11 | Capture Payment — Invalid State (Lab 10 §2 alt) | `capturePayment` 409 | `CapturePaymentTests.test_capture_invalid_state_transition_409` |
| 12 | Capture Payment — Partial Capture → void remainder (Lab 10 §2 alt) | `capturePayment` 200 | `CapturePaymentTests.test_capture_partial_capture_voids_remainder` |
| 13 | Capture Payment — unknown id | `capturePayment` 404 | `CapturePaymentTests.test_capture_unknown_payment_404` |
| 14 | **Refund Payment** — happy path (Validate Captured + amount ≤ remaining + count < 10 + ≤ 180d → acquirer refund → Persist) | `refundPayment` 200 Captured | `RefundPaymentTests.test_refund_partial_stays_captured` |
| 15 | Refund Payment — Full Refund → Refunded (I-6 #9, Lab 10 §3 alt) | `refundPayment` 200 Refunded | `RefundPaymentTests.test_refund_full_refund_terminal_state` |
| 16 | Refund Payment — `alt: Max refunds exceeded → 400 max_refunds_exceeded` (named alt) | `refundPayment` 400 | `RefundPaymentTests.test_refund_alt_max_refunds_exceeded_400_no_acquirer_call` |
| 17 | Refund Payment — Amount Exceeds Refundable (Lab 10 §3 alt) | `refundPayment` 400 | `RefundPaymentTests.test_refund_amount_exceeds_refundable_400` |
| 18 | Refund Payment — Refund Window Expired (Lab 10 §3 alt) | `refundPayment` 409 | `RefundPaymentTests.test_refund_window_expired_409` |
| 19 | Refund Payment — Invalid State (Lab 10 §3 alt) | `refundPayment` 409 | `RefundPaymentTests.test_refund_invalid_state_transition_409` |
| 20 | Refund Payment — unknown id | `refundPayment` 404 | `RefundPaymentTests.test_refund_unknown_payment_404` |
| 21 | Webhook delivery — async hop of every happy path (sign + deliver + record) | `receiveWebhook` (POST /webhooks) | `WebhookDeliveryTests.test_webhook_signed_hmac_and_delivered`, `…retries_then_delivers`, `…failed_delivery_after_7_attempts` |
| 22 | Route guard — out-of-scope paths (Tokenization, 3DS, etc.) | *(no operation — guard by design)* | `ConstraintTests.test_no_out_of_scope_path_is_callable` |
| 23 | G4 drift gate — OpenAPI ↔ runtime, both directions, all operations | all | `OpenApiContractTests.test_document_has_exactly_the_in_scope_paths`, `…test_runtime_matches_openapi_both_directions`, `…test_webhook_delivery_matches_webhook_event_schema` |

### Extension sitting — Slice A

| # | In-scope path | OpenAPI operation | Test id |
|---|---|---|---|
| 24 | **Void Payment** — happy path (Authorized → Voided, acquirer void, webhook async) | `voidPayment` 200 | `VoidPaymentTests.test_void_happy_path_voided` |
| 25 | Void Payment — alt: non-Authorized → 409 `invalid_state_transition` (no acquirer void, I-6 unchanged) | `voidPayment` 409 | `VoidPaymentTests.test_void_non_authorized_409` |
| 26 | Void Payment — unknown id | `voidPayment` 404 | `VoidPaymentTests.test_void_unknown_payment_404` |
| 27 | Void Payment — already voided (terminal) | `voidPayment` 409 | `VoidPaymentTests.test_void_already_voided_409` |
| 28 | **Payment Query** — happy path (GET → Query Store → card_ref last 4, no PAN) | `getPayment` 200 | `PaymentQueryTests.test_query_happy_path` |
| 29 | Payment Query — unknown id → 404 | `getPayment` 404 | `PaymentQueryTests.test_query_unknown_payment_404` |
| 30 | Payment Query — reflects state after capture | `getPayment` 200 | `PaymentQueryTests.test_query_after_capture_reflects_state` |
| 31 | Payment Query — reflects refund amounts | `getPayment` 200 | `PaymentQueryTests.test_query_after_refund_reflects_amounts` |
| 32 | **Expiry Job** — happy path (Authorized + expiresAt ≤ now → Failed, payment.failed published) | *(internal tick)* | `ExpiryJobTests.test_expiry_happy_path_authorized_to_failed` |
| 33 | Expiry Job — already-terminal not moved | *(internal tick)* | `ExpiryJobTests.test_expiry_already_terminal_not_moved` |
| 34 | Expiry Job — captured not expired | *(internal tick)* | `ExpiryJobTests.test_expiry_captured_not_moved` |
| 35 | Expiry Job — capture after expiry = 409 + row Failed | `capturePayment` 409 | `ExpiryJobTests.test_capture_after_expiry_still_409_and_row_is_failed` |
| 36 | Expiry Job — webhook delivered async | *(internal tick + drain)* | `ExpiryJobTests.test_expiry_webhook_delivered_async` |
| 37 | **CON.6 timeout** — acquirer exhausted → Pending → Failed (same ref, no dup charge) | `authorizePayment` 200 Failed | `CON6TimeoutTests.test_con6_timeout_authorize_pending_to_failed` |
| 38 | CON.6 — same transaction reference, 2 attempts | `authorizePayment` 200 Failed | `CON6TimeoutTests.test_con6_same_transaction_reference_no_duplicate` |
| 39 | CON.6 — retry succeeds on second attempt → Authorized | `authorizePayment` 201 | `CON6TimeoutTests.test_con6_retry_succeeds_on_second_attempt` |
| 40 | CON.6 — payment.failed event published | `authorizePayment` 200 Failed | `CON6TimeoutTests.test_con6_failed_event_published` |
| 41 | Void Payment — webhook event type `payment.voided` documented | `receiveWebhook` | `OpenApiContractTests.test_void_webhook_event_type_documented` |
| 42 | Rate limit 429 documented on all paths | all | `OpenApiContractTests.test_rate_limit_429_documented` |
| 43 | Payment Query — OpenAPI fields match | `getPayment` 200/404 | `OpenApiContractTests.test_query_matches_openapi` |

### Extension sitting — Slice B (Security)

| # | Property | Test id |
|---|---|---|
| S1 | Secrets not in source; runtime refuses to start without WEBHOOK_SECRET | `S1SecretsNotInSourceTests.test_s1_runtime_refuses_to_start_without_secret`, `…test_s1_no_hardcoded_default_in_source` |
| S2 | HMAC-SHA256 webhook — wrong signature rejected | `S2WebhookHMACTests.test_s2_wrong_signature_rejected` |
| S3 | PAN / card_ref — full PAN never in store, query, or webhook | `S3NoPANTests.test_s3_payment_store_row_has_no_full_pan`, `…test_s3_query_response_has_no_full_pan`, `…test_s3_webhook_payload_has_no_full_pan` |
| S4 | Payment Query never calls AcquirerHost / NAPAS Switch (I-5) | `S4QueryNeverCallsAcquirerTests.test_s4_get_while_stub_would_fail`, `…test_s4_unknown_query_no_acquirer_calls` |
| S5 | Fraud NEVER on void (I-5 / CON.3) | `S5FraudNeverOnVoidTests.test_s5_void_fraud_count_unchanged` |
| S6 | Webhook Service never writes Payment (I-9 / I-7) | `S6WebhookServiceCannotWritePaymentTests.test_s6_insert_payment_from_webhook_service_raises` |
| S7 | Merchant Platform never queries AcquirerHost (I-9) | `S7MerchantPlatformCannotCallAcquirerTests.test_s7_no_acquirer_attribute`, `…test_s7_no_method_reaching_acquirer` |
| S8 | Query Store never writes Payment (I-7) | `S8QueryStoreCannotWritePaymentTests.test_s8_query_store_insert_raises`, `…test_s8_query_store_update_raises`, `…test_s8_get_path_does_not_update_status` |
| S9 | Rate limiting — burst over cap → 429 | `S9RateLimitTests.test_s9_burst_over_cap_returns_429`, `…test_s9_different_merchant_not_throttled`, `…test_s9_window_expires_allows_again` |
| S10 | Idempotency before fraud and acquirer (I-5 / CON.2) | `S10IdempotencyBeforeFraudTests.test_s10_order_log_shows_idempotency_first` |
| S11 | CON.6 no duplicate charge — same ref, Payment Failed | `S11CON6NoDuplicateChargeTests.test_s11_timeout_same_ref_payment_failed` |

## 2. G5 — exception spec for each named `alt` (trigger + compensating action + who)

| Named `alt` (Lab 1 string) | Trigger | Compensating action | Who performs it | Runtime proof (test) |
|---|---|---|---|---|
| `Fraud blocks → Declined (no acquirer call)` | any fraud rule FRAUD-01→05 blocks (Lab 3 §5, CON.3) | Payment persisted **Declined** (with fraud_rule) and **no acquirer call is made**; `payment.declined` published | Fraud Gate (Payment Orchestrator) | asserts persisted state `declined` **and** `acquirer_host.calls == []` |
| `Auth expired → 409 authorization_expired` | `expiresAt ≤ now` (CON.4) | capture rejected 409, **no acquirer capture call**, I-6 state unchanged (still Authorized) | State Machine Engine (Payment Orchestrator) | asserts 409 **and** zero capture calls **and** state still `authorized` |
| `Max refunds exceeded → 400 max_refunds_exceeded` | `refundCount ≥ 10` (CON.5) | refund rejected 400, **no acquirer refund call**, refundedAmount / refundCount / status unchanged | State Machine Engine (Payment Orchestrator) | asserts 400 **and** refund-call count flat **and** amounts/status unchanged |
| Void of non-Authorized → 409 `invalid_state_transition` | `status ≠ authorized` | void rejected 409, **no acquirer void call**, I-6 state unchanged | State Machine Engine (Payment Orchestrator) | asserts 409 **and** zero void calls (from this point) **and** status unchanged |
| CON.6 acquirer timeout → Pending → Failed | acquirer does not respond after 30s + 1 retry (both exhausted) | Payment persisted **Failed** (same transaction reference, no duplicate charge); `payment.failed` published | Acquirer Client (Payment Orchestrator) | asserts `failed` **and** all authorize calls share one ref **and** exactly 2 attempts |
| Expiry Job: Authorized → Failed | `expiresAt ≤ now` on tick (CON.4, hourly) | Payment row moved to **Failed**; `payment.failed` published; capture after expiry → 409 | Expiry Job | asserts `failed` **and** `payment.failed` event **and** subsequent capture = 409 |

## 3. G6 — in-scope rows of the Lab 3 §6 test spec

| # | Transition (Lab 3 §6) | SUT | Test id | Status |
|---|---|---|---|---|
| 1 | Pending → Authorized | Payment Orchestrator | `test_authorize_happy_path_authorized` | in-scope |
| 2 | Pending → Captured (Direct Charge) | Payment Orchestrator | `test_authorize_direct_charge_captured` | in-scope |
| 3 | Pending → Declined (fraud `alt`) | Payment Orchestrator | `test_authorize_alt_fraud_block_declined_no_acquirer_call` | in-scope |
| 4 | Pending → Declined (issuer declines) | Payment Orchestrator | `test_authorize_issuer_decline` | in-scope |
| 5 | Pending → Failed (timeout, CON.6) | Payment Orchestrator | `test_con6_timeout_authorize_pending_to_failed` | **in-scope (extension)** |
| 6 | Authorized → Captured | Payment Orchestrator | `test_capture_happy_path_captured` | in-scope |
| 7 | Authorized → Voided | Payment Orchestrator | `test_void_happy_path_voided` | **in-scope (extension)** |
| 8 | Authorized → Failed (expiry job, CON.4) | Expiry Job | `test_expiry_happy_path_authorized_to_failed` | **in-scope (extension)** |
| 9 | Captured → Refunded | Payment Orchestrator | `test_refund_full_refund_terminal_state` | in-scope |
| 10 | Captured → Captured (partial, refundedAmount updated) | Payment Orchestrator | `test_refund_partial_stays_captured` | in-scope |

SUT names are I-4 strings; the Lab 10 §5 participant = SUT map is realized as: Payment Orchestrator → `payment_orchestrator/` package (its 8 modules), Expiry Job → `expiry_job.ExpiryJob`.

## 4. Lab 3 §4 contract register → where each row is realized

| Register row | Realized as |
|---|---|
| API Gateway → Payment Orchestrator, sync, forward validated request | `APIGateway.handle` → `RequestHandler` (in-process call, collapsed — name-map §2) |
| API Gateway → Query Store, sync, GET payment (Lab 9 rel 3) | `APIGateway._query` → `QueryStore.get` (in-process call) |
| Payment Orchestrator → Idempotency Store, sync, GET/SET/BLPOP key | `IdempotencyManager` ↔ `stores.IdempotencyStore` |
| Payment Orchestrator → AcquirerHost, sync, authorize / capture / void / refund (CON.6 retry) | `AcquirerClient` ↔ `mocks.AcquirerHostStub` |
| Payment Orchestrator → Message Queue, async, publish `payment.*` | `EventPublisher` → `stores.MessageQueue.publish` |
| Message Queue → Webhook Service, async, consume `payment.*` | `MessageQueue.subscribe(WebhookService.on_event)`, drained by `runtime.drain_webhooks()` |
| Webhook Service → Merchant Platform, async, POST webhook (HMAC-SHA256) | `WebhookService` → `mocks.MerchantPlatformFake`; contract published as OpenAPI `receiveWebhook` (POST /webhooks) |
| Expiry Job → Payment Store, sync, update expired rows (Lab 9 rel 10) | `ExpiryJob.tick` → `PaymentStore.update_payment_by_expiry_job` |
| Expiry Job → Message Queue, async, publish `payment.failed` (Lab 9 rel 11) | `ExpiryJob.tick` → `MessageQueue.publish` |

## 5. Hard-rule proofs (I-5 / I-9) — attempted, then rejected

| Rule | The test attempts… | …and asserts the runtime rejects it | Test id |
|---|---|---|---|
| I-5: idempotency check NEVER after fraud / acquirer call | observes the Authorize happy-path order; re-sends a used key with a fraud-triggering body | order log `idempotency_check → fraud_evaluate → acquirer_call`; cached replay with exactly 1 fraud evaluation and 0 acquirer calls | `I5HardRuleTests.test_i5_idempotency_check_precedes_fraud_and_acquirer`, `…test_i5_duplicate_key_attempt_to_skip_idempotency` |
| I-5: FRAUD-05 daily cumulative cannot be bypassed by splitting | 6 sub-threshold authorizations on the same card cross the daily limit | 6th authorization blocked (FRAUD-05), no acquirer call | `I5HardRuleTests.test_fraud05_daily_cumulative_attempt_to_skip_by_splitting_amount` |
| I-5 / CON.3: fraud NEVER on capture, void, refund | runs capture + refund + void after an authorize | fraud evaluation count unchanged | `I5HardRuleTests.test_i5_fraud_gate_never_on_capture_or_refund_paths`, `S5FraudNeverOnVoidTests.test_s5_void_fraud_count_unchanged` |
| I-5: webhook NEVER blocks the sync response | reads the API response before draining | response returned with the event still queued; zero deliveries until `drain()` | `I5HardRuleTests.test_i5_webhook_delivery_never_blocks_sync_response` |
| I-5: Payment Query NEVER calls AcquirerHost | GET while stub set to timeout | GET returns 200/404; `acquirer_host.calls` unchanged | `S4QueryNeverCallsAcquirerTests.test_s4_get_while_stub_would_fail`, `…test_s4_unknown_query_no_acquirer_calls` |
| I-9 forbidden: Webhook Service writing Payment records | `payment_store.insert_payment(webhook_service, payment)` | `PermissionError` | `I9ForbiddenPathTests.test_i9_webhook_service_cannot_write_payment_records`, `S6…test_s6_insert_payment_from_webhook_service_raises` |
| I-9 forbidden: Merchant Platform querying AcquirerHost | Access missing attribute | `AttributeError` (structural absence — no reference to acquirer exists) | `I9ForbiddenPathTests.test_i9_merchant_platform_has_no_route_to_acquirer`, `S7…test_s7_no_acquirer_attribute`, `…test_s7_no_method_reaching_acquirer` |
| I-7 forbidden: Query Store writing Payment records | `payment_store.insert_payment(query_store, payment)` | `PermissionError` | `S8QueryStoreCannotWritePaymentTests.test_s8_query_store_insert_raises`, `…test_s8_query_store_update_raises` |
| S1: secrets not in source | runtime starts without WEBHOOK_SECRET | `RuntimeError` — refuses to start | `S1SecretsNotInSourceTests.test_s1_runtime_refuses_to_start_without_secret` |
| S2: wrong HMAC rejected | deliver with wrong signing secret | event recorded `failed_delivery`; no accepted delivery | `S2WebhookHMACTests.test_s2_wrong_signature_rejected` |
| S3: no full PAN | inspect Payment Store row, Query response, webhook payload | card_ref = 4 chars; no 12+ digit string anywhere | `S3NoPANTests.*` |
| S9: rate limiting | burst 101 requests from one merchant | 101st → 429 `rate_limit_exceeded` | `S9RateLimitTests.test_s9_burst_over_cap_returns_429` |
| S11: CON.6 no duplicate charge | timeout both attempts; inspect refs | all authorize calls share one transaction ref; Payment = Failed | `S11CON6NoDuplicateChargeTests.test_s11_timeout_same_ref_payment_failed` |


## 6. Agent contract — attempt tests (AGENTS.md)

Spec: `AGENTS.md`. Fixtures: `tests/fixtures/agent/violations.py`. Checker: `tests/test_agent_contract.py`.

| # | Property | Attempt | Reject | Test id |
|---|----------|---------|--------|---------|
| A1 | No invented use case (N1) | POST /v1/3dsecure, /tokenize | 404 not_found; OpenAPI has no such path | `A1NoInventedUseCaseTests.test_a1_3dsecure_route_rejected`, `…test_a1_tokenize_route_rejected`, `…test_a1_openapi_has_no_out_of_scope_operations` |
| A2 | Title Case on the wire (M2) | Authorize, void, CON.6, query responses; OpenAPI enums | All return Title Case status; no lowercase enum | `A2TitleCaseOnWireTests.test_a2_authorize_returns_title_case`, `…test_a2_void_returns_title_case`, `…test_a2_con6_failed_returns_title_case`, `…test_a2_query_returns_title_case`, `…test_a2_openapi_enums_are_title_case` |
| A3 | No secret default (M7/S1) | Grep source; start with empty secret | No `simulated-webhook-secret` in source; RuntimeError on empty | `A3NoSecretDefaultTests.test_a3_no_hardcoded_secret_default`, `…test_a3_runtime_refuses_without_secret` |
| A4 | No pack edit (N4) | Check for .py in Lb/ or Lb/before/ | No runtime files in packs | `A4NoPackEditTests.test_a4_no_runtime_files_in_packs` |
| A5 | Expiry Job = Scheduler (M12) | Read name-map + README | Both say Scheduler, not Worker Tier | `A5ExpiryJobSchedulerTests.test_a5_name_map_says_scheduler`, `…test_a5_readme_says_scheduler_for_expiry` |
| A6 | Query Store read-only (N9/M5) | insert_payment / update_payment from query_store | PermissionError | `A6QueryStoreReadOnlyTests.test_a6_query_store_insert_rejected`, `…test_a6_query_store_update_rejected` |
| A7 | Spec-trace required (M10/N10) | Check all OpenAPI ops in spec-trace; attempt untraced route | All ops traced; untraced route → 404 | `A7SpecTraceRequiredTests.test_a7_all_openapi_operations_on_spec_trace`, `…test_a7_untraced_route_returns_404` |
| A8 | I-3 stay mocked (N6) | Grep source for https:// host URLs | No real host in payment_gateway/ | `A8I3MockedTests.test_a8_no_https_acquirer_in_source` |
| A9 | Leftover Title Case labels | spec-trace + README for lowercase 200 labels | No lowercase status labels | `A9LeftoverTitleCaseTests.test_a9_spec_trace_no_lowercase_status_labels`, `…test_a9_readme_demo_title_case` |
| A10 | Human A (SA signed) | README SA ☑ + AGENTS.md exists | SA acceptance present; AGENTS.md with MUST/MUST NOT | `A10HumanATests.test_a10_readme_has_sa_acceptance`, `…test_a10_agents_md_exists` |
