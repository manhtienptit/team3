"""Hard rules are impossible, not documented (I-5, I-9, CON.*).

Every test ATTEMPTS the violation or proves the ordering the spec demands,
and asserts the runtime rejects it: exception raised, mock untouched, or
I-6 state unchanged.
"""

from .support import RuntimeTestCase, CARD
from payment_gateway.payment_orchestrator.state_machine_engine import (
    InvalidTransition)

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

    def test_fraud05_daily_cumulative_is_sum_not_count(self):
        """FRAUD-05 attempt-to-skip: five individually legal authorizes of
        200,000,000 VND on ONE card sum to the 1,000,000,000 VND daily
        limit — the sixth must be blocked. A count-based counter (bump +1
        per transaction) would let all six through; this test catches it."""
        same_card = CARD
        for i in range(5):
            status, body = self.authorize(amount=200_000_000,
                                          key=f"f05-{i}", card=dict(same_card))
            self.assertEqual(status, 201, body)
        # card velocity after 5 auths is 5 < 10, so only the SUM can block
        status, body = self.authorize(amount=200_000_000, key="f05-5",
                                      card=dict(same_card))
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "declined")
        self.assertEqual(body["fraud_rule"], "FRAUD-05")
        payment = self.rt.payment_store.load_payment(body["id"])
        self.assertEqual(payment.status.value, "declined")

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

    def test_i9_merchant_platform_cannot_call_acquirer_directly(self):
        """I-9 forbidden path attempted: Merchant Platform querying
        AcquirerHost directly. It holds NO handle to the acquirer (nothing
        wires one), and the only surface it can call — the payment API —
        has no such route: the runtime itself rejects with 404 not_found
        and the acquirer stub records zero calls."""
        # structural: no handle exists on the Merchant Platform fake
        handles = [attr for attr in vars(self.rt.merchant_platform)
                   if "acq" in attr.lower()]
        self.assertEqual(handles, [])
        # the attempt, through the runtime surface the merchant can reach
        status, body = self.rt.handle(
            "POST", "/acquirer/authorize",
            {"amount": 500000, "transaction_ref": "forbidden"})
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")
        self.assertEqual(self.rt.acquirer_host.calls, [])  # mock untouched


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


class StateMachineEngineTests(RuntimeTestCase):
    """D6: every Payment transition goes through the State Machine Engine,
    and the engine rejects invalid ones against the payment's ACTUAL state
    (Payment.mark_* ops are engine-private; nothing mutates around it)."""

    def test_engine_rejects_invalid_transition_attempts(self):
        payment_id, _, _ = self.authorized_payment()
        payment = self.rt.payment_store.load_payment(payment_id)
        engine = self.rt.request_handler.state_machine

        with self.assertRaises(InvalidTransition):  # Authorized->Declined not I-6
            engine.to_declined(payment, "fraud_rule")
        with self.assertRaises(InvalidTransition):  # refund commit needs Captured
            engine.commit_refund(payment, 100000)
        self.assertEqual(payment.status.value, "authorized")  # unchanged

        status, _ = self.capture(payment_id, amount=500000)
        self.assertEqual(status, 200)
        with self.assertRaises(InvalidTransition):  # capture commit needs Authorized
            engine.commit_capture(payment, 100000, 0)
        self.assertEqual(payment.status.value, "captured")


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
