---
inclusion: fileMatch
fileMatchPattern: "payment_gateway/payment_orchestrator/**"
---

# Payment Orchestrator Module Rules

When modifying Payment Orchestrator modules, enforce these constraints:

## I-5 Order (authorize flow)
The authorize flow MUST follow this exact order — no code path may reach a later step without passing through earlier ones:
1. `idempotency_check` (IdempotencyManager)
2. `fraud_evaluate` (FraudGate) — **authorize path only**
3. `acquirer_call` (AcquirerClient)

## CON.3: Fraud Gate scope
Fraud Gate evaluates ONLY on the authorize path. It must NEVER be called from:
- `capture()`
- `void()`
- `refund()`

The `fraud_gate.evaluations` spy count must not change on capture/void/refund.

## CON.6: Acquirer timeout handling
- `AcquirerClient` retries once (MAX_ATTEMPTS=2) with the SAME transaction reference
- If exhausted, `AcquirerExhausted` is raised
- RequestHandler catches it and transitions Pending → Failed
- Response: `(200, {"status": "Failed", "decline_reason": "acquirer_timeout"})`

## Response status = Title Case
All response dicts with a `"status"` key MUST use Title Case Lab 1 I-6 names.
