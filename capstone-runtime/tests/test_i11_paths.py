"""I-11 slice: every named use case runs — happy path + the `alt` named in
I-11, plus the other in-scope alts of those same operations (Lab 10 §1–§3).

G5 proof lives here: for each named `alt` the test asserts the compensating
action actually happens (persisted Declined / rejected with unchanged I-6
state AND zero acquirer calls), not a bare 4xx.
"""

from .support import RuntimeTestCase, T0

AUTH_WINDOW = 7 * 86400        # CON.4
REFUND_WINDOW = 180 * 86400    # CON.5


# --------------------------------------------------------------------------
# I-11 use case 1 — "Authorize Payment"
#   happy: ... Fraud pass -> AcquirerHost approve -> Persist Authorized
#   alt (named in I-11): "Fraud blocks -> Declined (no acquirer call)"
# --------------------------------------------------------------------------
class AuthorizePaymentTests(RuntimeTestCase):

    def test_authorize_happy_path_authorized(self):
        """I-6 #1: Pending -> Authorized. Persisted, event on queue (async)."""
        status, body = self.authorize(amount=500000)
        self.assertEqual(status, 201)
        self.assertEqual(body["status"], "authorized")
        self.assertTrue(body["auth_code"])
        payment = self.rt.payment_store.load_payment(body["id"])
        self.assertEqual(payment.status.value, "authorized")
        self.assertEqual(payment.expires_at, T0 + AUTH_WINDOW)  # CON.4
        self.assertEqual(len(self.acquirer_calls_of("authorize")), 1)
        self.assertEqual([e["type"] for e in self.rt.message_queue.pending()],
                         ["payment.authorized"])

    def test_authorize_alt_fraud_block_declined_no_acquirer_call(self):
        """I-11 named alt + G5 (Lab 3 exception spec CON.3): trigger = fraud
        rule blocks; compensate = Payment -> Declined AND no acquirer call;
        performed by Fraud Gate (Payment Orchestrator)."""
        status, body = self.authorize(amount=250_000_000)  # > FRAUD-02 limit
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "declined")
        self.assertEqual(body["decline_reason"], "fraud_rule")
        self.assertEqual(body["fraud_rule"], "FRAUD-02")
        payment = self.rt.payment_store.load_payment(body["id"])
        self.assertEqual(payment.status.value, "declined")  # compensated
        self.assertEqual(self.rt.acquirer_host.calls, [])    # no acquirer call
        self.assertEqual([e["type"] for e in self.rt.message_queue.pending()],
                         ["payment.declined"])

    def test_authorize_direct_charge_captured(self):
        """I-6 #2 (Lab 10 §1 alt Direct Charge): capture:true ->
        Pending -> Captured in one operation."""
        status, body = self.authorize(amount=500000, capture=True)
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "captured")
        self.assertEqual(body["captured_amount"], 500000)
        payment = self.rt.payment_store.load_payment(body["id"])
        self.assertEqual(payment.status.value, "captured")
        kinds = [c[0] for c in self.rt.acquirer_host.calls]
        self.assertEqual(kinds, ["authorize", "capture"])

    def test_authorize_issuer_decline(self):
        """I-6 #4 (Lab 10 §1 alt Issuer Decline): acquirer DECLINE ->
        Declined (persisted), no capture side effects."""
        class DecliningAcquirerHost(self.rt.acquirer_host.__class__):
            def authorize(self, transaction_ref, amount, card):
                self.calls.append(("authorize", transaction_ref, amount))
                return {"decision": "DECLINE", "reason_code": "05"}

        self.rt.request_handler.acquirer.acquirer_host = DecliningAcquirerHost()
        status, body = self.authorize()
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "declined")
        self.assertEqual(body["decline_reason"], "issuer_decline")
        payment = self.rt.payment_store.load_payment(body["id"])
        self.assertEqual(payment.status.value, "declined")

    def test_authorize_duplicate_key_replays_cached_response(self):
        """Lab 10 §1 alt Idempotency Duplicate (CON.2): same key replays the
        original status+body; fraud evaluated once, acquirer called once."""
        first_status, first_body = self.authorize(amount=500000,
                                                  key="dup-key")
        self.rt.acquirer_host.calls.clear()
        second_status, second_body = self.authorize(amount=123456,
                                                    key="dup-key")
        self.assertEqual((second_status, second_body),
                         (first_status, first_body))
        self.assertEqual(self.rt.acquirer_host.calls, [])
        self.assertEqual(self.rt.request_handler.fraud_gate.evaluations, 1)

    def test_authorize_concurrent_same_key_conflict_409(self):
        """Lab 10 §1 alt Concurrent Same Key (CON.2): in-flight lock ->
        409 idempotency_conflict (5s BLPOP wait collapsed, see name-map)."""
        self.assertTrue(self.rt.idempotency_store.try_lock("busy-key"))
        status, body = self.authorize(key="busy-key")
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "idempotency_conflict")


