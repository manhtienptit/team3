"""In-memory stores (documented collapse of I-4 data containers, see name-map.md).

I-7 ownership is enforced here:
  - Persistence Manager (Payment Orchestrator) may write Payment records;
  - Expiry Job may write Payment records (Lab 9 rel 10, CON.4 transition only);
  - Webhook Service may write only Webhook Event rows.
The I-9 forbidden paths (Webhook Service writing Payment, Query Store writing
Payment) raise instead of silently succeeding.
"""

import threading


class IdempotencyStore:
    """I-4 Idempotency Store — in-memory stand-in for Redis (Cache Tier).

    Owns Idempotency Entries and Fraud Counters (I-7).
    """

    def __init__(self):
        self._entries = {}
        self._locks = set()
        self._fraud_counters = {}

    def get(self, key):
        return self._entries.get(key)

    def set(self, key, response):
        self._entries[key] = response

    def try_lock(self, key):
        if key in self._locks or key in self._entries:
            return False
        self._locks.add(key)
        return True

    def unlock(self, key):
        self._locks.discard(key)

    # Fraud counters (I-7: Fraud Counters live in Idempotency Store)
    def bump_counter(self, name, by=1, window=3600):
        self._fraud_counters[name] = self._fraud_counters.get(name, 0) + by
        return self._fraud_counters[name]

    def get_counter(self, name):
        return self._fraud_counters.get(name, 0)


class PaymentStore:
    """I-4 Payment Store — in-memory stand-in for PostgreSQL primary.

    Source of truth for Payment and Webhook Event (I-7).
    """

    def __init__(self):
        self._payments = {}
        self._webhook_events = []
        self._lock = threading.Lock()

    # -- Payment records: owner = Persistence Manager (Payment Orchestrator) --
    def insert_payment(self, caller, payment):
        self._require_payment_writer(caller)
        with self._lock:
            self._payments[payment.id] = payment

    def update_payment(self, caller, payment):
        self._require_payment_writer(caller)
        with self._lock:
            self._payments[payment.id] = payment

    # -- Expiry Job write path (Lab 9 rel 10: CON.4 transition) --
    def update_payment_by_expiry_job(self, caller, payment):
        """Only Expiry Job may call this (I-7: CON.4 transition)."""
        from .expiry_job import ExpiryJob
        if not isinstance(caller, ExpiryJob):
            raise PermissionError(
                "I-7: only Expiry Job may write Payment via this path")
        with self._lock:
            self._payments[payment.id] = payment

    def load_payment(self, payment_id):
        return self._payments.get(payment_id)

    def all_payments(self):
        """Returns all payment objects (for Expiry Job scan)."""
        return list(self._payments.values())

    # -- Webhook Event rows: owner = Webhook Service (I-7) --
    def record_webhook_event(self, caller, event):
        self._require_webhook_service(caller)
        self._webhook_events.append(event)

    def webhook_events(self):
        return list(self._webhook_events)

    @staticmethod
    def _require_payment_writer(caller):
        """I-7 / I-9: only Persistence Manager or Expiry Job may write
        Payment records. All others are forbidden paths."""
        from .payment_orchestrator.persistence_manager import PersistenceManager
        from .expiry_job import ExpiryJob
        if not isinstance(caller, (PersistenceManager, ExpiryJob)):
            raise PermissionError(
                "I-9 forbidden path: only Persistence Manager (Payment "
                "Orchestrator) or Expiry Job may write Payment records")

    @staticmethod
    def _require_webhook_service(caller):
        from .webhook_service import WebhookService
        if not isinstance(caller, WebhookService):
            raise PermissionError(
                "I-7: only Webhook Service may write Webhook Event rows")


class MessageQueue:
    """I-4 Message Queue — in-process bus (Queue Tier stand-in).

    At-least-once, ordered per payment. Delivery is deferred to `drain()`
    so webhook delivery can never block the synchronous API response (I-5).
    """

    def __init__(self):
        self._pending = []
        self._subscriber = None

    def publish(self, event):
        self._pending.append(event)

    def subscribe(self, subscriber):
        self._subscriber = subscriber

    def drain(self):
        while self._pending:
            event = self._pending.pop(0)
            if self._subscriber:
                self._subscriber(event)

    def pending(self):
        return list(self._pending)
