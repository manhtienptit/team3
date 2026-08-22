"""Event Publisher module (Lab 3 §2). Publishes payment.* events to Message
Queue (async, in-process bus)."""


class EventPublisher:
    def __init__(self, message_queue):
        self.queue = message_queue

    def publish(self, event_type, payment):
        self.queue.publish({
            "type": event_type,             # payment.authorized / .declined / .captured / .refunded
            "payment_id": payment.id,
            "status": payment.status.name,
            "amount": payment.amount,
            "occurred_at": payment.captured_at or payment.created_at,
        })
