"""Expiry Job container (I-4). Hourly tick that expires Authorized payments.

CON.4: expiresAt <= now and status Authorized -> Failed (I-6 #8).
Lab 9 rel 10: Expiry Job -> Payment Store (write the Failed transition).
Lab 9 rel 11: Expiry Job -> Message Queue (publish payment.failed).
Webhook delivery is async (Message Queue -> Webhook Service on drain).

In the collapsed build this is an in-process function `tick(now)` called by
the runtime (or by the demo script on a simulated clock). It does NOT write
Webhook Event rows (I-7: only Webhook Service owns those).
"""


class ExpiryJob:
    """Scans Payment Store for expired authorizations and transitions them
    to Failed. Writes via Payment Store directly (Lab 9 rel 10 — Expiry Job
    is allowed to write Payment for the CON.4 transition)."""

    def __init__(self, payment_store, message_queue):
        self._payment_store = payment_store
        self._message_queue = message_queue

    def tick(self, now):
        """Run one sweep. Returns list of expired payment ids (for testing)."""
        expired = []
        for payment in self._payment_store.all_payments():
            if payment.status.value != "authorized":
                continue
            if payment.expires_at is not None and now >= payment.expires_at:
                payment.mark_failed()
                self._payment_store.update_payment_by_expiry_job(self, payment)
                self._message_queue.publish({
                    "type": "payment.failed",
                    "payment_id": payment.id,
                    "status": "failed",
                    "amount": payment.amount,
                    "occurred_at": now,
                })
                expired.append(payment.id)
        return expired
