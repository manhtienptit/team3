"""Slice B — Security properties (S1–S11). Each test ATTEMPTS a violation
and asserts the runtime REJECTS it.

These are named properties from Lab 1 / I-4 / I-5 / I-9 / CON.* — not
invented. No Keycloak, mTLS, WAF, or 3DS.
"""

import json
import hmac
import hashlib

from payment_gateway.runtime import PaymentGatewayRuntime
from payment_gateway.query_store import QueryStore

from .support import RuntimeTestCase, T0, TEST_WEBHOOK_SECRET, CARD


class S1SecretsNotInSourceTests(RuntimeTestCase):
    """S1: WEBHOOK_SECRET not hardcoded. Runtime refuses to start without it."""

    def test_s1_runtime_refuses_to_start_without_secret(self):
        """Process starts with WEBHOOK_SECRET unset -> RuntimeError."""
        import os
        old = os.environ.pop("WEBHOOK_SECRET", None)
        try:
            with self.assertRaises(RuntimeError) as ctx:
                PaymentGatewayRuntime(clock=lambda: T0, webhook_secret="")
            self.assertIn("WEBHOOK_SECRET", str(ctx.exception))
        finally:
            if old is not None:
                os.environ["WEBHOOK_SECRET"] = old

    def test_s1_no_hardcoded_default_in_source(self):
        """Grep test: the string 'simulated-webhook-secret' must not appear
        as a getenv default or fallback anywhere in payment_gateway/."""
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[1] / "payment_gateway"
        for py_file in root.rglob("*.py"):
            content = py_file.read_text()
            # Allow it in test files / comments about the old version
            if "simulated-webhook-secret" in content:
                # Must not be a getenv default
                self.assertNotIn(
                    'get("WEBHOOK_SECRET", "simulated-webhook-secret")',
                    content,
                    f"S1 violation in {py_file.name}: hardcoded default")


class S2WebhookHMACTests(RuntimeTestCase):
    """S2: Wrong HMAC signature -> delivery rejected."""

    def test_s2_wrong_signature_rejected(self):
        """Deliver with a wrong signature -> not accepted."""
        self.authorize(amount=500000)
        # Tamper with the merchant platform to use wrong secret
        self.rt.merchant_platform.secret = b"wrong-secret"
        self.rt.drain_webhooks()
        # Event recorded as failed_delivery (signature mismatch)
        events = self.rt.payment_store.webhook_events()
        self.assertEqual(events[0]["status"], "failed_delivery")
        # No delivery accepted
        self.assertEqual(self.rt.merchant_platform.deliveries, [])


class S3NoPANTests(RuntimeTestCase):
    """S3: Full PAN never stored, never in Query, never in webhook."""

    def test_s3_payment_store_row_has_no_full_pan(self):
        """Authorize then inspect Payment Store row: only card_ref (last 4)."""
        payment_id, _, _ = self.authorized_payment()
        payment = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(len(payment.card_ref), 4)
        self.assertFalse(hasattr(payment, "card_number"))
        self.assertFalse(hasattr(payment, "pan"))

    def test_s3_query_response_has_no_full_pan(self):
        """GET response contains card_ref (4 chars), never full PAN."""
        payment_id, _, _ = self.authorized_payment()
        status, body = self.query(payment_id)
        self.assertEqual(status, 200)
        self.assertEqual(len(body["card_ref"]), 4)
        # Ensure no field in the response is a 12+ digit string (PAN-like)
        for key, value in body.items():
            if isinstance(value, str) and len(value) >= 12:
                self.assertFalse(value.replace(" ", "").isdigit(),
                                 f"S3: possible PAN in query field '{key}'")

    def test_s3_webhook_payload_has_no_full_pan(self):
        """Webhook event payload contains no full PAN."""
        self.authorize(amount=500000)
        self.rt.drain_webhooks()
        delivery = self.rt.merchant_platform.deliveries[0]
        payload = json.loads(delivery["payload"])
        for key, value in payload.items():
            if isinstance(value, str) and len(value) >= 12:
                self.assertFalse(value.replace(" ", "").isdigit(),
                                 f"S3: possible PAN in webhook field '{key}'")


class S4QueryNeverCallsAcquirerTests(RuntimeTestCase):
    """S4: Payment Query NEVER calls AcquirerHost / NAPAS Switch (I-5)."""

    def test_s4_get_while_stub_would_fail(self):
        """GET with acquirer stub set to timeout -> 200 still, no calls."""
        payment_id, _, _ = self.authorized_payment()
        calls_before = len(self.rt.acquirer_host.calls)
        self.rt.acquirer_host.timeout_next_n = 99  # would fail if called
        status, body = self.query(payment_id)
        self.assertEqual(status, 200)
        self.assertEqual(len(self.rt.acquirer_host.calls), calls_before)

    def test_s4_unknown_query_no_acquirer_calls(self):
        """GET 404 also makes no acquirer calls."""
        calls_before = len(self.rt.acquirer_host.calls)
        status, _ = self.query("pay_99999999")
        self.assertEqual(status, 404)
        self.assertEqual(len(self.rt.acquirer_host.calls), calls_before)


class S5FraudNeverOnVoidTests(RuntimeTestCase):
    """S5: Fraud Gate NEVER evaluates on the void path (I-5 / CON.3)."""

    def test_s5_void_fraud_count_unchanged(self):
        """Void after authorize: fraud evaluation count unchanged."""
        payment_id, _, _ = self.authorized_payment()
        evaluations_after_auth = self.rt.request_handler.fraud_gate.evaluations
        status, body = self.void(payment_id)
        self.assertEqual(status, 200)
        self.assertEqual(self.rt.request_handler.fraud_gate.evaluations,
                         evaluations_after_auth)
        # Acquirer void IS called (unlike fraud which is not)
        self.assertTrue(len(self.acquirer_calls_of("void")) >= 1)