# --------------------------------------------------------------------------
# I-11 use case 2 — "Capture Payment"
#   alt (named in I-11): "Auth expired -> 409 authorization_expired"
# --------------------------------------------------------------------------
class CapturePaymentTests(RuntimeTestCase):

    def test_capture_happy_path_captured(self):
        """I-6 #6: Authorized -> Captured after acquirer capture."""
        payment_id, _, _ = self.authorized_payment()
        status, body = self.capture(payment_id, amount=500000)
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "captured")
        self.assertEqual(body["captured_amount"], 500000)
        self.assertFalse(body["remainder_voided"])
        payment = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(payment.status.value, "captured")

    def test_capture_alt_authorization_expired_409_no_acquirer_call(self):
        """I-11 named alt + G5 (CON.4): trigger = expiresAt <= now;
        compensate = 409 authorization_expired, no acquirer capture, I-6
        state unchanged (still Authorized); performed by State Machine
        Engine."""
        payment_id, _, _ = self.authorized_payment()
        self.now["t"] = T0 + AUTH_WINDOW + 1  # cross the 7-day window
        self.rt.acquirer_host.calls.clear()
        status, body = self.capture(payment_id, amount=500000)
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "authorization_expired")
        self.assertEqual(self.acquirer_calls_of("capture"), [])  # no call
        payment = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(payment.status.value, "authorized")  # unchanged

    def test_capture_amount_exceeds_authorized_400(self):
        """Lab 10 §2 alt: amount > authorizedAmount -> 400."""
        payment_id, _, _ = self.authorized_payment(amount=500000)
        status, body = self.capture(payment_id, amount=500001)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "amount_exceeds_authorized")
        self.assertEqual(self.acquirer_calls_of("capture"), [])

    def test_capture_invalid_state_transition_409(self):
        """Lab 10 §2 alt: status != Authorized -> 409 invalid_state_transition."""
        payment_id, _ = self.captured_payment()
        status, body = self.capture(payment_id, amount=100000)
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "invalid_state_transition")

    def test_capture_partial_capture_voids_remainder(self):
        """Lab 10 §2 alt Partial Capture: remainder voided at acquirer."""
        payment_id, _, _ = self.authorized_payment(amount=500000)
        status, body = self.capture(payment_id, amount=300000)
        self.assertEqual(status, 200)
        self.assertTrue(body["remainder_voided"])
        self.assertEqual(body["captured_amount"], 300000)
        self.assertEqual(self.acquirer_calls_of("void"),
                         [("void", payment_id, 200000)])

    def test_capture_unknown_payment_404(self):
        status, body = self.capture("pay_99999999", amount=500000)
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "payment_not_found")


# --------------------------------------------------------------------------
# I-11 use case 3 — "Refund Payment"
#   alt (named in I-11): "Max refunds exceeded -> 400 max_refunds_exceeded"
# --------------------------------------------------------------------------
class RefundPaymentTests(RuntimeTestCase):

    def test_refund_partial_stays_captured(self):
        """I-6 #10 (happy path): Captured -> Captured, refundedAmount updated."""
        payment_id, _ = self.captured_payment(amount=500000)
        status, body = self.refund(payment_id, amount=100000)
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "captured")
        self.assertEqual(body["refunded_amount"], 100000)
        self.assertEqual(body["refund_count"], 1)
        payment = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(payment.status.value, "captured")

    def test_refund_full_refund_terminal_state(self):
        """I-6 #9 (Lab 10 §3 alt Full Refund): Captured -> Refunded."""
        payment_id, _ = self.captured_payment(amount=500000)
        status, body = self.refund(payment_id, amount=500000)
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "refunded")
        payment = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(payment.status.value, "refunded")
        from payment_gateway.payment import TERMINAL_STATES
        self.assertIn(payment.status, TERMINAL_STATES)

    def test_refund_alt_max_refunds_exceeded_400_no_acquirer_call(self):
        """I-11 named alt + G5 (CON.5): trigger = refundCount >= 10;
        compensate = 400 max_refunds_exceeded, no acquirer refund call,
        refundedAmount/refundCount unchanged; performed by State Machine
        Engine."""
        payment_id, _ = self.captured_payment(amount=500000)
        for i in range(10):  # 10 partial refunds stay Captured (CON.5 max)
            status, body = self.refund(payment_id, amount=10000)
            self.assertEqual(status, 200)
        before = self.rt.payment_store.load_payment(payment_id)
        refund_calls_before = len(self.acquirer_calls_of("refund"))
        status, body = self.refund(payment_id, amount=10000)  # 11th attempt
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "max_refunds_exceeded")
        self.assertEqual(len(self.acquirer_calls_of("refund")),
                         refund_calls_before)  # no acquirer call
        after = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(after.refunded_amount, before.refunded_amount)
        self.assertEqual(after.refund_count, before.refund_count)  # 10
        self.assertEqual(after.status.value, "captured")  # unchanged

    def test_refund_amount_exceeds_refundable_400(self):
        """Lab 10 §3 alt: amount > refundable remainder -> 400."""
        payment_id, _ = self.captured_payment(amount=500000)
        status, body = self.refund(payment_id, amount=100000)
        self.assertEqual(status, 200)
        status, body = self.refund(payment_id, amount=450000)
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "amount_exceeds_refundable")

    def test_refund_window_expired_409(self):
        """Lab 10 §3 alt (CON.5): capturedAt + 180d <= now -> 409."""
        payment_id, _ = self.captured_payment(amount=500000)
        self.now["t"] = T0 + REFUND_WINDOW + 1
        status, body = self.refund(payment_id, amount=100000)
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "refund_window_expired")

    def test_refund_invalid_state_transition_409(self):
        """Lab 10 §3 alt: status != Captured -> 409 invalid_state_transition."""
        payment_id, _, _ = self.authorized_payment()  # Authorized, not Captured
        status, body = self.refund(payment_id, amount=100000)
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "invalid_state_transition")

    def test_refund_unknown_payment_404(self):
        status, body = self.refund("pay_99999999", amount=100000)
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "payment_not_found")
