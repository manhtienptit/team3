"""Webhook Service container (I-4). Async event delivery to Merchant Platform.

Consumes payment.* events from the Message Queue (on drain(), never inside
the synchronous API response — I-5), signs the payload HMAC-SHA256, and
delivers POST to the Merchant Platform mock (10s timeout stays a label; the
in-process fake returns immediately). Retry per CON.7: 7 attempts on the
1m/5m/30m/2h/12h/24h schedule (delays stay labels — no real waiting).

S1: The webhook signing secret is injected (from environment in production,
from test fixture in tests). It is NEVER hardcoded in source.

I-7 / I-9: writes only Webhook Event delivery-status rows. It never writes
Payment records; PaymentStore rejects that path (asserted by tests).
"""

import hashlib
import hmac
import json

MAX_ATTEMPTS = 7  # CON.7
RETRY_SCHEDULE = ("1m", "5m", "30m", "2h", "12h", "24h")  # CON.7 labels


class WebhookService:
    def __init__(self, message_queue, merchant_platform, payment_store,
                 signing_secret):
        self.merchant_platform = merchant_platform
        self.payment_store = payment_store
        self.signing_secret = signing_secret  # S1: injected, not hardcoded
        message_queue.subscribe(self.on_event)

    def on_event(self, event):
        """Queue subscriber (async). Signs + delivers + records status."""
        if self.signing_secret is None:
            raise RuntimeError(
                "S1: WEBHOOK_SECRET not configured — refusing to sign")
        payload = json.dumps(event, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(self.signing_secret, payload.encode(),
                             hashlib.sha256).hexdigest()
        attempts = 0
        delivered = False
        while attempts < MAX_ATTEMPTS:
            attempts += 1
            if self._deliver(payload, signature):
                delivered = True
                break
        self.payment_store.record_webhook_event(self, {
            "event_type": event["type"],
            "payment_id": event["payment_id"],
            "attempts": attempts,
            "status": "delivered" if delivered else "failed_delivery",
        })

    def _deliver(self, payload, signature):
        """POST webhook to Merchant Platform (10s timeout label, HMAC header)."""
        return self.merchant_platform.receive_webhook(payload, signature)
