"""Query Store container (I-4). Read model for Payment Query (Lab 9 rel 3).

In the collapsed build this is an in-memory projection of Payment Store.
It returns Payment fields **without** full PAN — only card_ref (last 4 digits).
It NEVER writes Payment records (I-7: only Persistence Manager may write
Payment). It NEVER calls AcquirerHost (I-5).
"""


class QueryStore:
    """In-memory read model — stands for the Query Store container (I-4).
    Collapse: Database Tier read-replica (I-9 location)."""

    def __init__(self, payment_store):
        self._payment_store = payment_store

    def get(self, payment_id):
        """Returns a read-only projection or None. No PAN, no side effects."""
        payment = self._payment_store.load_payment(payment_id)
        if payment is None:
            return None
        return {
            "id": payment.id,
            "status": payment.status.name,
            "amount": payment.amount,
            "card_ref": payment.card_ref,  # last 4 only — never full PAN
            "merchant_id": payment.merchant_id,
            "captured_amount": payment.captured_amount,
            "refunded_amount": payment.refunded_amount,
            "refund_count": payment.refund_count,
            "created_at": payment.created_at,
        }
