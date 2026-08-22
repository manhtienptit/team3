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

    # -- transition operations: every Payment state change in this runtime
    #    goes through one of these. Payment.mark_* ops are private to the
    #    engine (Lab 3 §2: "Enforces valid transitions; rejects invalid
    #    with 409"). --

    def to_authorized(self, payment, auth_code, expires_at):
        """Pending -> Authorized (issuer approved, capture:false)."""
        self.validate_transition(payment.status.name, "Authorized")
        payment.mark_authorized(auth_code, expires_at)

    def to_captured_direct(self, payment, amount, now):
        """Pending -> Captured (Direct Charge, I-6 #2)."""
        self.validate_transition(payment.status.name, "Captured")
        payment.mark_captured(amount, now)

    def to_declined(self, payment, reason, fraud_rule=None):
        """Pending -> Declined (fraud block or issuer decline)."""
        self.validate_transition(payment.status.name, "Declined")
        payment.mark_declined(reason, fraud_rule)

    def commit_capture(self, payment, amount, now):
        """Authorized -> Captured, after AcquirerHost CAPTURE_OK. Guards the
        payment's actual state, not just the caller's intent."""
        if payment.status.value != "authorized":
            raise InvalidTransition(
                "invalid_state_transition",
                "capture commit requires status Authorized (I-6)")
        self.validate_transition("Authorized", "Captured")
        payment.mark_captured(amount, now)

    def commit_refund(self, payment, amount):
        """Captured -> Captured (partial) or Captured -> Refunded (full),
        after AcquirerHost REFUND_OK. Both targets are valid from Captured."""
        if payment.status.value != "captured":
            raise InvalidTransition(
                "invalid_state_transition",
                "refund commit requires status Captured (I-6)")
        self.validate_transition("Captured", "Captured")
        self.validate_transition("Captured", "Refunded")
        payment.apply_refund(amount)

    # -- pre-checks (raise the OpenAPI error codes; run BEFORE the
    #    acquirer call so invalid requests never reach AcquirerHost) --

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
