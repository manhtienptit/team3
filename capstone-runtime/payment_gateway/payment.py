"""I-6 named object: Payment.

States and transitions are Lab 1 I-6 exactly (one spelling per thing).
State transitions are operations on this type; validity is enforced by the
State Machine Engine (a collaborator inside Payment Orchestrator), never by
ad-hoc scripts.
"""

import itertools
from enum import Enum


class PaymentState(Enum):
    Pending = "pending"
    Authorized = "authorized"
    Captured = "captured"
    Voided = "voided"
    Refunded = "refunded"
    Declined = "declined"
    Failed = "failed"


TERMINAL_STATES = {PaymentState.Voided, PaymentState.Refunded,
                   PaymentState.Declined, PaymentState.Failed}

_ids = itertools.count(1)


class Payment:
    """Aggregate root. Source of truth rows live in Payment Store (I-7)."""

    def __init__(self, amount, card_ref, merchant_id, capture, idempotency_key,
                 now):
        self.id = f"pay_{next(_ids):08d}"
        self.amount = amount
        self.card_ref = card_ref
        self.merchant_id = merchant_id
        self.capture_requested = capture
        self.idempotency_key = idempotency_key
        self.status = PaymentState.Pending
        self.created_at = now
        self.auth_code = None
        self.expires_at = None
        self.captured_amount = 0
        self.captured_at = None
        self.refunded_amount = 0
        self.refund_count = 0
        self.fraud_rule = None
        self.decline_reason = None
        self.remainder_voided = False

    # ---- transition operations (I-6); each asserts the resulting state ----

    def mark_authorized(self, auth_code, expires_at):
        self.status = PaymentState.Authorized
        self.auth_code = auth_code
        self.expires_at = expires_at

    def mark_captured(self, amount, now):
        self.status = PaymentState.Captured
        self.captured_amount = amount
        self.captured_at = now

    def add_capture(self, amount, now):
        """Authorized -> Captured (capture of an existing authorization)."""
        self.status = PaymentState.Captured
        self.captured_amount = amount
        self.captured_at = now

    def mark_declined(self, reason, fraud_rule=None):
        self.status = PaymentState.Declined
        self.decline_reason = reason
        self.fraud_rule = fraud_rule

    def mark_failed(self):
        self.status = PaymentState.Failed

    def mark_voided(self):
        self.status = PaymentState.Voided

    def apply_refund(self, amount):
        """Captured -> Captured (partial) or Captured -> Refunded (full)."""
        self.refunded_amount += amount
        self.refund_count += 1
        if self.refunded_amount == self.captured_amount:
            self.status = PaymentState.Refunded
