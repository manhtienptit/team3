"""Agent contract violation fixtures (A1–A10).

These are EXAMPLES of what a bad agent diff would look like. They must NEVER
be applied to the runtime. The checker (test_agent_contract.py) uses them to
prove the contract is machine-checkable.

Each fixture is a dict describing the violation so the checker can assert
rejection without importing or modifying runtime code.
"""

# A1: Invented use case — adds a route not in Lab 1
A1_INVENTED_ROUTE = {
    "method": "POST",
    "path": "/v1/3dsecure/authenticate",
    "body": {"idempotency_key": "3ds-key", "amount": 500000},
    "violation": "N1: 3D Secure is Lab 1 out of scope",
}

A1_TOKENIZE_ROUTE = {
    "method": "POST",
    "path": "/v1/payments/tokenize",
    "body": {"idempotency_key": "tok-key", "card_number": "4111111111111111"},
    "violation": "N1: Tokenization is Lab 1 out of scope",
}

# A2: Lowercase status on the wire (violates M2)
A2_LOWERCASE_AUTHORIZED = {
    "field": "status",
    "bad_value": "authorized",
    "correct_value": "Authorized",
    "violation": "M2: status must be Title Case on the wire",
}

A2_LOWERCASE_VOIDED = {
    "field": "status",
    "bad_value": "voided",
    "correct_value": "Voided",
    "violation": "M2: status must be Title Case on the wire",
}

A2_LOWERCASE_FAILED = {
    "field": "status",
    "bad_value": "failed",
    "correct_value": "Failed",
    "violation": "M2: status must be Title Case on the wire",
}

# A3: Secret default in source (violates M7 / S1)
A3_SECRET_DEFAULT = {
    "code": 'os.environ.get("WEBHOOK_SECRET", "simulated-webhook-secret")',
    "violation": "M7/S1: no getenv default for WEBHOOK_SECRET",
}

# A4: Pack edit (violates N4)
A4_PACK_PATHS = [
    "Lb/Lab1-Scopes.md",
    "Lb/before/Lab3-Register.md",
    "Lb/before/Lab6-TestSpec.md",
]

# A5: Expiry Job = Scheduler (M12)
A5_WRONG_I9 = {
    "wrong": "Worker Tier",
    "correct": "Scheduler",
    "context": "Expiry Job I-9 location",
}

# A6: Query Store writes Payment (violates N9 / M5)
A6_QUERY_STORE_WRITE = {
    "call": "payment_store.insert_payment(query_store, payment)",
    "violation": "N9/M5: Query Store must not write Payment",
}

# A7: Route with no spec-trace row (violates M10 / N10)
A7_UNTRACED_ROUTE = {
    "method": "POST",
    "path": "/v1/payments/{id}/dispute",
    "violation": "M10/N10: no spec-trace row for this route",
}

# A8: Real host (violates N6)
A8_REAL_HOST = {
    "url": "https://api.acquirer-bank.vn/v1/authorize",
    "violation": "N6: must not call a real host; I-3 must be mocked",
}

# A9: Leftover lowercase labels in spec-trace / README
A9_LEFTOVER_LABELS = {
    "wrong_patterns": ["200 declined", "200 captured", "200 refunded",
                       "200 voided", "200 failed"],
    "correct_patterns": ["200 Declined", "200 Captured", "200 Refunded",
                         "200 Voided", "200 Failed"],
    "violation": "M2/A9: OpenAPI column labels must be Title Case",
}

# A10: Human A — SA sign missing or stale
A10_SA_SIGN = {
    "required_field": "SA (A)",
    "required_content": "accepted",
    "violation": "M11/A10: SA must sign this sitting after tests pass",
}
