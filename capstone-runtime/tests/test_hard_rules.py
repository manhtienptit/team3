"""Hard rules are impossible, not documented (I-5, I-9, CON.*).

Every test ATTEMPTS the violation or proves the ordering the spec demands,
and asserts the runtime rejects it: exception raised, mock untouched, or
I-6 state unchanged.
"""

from .support import RuntimeTestCase, CARD

WEBHOOK_FORBIDDEN = ("I-9 forbidden path: only Persistence Manager")


class I5HardRuleTests(RuntimeTestCase):

    def test_i5_idempotency_check_precedes_fraud_and_acquirer(self):
        """I-5: idempotency check NEVER after fraud evaluation or acquirer
        call — asserted on the order log of the Authorize happy path."""
        status, _ = self.authorize()
        self.assertEqual(status, 201)
        self.assertEqual(self.rt.request_handler.order_log,
                         ["idempotency_check", "fraud_evaluate",
                          "acquirer_call"])

    def test_i5_duplicate_key_attempt_to_skip_idempotency(self):
        """Attempt to skip the rule: re-send the SAME key with a body that
        would now trigger FRAUD-02. The runtime must answer from cache —
        fraud is not re-evaluated and no acquirer call is made."""
        self.authorize(amount=500000, key="skip-attempt")
        self.rt.acquirer_host.calls.clear()
        status, body = self.authorize(amount=250_000_000, key="skip-attempt")
        self.assertEqual(status, 201)  # cached original response replayed
        self.assertEqual(body["status"], "authorized")
        self.assertEqual(self.rt.acquirer_host.calls, [])
        self.assertEqual(self.rt.request_handler.fraud_gate.evaluations, 1)

    def test_fraud05_daily_cumulative_attempt_to_skip_by_splitting_amount(self):
        """Attempt to skip FRAUD-05 by splitting one large amount into
        several sub-threshold authorizations on the same card. The daily
        counter must accumulate by amount, not by count of transactions —
        the sixth authorization crosses the 1B VND/day limit and is
        blocked, even though every single call stays under FRAUD-02's
        high-value threshold."""
        card = self.fresh_card()
        for _ in range(5):
            status, _ = self.authorize(amount=190_000_000, card=card)
            self.assertEqual(status, 201)
        self.rt.acquirer_host.calls.clear()
        status, body = self.authorize(amount=190_000_000, card=card)
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "declined")
        self.assertEqual(body["fraud_rule"], "FRAUD-05")
        self.assertEqual(self.rt.acquirer_host.calls, [])

    def test_i5_fraud_gate_never_on_capture_or_refund_paths(self):
        """I-5 / CON.3: fraud module NEVER evaluates on capture/refund."""
        payment_id, _, _ = self.authorized_payment(amount=500000)
        evaluated_after_auth = self.rt.request_handler.fraud_gate.evaluations
        status, _ = self.capture(payment_id, amount=400000)
        self.assertEqual(status, 200)
        status, _ = self.refund(payment_id, amount=100000)
        self.assertEqual(status, 200)
        self.assertEqual(self.rt.request_handler.fraud_gate.evaluations,
                         evaluated_after_auth)

    def test_i5_webhook_delivery_never_blocks_sync_response(self):
        """I-5: webhook NEVER blocks the synchronous payment API response —
        the response returns with the event still queued; delivery happens
        only on drain()."""
        status, _ = self.authorize()
        self.assertEqual(status, 201)
        self.assertEqual(len(self.rt.message_queue.pending()), 1)
        self.assertEqual(self.rt.merchant_platform.deliveries, [])
        self.rt.drain_webhooks()
        self.assertEqual(len(self.rt.merchant_platform.deliveries), 1)


class I9ForbiddenPathTests(RuntimeTestCase):

    def test_i9_webhook_service_cannot_write_payment_records(self):
        """I-9 forbidden path attempted: Webhook Service writing a Payment
        record to Payment Store. PaymentStore rejects it."""
        payment_id, _, _ = self.authorized_payment()
        payment = self.rt.payment_store.load_payment(payment_id)
        with self.assertRaises(PermissionError) as raised:
            self.rt.payment_store.insert_payment(
                self.rt.webhook_service, payment)
        self.assertIn(WEBHOOK_FORBIDDEN, str(raised.exception))

    def test_i9_merchant_platform_has_no_route_to_acquirer(self):
        """I-9 forbidden path attempted: reach AcquirerHost through Merchant
        Platform. There is no Lab 9 relationship for this, so Merchant
        Platform holds no attribute or method that reaches it at all — a
        structural absence, not a guarded call that only raises."""
        self.assertFalse(hasattr(self.rt.merchant_platform, "acquirer"))
        self.assertFalse(hasattr(self.rt.merchant_platform, "acquirer_host"))
        with self.assertRaises(AttributeError):
            self.rt.merchant_platform.acquirer_host.authorize(
                "tx", 500000, dict(CARD))


class ConstraintTests(RuntimeTestCase):

    def test_con1_amount_below_minimum_400(self):
        status, body = self.authorize(amount=9_999)  # CON.1 min = 10,000
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_amount")

    def test_con1_amount_above_maximum_400(self):
        status, body = self.authorize(amount=500_000_001)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_amount")

    def test_con2_missing_idempotency_key_400(self):
        status, body = self.rt.handle("POST", "/v1/payments",
                                      {"amount": 500000, "card": dict(CARD)})
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_request")

    def test_con2_idempotency_key_over_64_chars_400(self):
        status, body = self.authorize(key="x" * 65)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_request")

    def test_con1_invalid_card_luhn_400(self):
        status, body = self.authorize(
            card={"number": "4111111111111112", "exp_month": 12,
                  "exp_year": 2030})
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_card")

    def test_no_out_of_scope_path_is_callable(self):
        """Void Payment and Payment Query are N/A (not I-11): no route
        exists — API Gateway answers 404 not_found."""
        payment_id, _, _ = self.authorized_payment()
        status, body = self.rt.handle(
            "POST", f"/v1/payments/{payment_id}/void",
            {"amount": 500000, "idempotency_key": "void-key"})
        self.assertEqual((status, body["error"]), (404, "not_found"))
        status, body = self.rt.handle("GET", f"/v1/payments/{payment_id}", {})
        self.assertEqual((status, body["error"]), (404, "not_found"))


class WebhookDeliveryTests(RuntimeTestCase):
    """CON.7 on the async hop of every I-11 happy path."""

    def test_webhook_signed_hmac_and_delivered(self):
        self.authorize()
        self.rt.drain_webhooks()
        delivery = self.rt.merchant_platform.deliveries[0]
        self.assertTrue(delivery["valid_signature"])
        event_row = self.rt.payment_store.webhook_events()[0]
        self.assertEqual(event_row["status"], "delivered")
        self.assertEqual(event_row["attempts"], 1)

    def test_webhook_retries_then_delivers(self):
        self.rt.merchant_platform.fail_first_n = 2
        self.authorize()
        self.rt.drain_webhooks()
        event_row = self.rt.payment_store.webhook_events()[0]
        self.assertEqual(event_row["status"], "delivered")
        self.assertEqual(event_row["attempts"], 3)  # 2 failed + 1 ok

    def test_webhook_failed_delivery_after_7_attempts(self):
        self.rt.merchant_platform.fail_first_n = 99
        self.authorize()
        self.rt.drain_webhooks()
        event_row = self.rt.payment_store.webhook_events()[0]
        self.assertEqual(event_row["status"], "failed_delivery")
        self.assertEqual(event_row["attempts"], 7)  # CON.7 max
