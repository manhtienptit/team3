"""G4 drift gate: openapi.json is the public contract of this sitting, so
the runtime is asserted against it in BOTH directions —

  forward:  every scenario's (operation, status, error-or-status code) is
            declared in the document;
  reverse:  every declared error code and success status enum value for the
            three payment operations is exercised by some scenario.

No documented 400 that the runtime never returns; no runtime 409 missing
from the document (capstone: "OpenAPI ... drifted from runtime" = fail).
"""

import json
from pathlib import Path

from .support import RuntimeTestCase, CARD, T0

OPENAPI = json.loads(
    (Path(__file__).resolve().parents[1] / "openapi.json").read_text())

PAYMENT_OPS = {
    "authorizePayment": "/v1/payments",
    "capturePayment": "/v1/payments/{payment_id}/capture",
    "refundPayment": "/v1/payments/{payment_id}/refund",
}
AUTH_WINDOW = 7 * 86400
REFUND_WINDOW = 180 * 86400


def documented(path, status):
    responses = OPENAPI["paths"][path]["post"]["responses"]
    return responses[str(status)]


def error_codes(path, status):
    return documented(path, status)["content"]["application/json"]["schema"] \
        .get("x-error-codes", [])


def status_enum(path, status):
    schema = documented(path, status)["content"]["application/json"]["schema"]
    return schema.get("properties", {}).get("status", {}).get("enum", [])


