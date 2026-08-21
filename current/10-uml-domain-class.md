# 10 - UML Domain Class

**Title:** Domain Class - Payment  
**Viewpoint:** UML Class  
**Layer(s):** Application / Domain  
**As-Is | To-Be | Transition:** To-Be  
**Owner:** Dev - Team 3  
**RACI:** R Dev, A SA, C DA/BA/Test, I Owner/Ops  
**Version:** v1.0.0  **Date:** 2026-08-21  **Status:** Draft  
**Legend:** composition means owned data; association means related domain record.  
**Scope:** Payment, PaymentMethod, WebhookEvent, FraudRule; no implementation.

```mermaid
+classDiagram
+  class Payment {
+    id
+    idempotencyKey
+    amount
+    capturedAmount
+    refundedAmount
+    status
+    authCode
+  }
+  class PaymentMethod {
+    type
+    maskedDetails
+  }
+  class WebhookEvent {
+    paymentId
+    eventType
+    deliveryStatus
+    attempts
+  }
+  class FraudRule {
+    id
+    ruleType
+    action
+  }
+  Payment *-- PaymentMethod
+  Payment --> WebhookEvent : triggers
+  Payment --> FraudRule : evaluated by
+```
+
+Invariant: Payment has exactly one allowed lifecycle status; refundedAmount never exceeds capturedAmount; idempotencyKey identifies one write result.
