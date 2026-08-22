"""State Machine Engine module (Lab 3 §2). Enforces I-6 transitions.

Every check raises InvalidTransition with the exact error code named in
Lab 10 (authorization_expired, amount_exceeds_authorized,
invalid_state_transition, max_refunds_exceeded, refund_window_expired,
amount_exceeds_refundable) so the runtime body matches OpenAPI.
"""


class InvalidTransition(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class StateMachineEngine:
    AUTH_WINDOW_SECONDS = 7 * 86400        # CON.4
    MAX_PARTIAL_REFUNDS = 10               # CON.5
    REFUND_WINDOW_SECONDS = 180 * 86400    # CON.5

    def validate_transition(self, from_state, to_state):
        """Lab 10 §1 step 7: validateTransition(null -> Pending) on the
        authorize path. Creation (None) may only produce Pending."""
        allowed = {
            ("Pending", "Authorized"), ("Pending", "Captured"),
            ("Pending", "Declined"), ("Pending", "Failed"),
            ("Authorized", "Captured"), ("Authorized", "Voided"),
            ("Authorized", "Failed"),
            ("Captured", "Refunded"), ("Captured", "Captured"),
        }
        if from_state is None and to_state == "Pending":
            return
        if (from_state, to_state) not in allowed:
            raise InvalidTransition(
                "invalid_state_transition",
                f"transition {from_state} -> {to_state} is not valid (I-6)")

    def validate_capture(self, payment, amount, now):
        if payment.status.value != "authorized":
            raise InvalidTransition(
                "invalid_state_transition",
                "capture requires status Authorized (I-6)")
        if payment.expires_at is not None and now >= payment.expires_at:
            raise InvalidTransition(
                "authorization_expired",
                "authorization expired after 7 calendar days (CON.4)")
        if amount > payment.amount:
            raise InvalidTransition(
                "amount_exceeds_authorized",
                "capture amount exceeds authorized amount")

    def validate_refund(self, payment, amount, now):
        if payment.status.value != "captured":
            raise InvalidTransition(
                "invalid_state_transition",
                "refund requires status Captured (I-6)")
        if payment.refund_count >= self.MAX_PARTIAL_REFUNDS:
            raise InvalidTransition(
                "max_refunds_exceeded",
                "maximum 10 partial refunds per payment (CON.5)")
        if amount > payment.captured_amount - payment.refunded_amount:
            raise InvalidTransition(
                "amount_exceeds_refundable",
                "refund amount exceeds refundable remainder")
        if now >= payment.captured_at + self.REFUND_WINDOW_SECONDS:
            raise InvalidTransition(
                "refund_window_expired",
                "refund window of 180 days has expired (CON.5)")
