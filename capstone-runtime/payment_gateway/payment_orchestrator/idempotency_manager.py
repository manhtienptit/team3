"""Idempotency Manager module (Lab 3 §2). CON.2.

Hard rule (I-5): the idempotency check ALWAYS runs before fraud evaluation
and before any acquirer call — Request Handler enforces the order and the
order is asserted by tests.
"""


class IdempotencyConflict(Exception):
    pass


class IdempotencyManager:
    TTL_SECONDS = 172800  # CON.2: 48h

    def __init__(self, idempotency_store):
        self.store = idempotency_store

    def check(self, key):
        """Returns ('cached', response) for a duplicate, ('new', None) after
        acquiring the lock, raises IdempotencyConflict if locked in-flight."""
        cached = self.store.get(key)
        if cached is not None:
            return "cached", cached
        if not self.store.try_lock(key):
            raise IdempotencyConflict("idempotency_conflict")
        return "new", None

    def cache(self, key, response):
        self.store.unlock(key)
        self.store.set(key, response)

    def release(self, key):
        self.store.unlock(key)
