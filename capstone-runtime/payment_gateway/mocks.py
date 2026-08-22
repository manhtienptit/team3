"""I-3 mocks (stub / in-process fake). No real host, no production credentials.

See README.md "I-3 mock list". AcquirerHost stub internally stands for the
AcquirerHost -> NAPAS Switch -> Issuing Bank chain (I-3 names stay labels).
"""

import hashlib
import hmac
import os


class AcquirerTimeout(Exception):
    """Simulates CON.6: AcquirerHost did not respond within 30s (label)."""
    pass


class AcquirerHostStub:
    """Stub for I-3 AcquirerHost (which routes via NAPAS Switch to Issuing
    Bank). Records every call so tests can assert "no acquirer call" (CON.3,
    G5) and detect direct calls from Merchant Platform (I-9 forbidden path).

    CON.6: `timeout_next_n` can be set to simulate acquirer non-response.
    """

    def __init__(self):
        self.calls = []
        self.timeout_next_n = 0  # CON.6: number of calls that will time out

    def _maybe_timeout(self):
        if self.timeout_next_n > 0:
            self.timeout_next_n -= 1
            raise AcquirerTimeout("acquirer did not respond (CON.6 30s label)")

    def authorize(self, transaction_ref, amount, card):
        self.calls.append(("authorize", transaction_ref, amount))
        self._maybe_timeout()
        return {"decision": "APPROVE", "auth_code": "A-000001"}

    def capture(self, transaction_ref, amount):
        self.calls.append(("capture", transaction_ref, amount))
        self._maybe_timeout()
        return {"decision": "CAPTURE_OK"}

    def refund(self, transaction_ref, amount):
        self.calls.append(("refund", transaction_ref, amount))
        self._maybe_timeout()
        return {"decision": "REFUND_OK"}

    def void(self, transaction_ref, amount):
        self.calls.append(("void", transaction_ref, amount))
        self._maybe_timeout()
        return {"decision": "VOID_OK"}


class MerchantPlatformFake:
    """In-process fake for I-3 Merchant Platform: receives webhook deliveries
    and verifies the HMAC-SHA256 signature. It holds no reference to
    AcquirerHost (I-9: Merchant Platform must NOT query AcquirerHost directly).
    """

    def __init__(self):
        self.deliveries = []
        # S1: secret comes from environment; no hardcoded default in source.
        # For tests, the runtime injects the value explicitly.
        self.secret = os.environ.get("WEBHOOK_SECRET", "").encode() or None
        self.fail_first_n = 0  # test scripting for CON.7 retry

    def receive_webhook(self, payload, signature):
        """Returns True when the delivery is accepted (200 from merchant)."""
        if self.fail_first_n > 0:
            self.fail_first_n -= 1
            return False
        if self.secret is None:
            return False  # cannot verify without secret
        body = payload.encode()
        expected = hmac.new(self.secret, body, hashlib.sha256).hexdigest()
        valid = hmac.compare_digest(expected, signature)
        if not valid:
            return False  # S2: reject wrong signature
        self.deliveries.append({"payload": payload, "signature": signature,
                                "valid_signature": True})
        return True

    # I-9 forbidden path: there is deliberately no method here that reaches
    # AcquirerHost, and no attribute referencing it. The Lab 9 relationship
    # list has no Merchant Platform -> AcquirerHost edge, so the absence is
    # structural, not a guarded call that only raises.
