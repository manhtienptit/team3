"""Acquirer Client module (Lab 3 §2). Talks to AcquirerHost (mocked I-3)."""


class AcquirerClient:
    """CON.6 labels (30s timeout + 1 retry) stay labels over the stub; the
    stub never sleeps, so the CON.6 timeout alt itself is N/A on this slice
    (not an I-11 named alt)."""

    def __init__(self, acquirer_host_stub):
        self.acquirer_host = acquirer_host_stub

    def authorize(self, transaction_ref, amount, card):
        result = self.acquirer_host.authorize(transaction_ref, amount, card)
        if result["decision"] == "APPROVE":
            return "approved", result["auth_code"]
        return "declined", result.get("reason_code")

    def capture(self, transaction_ref, amount):
        result = self.acquirer_host.capture(transaction_ref, amount)
        return result["decision"] == "CAPTURE_OK"

    def refund(self, transaction_ref, amount):
        result = self.acquirer_host.refund(transaction_ref, amount)
        return result["decision"] == "REFUND_OK"

    def void(self, transaction_ref, amount):
        """Void of the uncaptured remainder on the Partial Capture alt
        (Lab 10 §2). Not the standalone Void Payment use case (N/A)."""
        result = self.acquirer_host.void(transaction_ref, amount)
        return result["decision"] == "VOID_OK"
