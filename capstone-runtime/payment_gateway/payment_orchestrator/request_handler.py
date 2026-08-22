"""Request Handler module (Lab 3 §2) — routes each flow.

Order of the authorize flow is the I-5 hard rule made structural:
idempotency check -> fraud gate -> acquirer call. There is no code path
that reaches Fraud Gate or Acquirer Client with an unchecked idempotency
key (asserted by tests).
"""

from ..payment import Payment
from .input_validator import ValidationError
from .idempotency_manager import IdempotencyConflict
from .fraud_gate import FraudBlocked
from .state_machine_engine import InvalidTransition

AUTH_WINDOW_SECONDS = 7 * 86400  # CON.4


class GatewayError(Exception):
    """Error crossing API Gateway -> Merchant Platform. status/body must
    match openapi.json exactly (G4)."""

    def __init__(self, status, code, message):
        super().__init__(message)
        self.status = status
        self.body = {"error": code, "message": message}


class RequestHandler:
    def __init__(self, validator, idempotency_manager, fraud_gate,
                 state_machine, acquirer_client, persistence_manager,
                 event_publisher, clock):
        self.validator = validator
        self.idempotency = idempotency_manager
        self.fraud_gate = fraud_gate          # auth path only (CON.3)
        self.state_machine = state_machine
        self.acquirer = acquirer_client
        self.persistence = persistence_manager
        self.events = event_publisher
        self.clock = clock
        self.order_log = []  # test spy for I-5 ordering assertions

    # ------------------------------------------------------------------ auth
    def authorize(self, body):
        amount, card = body["amount"], body["card"]
        capture = bool(body.get("capture", False))
        merchant_id = body.get("merchant_id", "mer_3")
        self.validator.validate(amount, card, self.clock())
        self.order_log.append("idempotency_check")
        outcome, cached = self.idempotency.check(body["idempotency_key"])
        if outcome == "cached":
            self.order_log.append("cached_response")
            return cached["status"], cached["body"]

        payment = Payment(amount, card["number"][-4:], merchant_id, capture,
                          body["idempotency_key"], self.clock())

        # CON.3: fraud gate on the authorization path only
        self.order_log.append("fraud_evaluate")
        try:
            self.fraud_gate.evaluate(card, amount, merchant_id)
        except FraudBlocked as block:
            self.order_log.append("fraud_blocked")
            payment.mark_declined("fraud_rule", fraud_rule=block.rule_id)
            self.persistence.persist_new(payment)
            response = (200, {"id": payment.id, "status": "declined",
                              "decline_reason": "fraud_rule",
                              "fraud_rule": block.rule_id})
            self._finish(body["idempotency_key"], response, payment,
                         "payment.declined")
            return response

        # Lab 10 §1 step 7: validateTransition(null -> Pending)
        self.state_machine.validate_transition(None, "Pending")

        self.order_log.append("acquirer_call")
        decision, auth_code = self.acquirer.authorize(
            payment.id, amount, card)
        if decision != "approved":
            payment.mark_declined("issuer_decline")
            self.persistence.persist_new(payment)
            response = (200, {"id": payment.id, "status": "declined",
                              "decline_reason": "issuer_decline"})
            self._finish(body["idempotency_key"], response, payment,
                         "payment.declined")
            return response

        if capture:  # Direct Charge: Pending -> Captured (I-6)
            self.acquirer.capture(payment.id, amount)
            payment.mark_captured(amount, self.clock())
            self.persistence.persist_new(payment)
            response = (200, {"id": payment.id, "status": "captured",
                              "captured_amount": amount})
            self._finish(body["idempotency_key"], response, payment,
                         "payment.captured")
            return response

        expires_at = self.clock() + AUTH_WINDOW_SECONDS
        payment.mark_authorized(auth_code, expires_at)
        self.persistence.persist_new(payment)
        response = (201, {"id": payment.id, "status": "authorized",
                          "auth_code": auth_code})
        self._finish(body["idempotency_key"], response, payment,
                     "payment.authorized")
        return response

    # ---------------------------------------------------------------- capture
    def capture(self, payment_id, body):
        self.order_log.append("idempotency_check")
        outcome, cached = self.idempotency.check(body["idempotency_key"])
        if outcome == "cached":
            return cached["status"], cached["body"]

        payment = self.persistence.load(payment_id)
        if payment is None:
            self.idempotency.release(body["idempotency_key"])
            raise GatewayError(404, "payment_not_found",
                               f"no payment with id {payment_id}")
        amount = body["amount"]
        try:
            self.state_machine.validate_capture(payment, amount, self.clock())
        except InvalidTransition as invalid:
            self.idempotency.release(body["idempotency_key"])
            raise GatewayError(
                409 if invalid.code in ("authorization_expired",
                                        "invalid_state_transition") else 400,
                invalid.code, invalid.message)

        self.order_log.append("acquirer_call")
        self.acquirer.capture(payment.id, amount)
        payment.add_capture(amount, self.clock())
        if amount < payment.amount:  # Partial Capture alt: void the remainder
            self.acquirer.void(payment.id, payment.amount - amount)
            payment.remainder_voided = True
        self.persistence.save(payment)
        response = (200, {"id": payment.id, "status": "captured",
                          "captured_amount": payment.captured_amount,
                          "remainder_voided": payment.remainder_voided})
        self._finish(body["idempotency_key"], response, payment,
                     "payment.captured")
        return response

    # ----------------------------------------------------------------- refund
    def refund(self, payment_id, body):
        self.order_log.append("idempotency_check")
        outcome, cached = self.idempotency.check(body["idempotency_key"])
        if outcome == "cached":
            return cached["status"], cached["body"]

        payment = self.persistence.load(payment_id)
        if payment is None:
            self.idempotency.release(body["idempotency_key"])
            raise GatewayError(404, "payment_not_found",
                               f"no payment with id {payment_id}")
        amount = body["amount"]
        try:
            self.state_machine.validate_refund(payment, amount, self.clock())
        except InvalidTransition as invalid:
            self.idempotency.release(body["idempotency_key"])
            raise GatewayError(
                409 if invalid.code in ("refund_window_expired",
                                        "invalid_state_transition") else 400,
                invalid.code, invalid.message)

        self.order_log.append("acquirer_call")
        self.acquirer.refund(payment.id, amount)
        payment.apply_refund(amount)
        self.persistence.save(payment)
        response = (200, {"id": payment.id, "status": payment.status.value,
                          "refunded_amount": payment.refunded_amount,
                          "refund_count": payment.refund_count})
        self._finish(body["idempotency_key"], response, payment,
                     "payment.refunded")
        return response

    # --------------------------------------------------------------- helpers
    def _finish(self, key, response, payment, event_type):
        """Cache the idempotent response, publish the event (async — webhook
        delivery happens on queue.drain(), never in the sync response path)."""
        self.idempotency.cache(key, {"status": response[0],
                                     "body": response[1]})
        self.events.publish(event_type, payment)

    def error_response(self, error):
        """Maps module-level exceptions to the OpenAPI error envelope."""
        if isinstance(error, ValidationError):
            return 400, {"error": error.code, "message": error.message}
        if isinstance(error, IdempotencyConflict):
            return 409, {"error": "idempotency_conflict",
                         "message": "idempotency key is in flight (CON.2)"}
        if isinstance(error, GatewayError):
            return error.status, error.body
        raise error
