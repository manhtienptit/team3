"""Persistence Manager module (Lab 3 §2). Writes Payment records to Payment
Store. Sole writer of Payment records (I-7) — enforced by PaymentStore."""


class PersistenceManager:
    def __init__(self, payment_store, clock):
        self.store = payment_store
        self.clock = clock

    def persist_new(self, payment):
        self.store.insert_payment(self, payment)

    def save(self, payment):
        self.store.update_payment(self, payment)

    def load(self, payment_id):
        return self.store.load_payment(payment_id)
