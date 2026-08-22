"""Demo script — 12-minute capstone+ extension demo.

Order per extension spec:
1. I-1 goal
2. One Lab 9 sequence on screen (Payment Query or Expiry)
3. Live Query happy path
4. Live Void happy path
5. Live Expiry Job (Authorized → Failed)
6. Live CON.6 timeout (Pending → Failed, same ref)
7. Live named security attempt (S8 Query Store write → PermissionError)
8. Test report
"""

import subprocess
import sys

from .runtime import PaymentGatewayRuntime

AUTH_WINDOW = 7 * 86400
T0 = 1_700_000_000


def main():
    t = {"now": T0}
    rt = PaymentGatewayRuntime(clock=lambda: t["now"],
                               webhook_secret="demo-secret")

    def sep(n, title):
        print("=" * 70)
        print(f"{n}) {title}")
        print("=" * 70)

    # 1. I-1 GOAL
    sep(1, "I-1 GOAL (Lab 1 string)")
    print("Goal    : Enable merchants to accept online card payments (Visa/MC) "
          "via a single API with fraud protection and reliable webhook "
          "notification")
    print("Outcome : Process 500 TPS authorization with P95 < 2s; 99.9% "
          "uptime; zero duplicate charges via idempotency")

    # 2. ONE SEQUENCE ON SCREEN — Payment Query (Lab 9 rel 3)
    sep(2, "ONE SEQUENCE ON SCREEN — Payment Query (Lab 9 rel 3)")
    print("   1. Merchant Platform      -> API Gateway            "
          "GET /v1/payments/{id}")
    print("   2. API Gateway            -> Rate Limiter           "
          "allow(merchant_id)")
    print("   3. API Gateway            -> Query Store            "
          "get(payment_id) [Lab 9 rel 3]")
    print("   4. Query Store            -> Payment Store          "
          "load_payment(id) [read-only projection]")
    print("   5. API Gateway            -> Merchant Platform      "
          "200 {id, status, amount, card_ref(last4)}")
    print()
    print("   Note: Query Store NEVER calls AcquirerHost (I-5/S4).")
    print("   Note: card_ref = last 4 digits only; full PAN never stored (S3).")

    # 3. LIVE QUERY HAPPY PATH
    sep(3, "LIVE QUERY HAPPY PATH — GET /v1/payments/{id}")
    card = {"number": "4111111111111111", "exp_month": 12, "exp_year": 2030,
            "bin_country": "VN"}
    status, body = rt.handle("POST", "/v1/payments",
                             {"amount": 500000, "card": card,
                              "idempotency_key": "demo-auth-1"})
    print(f"  authorize        : {status} {body}")
    payment_id = body["id"]
    status, body = rt.handle("GET", f"/v1/payments/{payment_id}", {})
    print(f"  GET response     : {status} {body}")
    print(f"  card_ref (last4) : {body['card_ref']!r} (full PAN absent — S3)")

    # 4. LIVE VOID HAPPY PATH
    sep(4, "LIVE VOID HAPPY PATH — POST /v1/payments/{id}/void")
    status, body = rt.handle("POST", "/v1/payments",
                             {"amount": 300000, "card": card,
                              "idempotency_key": "demo-auth-2"})
    void_id = body["id"]
    print(f"  authorize        : {status} {body}")
    status, body = rt.handle("POST", f"/v1/payments/{void_id}/void",
                             {"idempotency_key": "demo-void-1"})
    print(f"  void response    : {status} {body}")
    payment = rt.payment_store.load_payment(void_id)
    print(f"  Payment Store    : status={payment.status.value}")
    print(f"  acquirer calls   : {[c for c in rt.acquirer_host.calls if c[1] == void_id]}")

    # 5. LIVE EXPIRY JOB — Authorized → Failed
    sep(5, "LIVE EXPIRY JOB — tick(now) with expired authorization")
    status, body = rt.handle("POST", "/v1/payments",
                             {"amount": 200000, "card": card,
                              "idempotency_key": "demo-auth-3"})
    expiry_id = body["id"]
    print(f"  authorize        : {status} {body}")
    t["now"] = T0 + AUTH_WINDOW + 1
    expired = rt.tick_expiry()
    print(f"  tick(now={t['now']}) expired: {expired}")
    payment = rt.payment_store.load_payment(expiry_id)
    print(f"  Payment Store    : status={payment.status.value} (was authorized)")
    events = rt.message_queue.pending()
    failed_events = [e for e in events if e.get("type") == "payment.failed"]
    print(f"  payment.failed event queued: {len(failed_events) > 0}")
    t["now"] = T0  # reset

    # 6. LIVE CON.6 TIMEOUT — Pending → Failed (same ref)
    sep(6, "LIVE CON.6 TIMEOUT — acquirer exhaust → Pending → Failed")
    rt.acquirer_host.timeout_next_n = 99
    status, body = rt.handle("POST", "/v1/payments",
                             {"amount": 400000, "card": card,
                              "idempotency_key": "demo-auth-4"})
    print(f"  response         : {status} {body}")
    timeout_id = body["id"]
    auth_calls = [c for c in rt.acquirer_host.calls
                  if c[0] == "authorize" and c[1] == timeout_id]
    print(f"  acquirer calls   : {auth_calls}")
    refs = set(c[1] for c in auth_calls)
    print(f"  transaction refs : {refs} (same ref — no dup charge, S11)")
    print(f"  Payment status   : {rt.payment_store.load_payment(timeout_id).status.value}")
    rt.acquirer_host.timeout_next_n = 0

    # 7. LIVE NAMED SECURITY ATTEMPT — S8 Query Store cannot write Payment
    sep(7, "LIVE SECURITY ATTEMPT — S8 Query Store write → PermissionError")
    payment = rt.payment_store.load_payment(payment_id)
    try:
        rt.payment_store.insert_payment(rt.query_store, payment)
        print("  ERROR: should have raised!")
    except PermissionError as e:
        print(f"  PermissionError  : {e}")
        print("  (Query Store is read-only — I-7 enforced)")

    # 8. TEST REPORT
    sep(8, "TEST REPORT — python3 -m unittest discover -s tests -t .")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
        capture_output=True, text=True,
        cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
        env={**__import__("os").environ, "WEBHOOK_SECRET": "demo-secret"})
    # Parse last line for summary
    lines = result.stderr.strip().split("\n")
    for line in lines[-3:]:
        print(f"  {line}")
    ok = result.returncode == 0
    print(f"  RESULT: {'OK' if ok else 'FAILED'}")


if __name__ == "__main__":
    main()