class OpenApiContractTests(RuntimeTestCase):

    def test_document_has_exactly_the_in_scope_paths(self):
        self.assertEqual(
            set(OPENAPI["paths"].keys()),
            {"/v1/payments",
             "/v1/payments/{payment_id}/capture",
             "/v1/payments/{payment_id}/refund",
             "/webhooks"},
            "Void Payment / Payment Query are N/A (not I-11) and must not "
            "appear; /webhooks covers the Lab 3 §4 delivery row")

    def test_runtime_matches_openapi_both_directions(self):
        seen = set()

        def record(op, status, body):
            code = body.get("error") or body.get("status")
            path = PAYMENT_OPS[op]
            responses = OPENAPI["paths"][path]["post"]["responses"]
            self.assertIn(str(status), responses,
                          f"{op}: runtime returned undocumented status "
                          f"{status} {body}")
            allowed = error_codes(path, status) or status_enum(path, status)
            self.assertIn(code, allowed,
                          f"{op} {status}: runtime body {body!r} drifted "
                          f"from openapi.json (allowed: {allowed})")
            seen.add((op, str(status), code))

        # ---------------- POST /v1/payments (authorizePayment) ----------
        op = "authorizePayment"
        status, body = self.authorize(amount=500000)
        self.assertEqual(status, 201)
        record(op, status, body)

        status, body = self.authorize(amount=250_000_000)  # named alt
        self.assertEqual(status, 200)
        record(op, status, body)

        status, body = self.authorize(amount=500000, capture=True)
        self.assertEqual(status, 200)
        record(op, status, body)

        status, body = self.rt.handle("POST", "/v1/payments",
                                      {"amount": 500000, "card": dict(CARD)})
        self.assertEqual(status, 400)
        record(op, status, body)

        status, body = self.authorize(amount=9_999)
        self.assertEqual(status, 400)
        record(op, status, body)

        status, body = self.authorize(
            card={"number": "4111111111111112", "exp_month": 12,
                  "exp_year": 2030})
        self.assertEqual(status, 400)
        record(op, status, body)

        self.rt.idempotency_store.try_lock("busy")
        status, body = self.authorize(key="busy")
        self.assertEqual(status, 409)
        record(op, status, body)

        # ---------------- capture ---------------------------------------
        op = "capturePayment"
        pid, _, _ = self.authorized_payment()
        status, body = self.capture(pid, amount=500000)
        self.assertEqual(status, 200)
        record(op, status, body)

        status, body = self.rt.handle(
            "POST", f"/v1/payments/{pid}/capture", {"idempotency_key": "x"})
        self.assertEqual(status, 400)
        record(op, status, body)

        pid2, _, _ = self.authorized_payment(amount=500000)
        status, body = self.capture(pid2, amount=500001)
        self.assertEqual(status, 400)
        record(op, status, body)

        status, body = self.capture("pay_99999999", amount=500000)
        self.assertEqual(status, 404)
        record(op, status, body)

        pid3, _, _ = self.authorized_payment()
        self.now["t"] = T0 + AUTH_WINDOW + 1
        status, body = self.capture(pid3, amount=500000)  # named alt
        self.assertEqual(status, 409)
        record(op, status, body)

        pid4, cap_body = self.captured_payment()
        status, body = self.capture(pid4, amount=100000)
        self.assertEqual(status, 409)
        record(op, status, body)

        self.rt.idempotency_store.try_lock("cap-busy")
        status, body = self.capture(pid4, amount=100000, key="cap-busy")
        self.assertEqual(status, 409)
        record(op, status, body)

        # ---------------- refund ----------------------------------------
        op = "refundPayment"
        pid5, _ = self.captured_payment(amount=500000)
        status, body = self.refund(pid5, amount=100000)
        self.assertEqual(status, 200)
        record(op, status, body)

        status, body = self.refund(pid5, amount=400000)  # full -> Refunded
        self.assertEqual(status, 200)
        record(op, status, body)

        status, body = self.rt.handle(
            "POST", f"/v1/payments/{pid5}/refund", {"idempotency_key": "x"})
        self.assertEqual(status, 400)
        record(op, status, body)

        pid6, _ = self.captured_payment(amount=500000)
        for _ in range(10):
            self.refund(pid6, amount=10000)
        status, body = self.refund(pid6, amount=10000)  # named alt
        self.assertEqual(status, 400)
        record(op, status, body)

        pid6b, _ = self.captured_payment(amount=200000)
        status, body = self.refund(pid6b, amount=100000)
        self.assertEqual(status, 200)
        status, body = self.refund(pid6b, amount=150000)  # > remainder
        self.assertEqual(status, 400)
        record(op, status, body)

        status, body = self.refund("pay_99999999", amount=100000)
        self.assertEqual(status, 404)
        record(op, status, body)

        self.now["t"] = T0  # back to base time so windows are exact
        pid7, _ = self.captured_payment(amount=500000)
        self.now["t"] = T0 + REFUND_WINDOW + 1
        status, body = self.refund(pid7, amount=100000)
        self.assertEqual(status, 409)
        record(op, status, body)

        self.now["t"] = T0
        pid8, _, _ = self.authorized_payment()  # Authorized, not Captured
        status, body = self.refund(pid8, amount=100000)
        self.assertEqual(status, 409)
        record(op, status, body)

        self.rt.idempotency_store.try_lock("ref-busy")
        status, body = self.refund(pid8, amount=100000, key="ref-busy")
        self.assertEqual(status, 409)
        record(op, status, body)

        # ---------------- forward + reverse assertions -------------------
        for op_id, path in PAYMENT_OPS.items():
            for status_code, response in \
                    OPENAPI["paths"][path]["post"]["responses"].items():
                for code in error_codes(path, status_code):
                    self.assertIn(
                        (op_id, status_code, code), seen,
                        f"documented but never returned by the runtime: "
                        f"{op_id} {status_code} {code}")
                for value in status_enum(path, status_code):
                    self.assertIn(
                        (op_id, status_code, value), seen,
                        f"documented success status never returned: "
                        f"{op_id} {status_code} {value}")

    def test_webhook_delivery_matches_webhook_event_schema(self):
        self.authorize()
        self.rt.drain_webhooks()
        payload = json.loads(
            self.rt.merchant_platform.deliveries[0]["payload"])
        schema = OPENAPI["components"]["schemas"]["WebhookEvent"]
        self.assertEqual(set(schema["required"]), set(payload.keys()))
        self.assertIn(payload["type"],
                     schema["properties"]["type"]["enum"])
        self.assertTrue(
            self.rt.merchant_platform.deliveries[0]["valid_signature"])
