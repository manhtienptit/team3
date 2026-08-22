"""Extension sitting — Slice A: Void Payment, Payment Query, Expiry Job, CON.6.

Each new use case runs: happy path + named alt. G5 proof for CON.6 and
Expiry Job: compensating action actually happens (persisted Failed, same
transaction reference, no duplicate charge).
"""

from .support import RuntimeTestCase, T0

AUTH_WINDOW = 7 * 86400  # CON.4


# --------------------------------------------------------------------------
# Void Payment — POST /v1/payments/{id}/void
#   happy: Authorized -> Voided (acquirer void, webhook async)
#   alt: non-Authorized -> 409 invalid_state_transition
# --------------------------------------------------------------------------
class VoidPaymentTests(RuntimeTestCase):

    def test_void_happy_path_voided(self):
        """I-6: Authorized -> Voided. Acquirer void called, event published."""
        payment_id, _, _ = self.authorized_payment()
        status, body = self.void(payment_id)
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "Voided")
        self.assertEqual(body["id"], payment_id)
        payment = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(payment.status.value, "voided")
        self.assertEqual(self.acquirer_calls_of("void"),
                         [("void", payment_id, 500000)])
        events = self.rt.message_queue.pending()
        self.assertEqual(events[-1]["type"], "payment.voided")

    def test_void_non_authorized_409(self):
        """Alt: void of non-Authorized -> 409 invalid_state_transition;
        no acquirer void call; I-6 state unchanged."""
        payment_id, _ = self.captured_payment()
        void_calls_before = len(self.acquirer_calls_of("void"))
        status, body = self.void(payment_id)
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "invalid_state_transition")
        self.assertEqual(len(self.acquirer_calls_of("void")), void_calls_before)
        payment = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(payment.status.value, "captured")  # unchanged

    def test_void_unknown_payment_404(self):
        status, body = self.void("pay_99999999")
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "payment_not_found")

    def test_void_already_voided_409(self):
        """Double-void -> 409 (Voided is terminal, not Authorized)."""
        payment_id, _, _ = self.authorized_payment()
        self.void(payment_id)
        status, body = self.void(payment_id)
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "invalid_state_transition")


# --------------------------------------------------------------------------
# Payment Query — GET /v1/payments/{id}
#   happy: returns payment fields with card_ref (last 4), not full PAN
#   alt: unknown id -> 404
# --------------------------------------------------------------------------
class PaymentQueryTests(RuntimeTestCase):

    def test_query_happy_path(self):
        """GET returns current Payment fields without full PAN."""
        payment_id, _, _ = self.authorized_payment(amount=500000)
        status, body = self.query(payment_id)
        self.assertEqual(status, 200)
        self.assertEqual(body["id"], payment_id)
        self.assertEqual(body["status"], "Authorized")
        self.assertEqual(body["amount"], 500000)
        self.assertEqual(len(body["card_ref"]), 4)  # last 4 only
        self.assertNotIn("card", body)  # no full card object
        # S3: full PAN is not in the query response
        for value in body.values():
            if isinstance(value, str) and len(value) >= 12:
                self.assertFalse(value.isdigit(),
                                 "full PAN must not appear in query response")

    def test_query_unknown_payment_404(self):
        status, body = self.query("pay_99999999")
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "payment_not_found")

    def test_query_after_capture_reflects_state(self):
        """Query returns updated state after capture."""
        payment_id, _ = self.captured_payment(amount=500000)
        status, body = self.query(payment_id)
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "Captured")
        self.assertEqual(body["captured_amount"], 500000)

    def test_query_after_refund_reflects_amounts(self):
        payment_id, _ = self.captured_payment(amount=500000)
        self.refund(payment_id, amount=100000)
        status, body = self.query(payment_id)
        self.assertEqual(status, 200)
        self.assertEqual(body["refunded_amount"], 100000)
        self.assertEqual(body["refund_count"], 1)


