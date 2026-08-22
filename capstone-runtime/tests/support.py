"""Shared test fixtures (test helper only — not a new I-4 identity).

Fresh runtime per test with an injectable clock so CON.4 (7-day auth
window) and CON.5 (180-day refund window) can be crossed without sleeping.
"""

import itertools
import unittest

from payment_gateway.runtime import PaymentGatewayRuntime

T0 = 1_700_000_000
CARD = {"number": "4111111111111111", "exp_month": 12, "exp_year": 2030,
        "bin_country": "VN"}


def make_card(n):
    """Distinct Luhn-valid 16-digit simulated PAN (no real card data).
    Fresh card per authorize call: FRAUD-01 card velocity is per-card, and
    one test creating many payments must not trip it by accident."""
    base = f"4{n:014d}"  # 15 digits
    total = 0
    for i, ch in enumerate(base):
        d = int(ch)
        if (15 - i) % 2 == 1:
            d = d * 2
            if d > 9:
                d -= 9
        total += d
    return base + str((10 - total % 10) % 10)


class RuntimeTestCase(unittest.TestCase):
    def setUp(self):
        self.now = {"t": T0}
        self.rt = PaymentGatewayRuntime(clock=lambda: self.now["t"])
        self._keys = itertools.count(1)
        self._cards = itertools.count(1)

    def _key(self, prefix):
        return f"{prefix}-{next(self._keys)}"

    def fresh_card(self):
        return {"number": make_card(next(self._cards)), "exp_month": 12,
                "exp_year": 2030, "bin_country": "VN"}

    def authorize(self, amount=500000, key=None, **over):
        card = over.pop("card", None) or self.fresh_card()
        body = {"amount": amount, "card": card,
                "idempotency_key": key or self._key("auth")}
        body.update(over)
        return self.rt.handle("POST", "/v1/payments", body)

    def capture(self, payment_id, amount=500000, key=None):
        return self.rt.handle(
            "POST", f"/v1/payments/{payment_id}/capture",
            {"amount": amount, "idempotency_key": key or self._key("cap")})

    def refund(self, payment_id, amount, key=None):
        return self.rt.handle(
            "POST", f"/v1/payments/{payment_id}/refund",
            {"amount": amount, "idempotency_key": key or self._key("ref")})

    def authorized_payment(self, amount=500000):
        """Authorize and return (payment_id, status, body)."""
        status, body = self.authorize(amount=amount)
        assert status == 201, body
        return body["id"], status, body

    def captured_payment(self, amount=500000, capture_amount=None):
        """Authorize + capture; returns (payment_id, capture body)."""
        payment_id, _, _ = self.authorized_payment(amount)
        status, body = self.capture(payment_id,
                                    amount=capture_amount or amount)
        assert status == 200, body
        return payment_id, body

    def acquirer_calls_of(self, kind):
        return [c for c in self.rt.acquirer_host.calls if c[0] == kind]
