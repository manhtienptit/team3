"""Demo script (10-minute order per capstone.md):

I-1 goal -> one I-11 sequence on screen -> live happy path -> live named
alt / CON.* -> test report.

Run from capstone-runtime/:  python3 -m payment_gateway.demo
"""

import io
import unittest

from .runtime import PaymentGatewayRuntime

GOAL = ("Enable merchants to accept online card payments (Visa/MC) via a "
        "single API with fraud protection and reliable webhook notification")
OUTCOME = ("Process 500 TPS authorization with P95 < 2s; 99.9% uptime; "
           "zero duplicate charges via idempotency")

CARD = {"number": "4111111111111111", "exp_month": 12, "exp_year": 2030,
        "bin_country": "VN"}

SEQUENCE = [
    ("Merchant Platform", "API Gateway", "POST /v1/payments"),
    ("API Gateway", "Request Handler", "forward validated request"),
    ("Request Handler", "Input Validator", "validate(amount, card) [CON.1]"),
    ("Request Handler", "Idempotency Manager", "check(idempotency_key) [CON.2]"),
    ("Idempotency Manager", "Idempotency Store", "GET/SET idempotency key"),
    ("Request Handler", "Fraud Gate", "evaluate(card, amount, merchant) [CON.3]"),
    ("Request Handler", "State Machine Engine", "validateTransition(null -> Pending)"),
    ("Request Handler", "Acquirer Client", "authorize(card_ref, amount) [CON.6 labels]"),
    ("Acquirer Client", "AcquirerHost", "HTTPS authorize (mocked I-3)"),
    ("Request Handler", "Persistence Manager", "persist(Payment{Authorized}) [CON.4 7d]"),
    ("Request Handler", "Event Publisher", "publish(payment.authorized)"),
    ("API Gateway", "Merchant Platform", "201 Authorized"),
    ("Message Queue", "Webhook Service", "consume event (async)"),
    ("Webhook Service", "Merchant Platform", "POST webhook, HMAC-SHA256 (async)"),
]


def line(title):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def main():
    runtime = PaymentGatewayRuntime(clock=lambda: 1_700_000_000)

    line("1) I-1 GOAL (Lab 1 string)")
    print(f"Goal    : {GOAL}")
    print(f"Outcome : {OUTCOME}")

    line("2) ONE I-11 SEQUENCE ON SCREEN — Authorize Payment (Lab 10 §1 names)")
    for step, (src, dst, message) in enumerate(SEQUENCE, 1):
        print(f"  {step:2d}. {src:<22} -> {dst:<22} {message}")

    line("3) LIVE HAPPY PATH — POST /v1/payments (capture: false)")
    status, body = runtime.handle("POST", "/v1/payments", {
        "amount": 500000, "card": dict(CARD), "idempotency_key": "demo-happy",
        "capture": False})
    print(f"  response           : {status} {body}")
    payment = runtime.payment_store.load_payment(body["id"])
    print(f"  Payment Store row  : status={payment.status.value} "
          f"expiresAt=+{payment.expires_at - payment.created_at}s (CON.4)")
    print(f"  queue (async)      : {[e['type'] for e in runtime.message_queue.pending()]}")
    runtime.drain_webhooks()
    delivery = runtime.merchant_platform.deliveries[0]
    print(f"  webhook delivered  : valid_signature="
          f"{delivery['valid_signature']} (HMAC-SHA256)")

    line("4) LIVE NAMED ALT / CON.* — Fraud blocks -> Declined (no acquirer call)")
    runtime.acquirer_host.calls.clear()
    status, body = runtime.handle("POST", "/v1/payments", {
        "amount": 250_000_000, "card": dict(CARD),
        "idempotency_key": "demo-fraud"})
    print(f"  response           : {status} {body}")
    declined = runtime.payment_store.load_payment(body["id"])
    print(f"  compensating action: Payment persisted "
          f"{declined.status.value} (fraud_rule={declined.fraud_rule})")
    print(f"  acquirer calls     : {runtime.acquirer_host.calls}  <- empty (G5)")

    line("5) TEST REPORT — python3 -m unittest discover -s tests -t .")
    suite = unittest.defaultTestLoader.discover("tests", top_level_dir=".")
    report = io.StringIO()
    result = unittest.TextTestRunner(stream=report, verbosity=0).run(suite)
    print(report.read().strip())
    print(f"  tests run={result.testsRun} failures={len(result.failures)} "
          f"errors={len(result.errors)}")
    print("  RESULT: OK" if result.wasSuccessful() else "  RESULT: FAILED")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