class S6WebhookServiceCannotWritePaymentTests(RuntimeTestCase):
    """S6: Webhook Service never writes Payment (I-9 / I-7). Kept from first sitting."""

    def test_s6_insert_payment_from_webhook_service_raises(self):
        payment_id, _, _ = self.authorized_payment()
        payment = self.rt.payment_store.load_payment(payment_id)
        with self.assertRaises(PermissionError):
            self.rt.payment_store.insert_payment(
                self.rt.webhook_service, payment)


class S7MerchantPlatformCannotCallAcquirerTests(RuntimeTestCase):
    """S7: Merchant Platform never queries AcquirerHost (I-9). Structural."""

    def test_s7_no_acquirer_attribute(self):
        self.assertFalse(hasattr(self.rt.merchant_platform, "acquirer"))
        self.assertFalse(hasattr(self.rt.merchant_platform, "acquirer_host"))

    def test_s7_no_method_reaching_acquirer(self):
        with self.assertRaises(AttributeError):
            self.rt.merchant_platform.acquirer_host.authorize(
                "tx", 500000, dict(CARD))


class S8QueryStoreCannotWritePaymentTests(RuntimeTestCase):
    """S8: Query Store never writes Payment (I-7). Read-only."""

    def test_s8_query_store_insert_raises(self):
        """Attempt insert_payment from query_store -> PermissionError."""
        payment_id, _, _ = self.authorized_payment()
        payment = self.rt.payment_store.load_payment(payment_id)
        with self.assertRaises(PermissionError):
            self.rt.payment_store.insert_payment(
                self.rt.query_store, payment)

    def test_s8_query_store_update_raises(self):
        """Attempt update_payment from query_store -> PermissionError."""
        payment_id, _, _ = self.authorized_payment()
        payment = self.rt.payment_store.load_payment(payment_id)
        with self.assertRaises(PermissionError):
            self.rt.payment_store.update_payment(
                self.rt.query_store, payment)

    def test_s8_get_path_does_not_update_status(self):
        """GET /v1/payments/{id} does not modify the payment row."""
        payment_id, _, _ = self.authorized_payment()
        before = self.rt.payment_store.load_payment(payment_id)
        before_status = before.status.value
        self.query(payment_id)
        after = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(after.status.value, before_status)


class S9RateLimitTests(RuntimeTestCase):
    """S9: Rate limiting — burst over ASSUMPTION cap -> 429."""

    def test_s9_burst_over_cap_returns_429(self):
        """ASSUMPTION: 100 req/merchant/60s. 101st -> 429."""
        from payment_gateway.api_gateway import RATE_LIMIT_CAP
        for i in range(RATE_LIMIT_CAP):
            status, _ = self.authorize(amount=500000)
            self.assertIn(status, (200, 201))
        # Next call exceeds the cap
        status, body = self.authorize(amount=500000)
        self.assertEqual(status, 429)
        self.assertEqual(body["error"], "rate_limit_exceeded")

    def test_s9_different_merchant_not_throttled(self):
        """Different merchant_id has its own bucket."""
        from payment_gateway.api_gateway import RATE_LIMIT_CAP
        for i in range(RATE_LIMIT_CAP):
            self.authorize(amount=500000, merchant_id="mer_3")
        # Different merchant still allowed
        status, _ = self.authorize(amount=500000, merchant_id="mer_other")
        self.assertIn(status, (200, 201))

    def test_s9_window_expires_allows_again(self):
        """After window passes, requests are allowed again."""
        from payment_gateway.api_gateway import RATE_LIMIT_CAP, RATE_LIMIT_WINDOW
        for i in range(RATE_LIMIT_CAP):
            self.authorize(amount=500000)
        # Advance clock past the window
        self.now["t"] = T0 + RATE_LIMIT_WINDOW + 1
        status, _ = self.authorize(amount=500000)
        self.assertIn(status, (200, 201))


class S10IdempotencyBeforeFraudTests(RuntimeTestCase):
    """S10: Idempotency before fraud and acquirer (I-5 / CON.2).
    First-sitting tests remain green — this just confirms."""

    def test_s10_order_log_shows_idempotency_first(self):
        self.authorize(amount=500000)
        self.assertEqual(self.rt.request_handler.order_log[:3],
                         ["idempotency_check", "fraud_evaluate",
                          "acquirer_call"])


class S11CON6NoDuplicateChargeTests(RuntimeTestCase):
    """S11: CON.6 timeout + retry uses same ref; no duplicate charge."""

    def test_s11_timeout_same_ref_payment_failed(self):
        """Timeout: all authorize calls share one transaction ref.
        Payment ends as Failed. No second authorize with a different ref."""
        self.rt.acquirer_host.timeout_next_n = 99
        status, body = self.authorize(amount=500000)
        self.assertEqual(body["status"], "Failed")
        payment_id = body["id"]
        auth_calls = self.acquirer_calls_of("authorize")
        # All calls use the same payment_id as transaction reference
        refs = set(c[1] for c in auth_calls)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs, {payment_id})
        # Payment is definitively Failed
        payment = self.rt.payment_store.load_payment(payment_id)
        self.assertEqual(payment.status.value, "failed")
