"""Acquirer Client module (Lab 3 §2). Talks to AcquirerHost (mocked I-3).

CON.6: 30s timeout + 1 retry (same transaction reference). If both attempts
fail, raises AcquirerExhausted so the caller transitions to Failed.
The 30s and 5s-between-retry are labels (collapsed build: stub raises
AcquirerTimeout immediately when configured to time out).
"""

from ..mocks import AcquirerTimeout

MAX_ATTEMPTS = 2  # CON.6: initial + 1 retry


class AcquirerExhausted(Exception):
    """CON.6: acquirer did not respond after all retry attempts."""
    def __init__(self, transaction_ref):
        super().__init__(f"acquirer exhausted for {transaction_ref}")
        self.transaction_ref = transaction_ref


class AcquirerClient:
    def __init__(self, acquirer_host_stub):
        self.acquirer_host = acquirer_host_stub

    def authorize(self, transaction_ref, amount, card):
        """CON.6: retry once with the SAME transaction reference (no second
        authorize creates a duplicate charge — G5 S11)."""
        for attempt in range(MAX_ATTEMPTS):
            try:
                result = self.acquirer_host.authorize(
                    transaction_ref, amount, card)
                if result["decision"] == "APPROVE":
                    return "approved", result["auth_code"]
                return "declined", result.get("reason_code")
            except AcquirerTimeout:
                if attempt == MAX_ATTEMPTS - 1:
                    raise AcquirerExhausted(transaction_ref)
        raise AcquirerExhausted(transaction_ref)  # pragma: no cover

    def capture(self, transaction_ref, amount):
        for attempt in range(MAX_ATTEMPTS):
            try:
                result = self.acquirer_host.capture(transaction_ref, amount)
                return result["decision"] == "CAPTURE_OK"
            except AcquirerTimeout:
                if attempt == MAX_ATTEMPTS - 1:
                    raise AcquirerExhausted(transaction_ref)
        raise AcquirerExhausted(transaction_ref)  # pragma: no cover

    def refund(self, transaction_ref, amount):
        for attempt in range(MAX_ATTEMPTS):
            try:
                result = self.acquirer_host.refund(transaction_ref, amount)
                return result["decision"] == "REFUND_OK"
            except AcquirerTimeout:
                if attempt == MAX_ATTEMPTS - 1:
                    raise AcquirerExhausted(transaction_ref)
        raise AcquirerExhausted(transaction_ref)  # pragma: no cover

    def void(self, transaction_ref, amount):
        """AcquirerHost void — used by Void Payment (Authorized -> Voided)
        and by the Partial Capture alt (Lab 10 §2, void remainder)."""
        for attempt in range(MAX_ATTEMPTS):
            try:
                result = self.acquirer_host.void(transaction_ref, amount)
                return result["decision"] == "VOID_OK"
            except AcquirerTimeout:
                if attempt == MAX_ATTEMPTS - 1:
                    raise AcquirerExhausted(transaction_ref)
        raise AcquirerExhausted(transaction_ref)  # pragma: no cover