# --------------------------------------------------------------------------
# Expiry Job — tick(now)
#   happy: Authorized + expiresAt <= now -> Failed
#   alt: already-terminal not moved; capture after expiry = 409 + row Failed
# --------------------------------------------------------------------------
class ExpiryJobTests(RuntimeTestCase):

    def test_expiry_happy_path_authorized_to_failed(self):
        """CON.4 / I-6 #8: expiresAt <= now -> Authorized -> Failed."""
        payment_id, _, _ = self.authorized_payment()
        self.now["t"] = T0 + AUTH_WINDOW + 1
        expired = self.rt.tick_expiry()
        self.assertIn(payment_id, expired)
        payment = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(payment.status.value, "failed")
        events = self.rt.message_queue.pending()
        failed_events = [e for e in events if e["type"] == "payment.failed"]
        self.assertTrue(any(e["payment_id"] == payment_id
                            for e in failed_events))

    def test_expiry_already_terminal_not_moved(self):
        """Declined payment is not moved by expiry tick."""
        status, body = self.authorize(amount=250_000_000)  # fraud -> declined
        self.assertEqual(body["status"], "Declined")
        self.now["t"] = T0 + AUTH_WINDOW + 1
        expired = self.rt.tick_expiry()
        self.assertEqual(expired, [])
        payment = self.rt.payment_store.load_payment(body["id"])
        self.assertEqual(payment.status.value, "declined")  # unchanged

    def test_expiry_captured_not_moved(self):
        """Captured payment is not expired (only Authorized is)."""
        payment_id, _ = self.captured_payment()
        self.now["t"] = T0 + AUTH_WINDOW + 1
        expired = self.rt.tick_expiry()
        self.assertNotIn(payment_id, expired)
        payment = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(payment.status.value, "captured")

    def test_capture_after_expiry_still_409_and_row_is_failed(self):
        """Capture after expiry -> 409; but also tick has moved row to Failed
        (not just the validation — the row itself is terminal)."""
        payment_id, _, _ = self.authorized_payment()
        self.now["t"] = T0 + AUTH_WINDOW + 1
        self.rt.tick_expiry()
        status, body = self.capture(payment_id, amount=500000)
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "invalid_state_transition")
        payment = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(payment.status.value, "failed")

    def test_expiry_webhook_delivered_async(self):
        """payment.failed webhook delivered after drain, not inline."""
        payment_id, _, _ = self.authorized_payment()
        self.now["t"] = T0 + AUTH_WINDOW + 1
        self.rt.tick_expiry()
        self.assertEqual(self.rt.merchant_platform.deliveries, [])
        self.rt.drain_webhooks()
        self.assertTrue(len(self.rt.merchant_platform.deliveries) >= 1)


# --------------------------------------------------------------------------
# CON.6 timeout — AcquirerHost not answering
#   G5: same transaction reference, no duplicate charge, Payment = Failed
# --------------------------------------------------------------------------
class CON6TimeoutTests(RuntimeTestCase):

    def test_con6_timeout_authorize_pending_to_failed(self):
        """CON.6: acquirer exhausted -> Pending -> Failed (G5)."""
        self.rt.acquirer_host.timeout_next_n = 99  # all calls time out
        status, body = self.authorize(amount=500000)
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "Failed")
        self.assertEqual(body["decline_reason"], "acquirer_timeout")
        payment = self.rt.payment_store.load_payment(body["id"])
        self.assertEqual(payment.status.value, "failed")

    def test_con6_same_transaction_reference_no_duplicate(self):
        """S11 / G5: retry uses the SAME transaction reference. Only one
        payment id appears in acquirer calls (no second authorize creates
        a duplicate charge)."""
        self.rt.acquirer_host.timeout_next_n = 99
        status, body = self.authorize(amount=500000)
        payment_id = body["id"]
        # All authorize calls share the same transaction reference
        auth_calls = self.acquirer_calls_of("authorize")
        refs = {c[1] for c in auth_calls}
        self.assertEqual(refs, {payment_id})
        # Exactly 2 attempts (initial + 1 retry per CON.6)
        self.assertEqual(len(auth_calls), 2)

    def test_con6_retry_succeeds_on_second_attempt(self):
        """CON.6: first attempt times out, retry succeeds -> Authorized."""
        self.rt.acquirer_host.timeout_next_n = 1  # only first call times out
        status, body = self.authorize(amount=500000)
        self.assertEqual(status, 201)
        self.assertEqual(body["status"], "Authorized")
        # Two authorize calls: first timed out, second succeeded
        auth_calls = self.acquirer_calls_of("authorize")
        self.assertEqual(len(auth_calls), 2)

    def test_con6_failed_event_published(self):
        """payment.failed event published on timeout exhaustion."""
        self.rt.acquirer_host.timeout_next_n = 99
        self.authorize(amount=500000)
        events = self.rt.message_queue.pending()
        self.assertEqual(events[-1]["type"], "payment.failed")
