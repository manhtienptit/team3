"""I-3 mocks (stub / in-process fake). No real host, no production credentials.

See README.md "I-3 mock list". AcquirerHost stub internally stands for the
AcquirerHost -> NAPAS Switch -> Issuing Bank chain (I-3 names stay labels).
"""

import hashlib
import hmac


class AcquirerHostStub:
    """Stub for I-3 AcquirerHost (which routes via NAPAS Switch to Issuing
    Bank). Records every call so tests can assert "no acquirer call" (CON.3,
    G5) and detect direct calls from Merchant Platform (I-9 forbidden path).
    """

    def __init__(self):
        self.calls = []

    def authorize(self, transaction_ref, amount, card):
        self.calls.append(("authorize", transaction_ref, amount))
        return {"decision": "APPROVE", "auth_code": "A-000001"}

    def capture(self, transaction_ref, amount):
        self.calls.append(("capture", transaction_ref, amount))
        return {"decision": "CAPTURE_OK"}

    def refund(self, transaction_ref, amount):
        self.calls.append(("refund", transaction_ref, amount))
        return {"decision": "REFUND_OK"}

    def void(self, transaction_ref, amount):
        self.calls.append(("void", transaction_ref, amount))
        return {"decision": "VOID_OK"}


class MerchantPlatformFake:
    """In-process fake for I-3 Merchant Platform: receives webhook deliveries
    and verifies the HMAC-SHA256 signature. It holds no reference to
    AcquirerHost (I-9: Merchant Platform must NOT query AcquirerHost directly
    — no such relationship exists on Lab 9, so none is wired here either;
    tests attempt the call through the runtime surface and are rejected).
    """

    def __init__(self):
        self.deliveries = []
        self.secret = b"simulated-webhook-secret"  # simulated, not production
        self.fail_first_n = 0  # test scripting for CON.7 retry

    def receive_webhook(self, payload, signature):
        """Returns True when the delivery is accepted (200 from merchant)."""
        if self.fail_first_n > 0:
            self.fail_first_n -= 1
            return False
        body = payload.encode()
        expected = hmac.new(self.secret, body, hashlib.sha256).hexdigest()
        valid = hmac.compare_digest(expected, signature)
        self.deliveries.append({"payload": payload, "signature": signature,
                                "valid_signature": valid})
        return True
