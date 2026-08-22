"""API Gateway container (I-4). Routing + request envelope checks + rate
limiting (I-4 named responsibility); forwards validated requests to Payment
Orchestrator over the Lab 9 relationship "Forward validated request [sync]".

The in-scope routes are the 3 original I-11 use cases + Void Payment +
Payment Query (extension sitting). Any other path returns 404 not_found.
"""

import os

# ASSUMPTION: 100 requests / merchant / 60s (name-map §4)
RATE_LIMIT_CAP = int(os.environ.get("RATE_LIMIT_CAP", "100"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))


class RateLimiter:
    """Per-merchant rate limiter (ASSUMPTION: 100 req/merchant/60s).
    Uses a simple sliding-window counter in the collapsed build."""

    def __init__(self, cap, window, clock):
        self.cap = cap
        self.window = window
        self.clock = clock
        self._buckets = {}  # merchant_id -> [(timestamp, ...)]

    def allow(self, merchant_id):
        now = self.clock()
        bucket = self._buckets.setdefault(merchant_id, [])
        # Evict expired entries
        cutoff = now - self.window
        self._buckets[merchant_id] = [t for t in bucket if t > cutoff]
        bucket = self._buckets[merchant_id]
        if len(bucket) >= self.cap:
            return False
        bucket.append(now)
        return True


class APIGateway:
    def __init__(self, request_handler, query_store, clock):
        self.request_handler = request_handler
        self.query_store = query_store
        self.rate_limiter = RateLimiter(RATE_LIMIT_CAP, RATE_LIMIT_WINDOW,
                                        clock)

    def handle(self, method, path, body):
        """Returns (status, body-dict) for every call; never raises outward."""
        # Rate limiting (S9): extract merchant_id from body or use default
        merchant_id = (body or {}).get("merchant_id", "mer_3")
        if not self.rate_limiter.allow(merchant_id):
            return 429, {"error": "rate_limit_exceeded",
                         "message": "too many requests from this merchant "
                                    f"(limit: {RATE_LIMIT_CAP}/{RATE_LIMIT_WINDOW}s)"}

        if method == "POST" and path == "/v1/payments":
            problem = self._require(body, ("idempotency_key", "amount", "card"))
            if problem:
                return problem
            return self._guard(self.request_handler.authorize, body)

        parts = path.split("/")

        if method == "GET" and len(parts) == 4 and parts[1] == "v1" \
                and parts[2] == "payments":
            # Payment Query: GET /v1/payments/{id} -> Query Store (Lab 9 rel 3)
            return self._query(parts[3])

        if method == "POST" and len(parts) == 5 and parts[4] == "capture":
            problem = self._require(body, ("idempotency_key", "amount"))
            if problem:
                return problem
            return self._guard(self.request_handler.capture, parts[3], body)

        if method == "POST" and len(parts) == 5 and parts[4] == "void":
            problem = self._require(body, ("idempotency_key",))
            if problem:
                return problem
            return self._guard(self.request_handler.void, parts[3], body)

        if method == "POST" and len(parts) == 5 and parts[4] == "refund":
            problem = self._require(body, ("idempotency_key", "amount"))
            if problem:
                return problem
            return self._guard(self.request_handler.refund, parts[3], body)

        return 404, {"error": "not_found",
                     "message": f"no route for {method} {path}"}

    def _query(self, payment_id):
        """Payment Query — served by Query Store (I-4, Lab 9 rel 3).
        Never calls AcquirerHost (I-5). Returns card_ref (last 4), not PAN."""
        result = self.query_store.get(payment_id)
        if result is None:
            return 404, {"error": "payment_not_found",
                         "message": f"no payment with id {payment_id}"}
        return 200, result

    @staticmethod
    def _require(body, fields):
        """CON.2: idempotency key required on all POST (string, max 64 chars).
        Other missing required fields get the same 400 invalid_request."""
        missing = [f for f in fields if f not in body]
        if missing:
            return 400, {"error": "invalid_request",
                         "message": "missing required field(s): "
                                    + ", ".join(missing)}
        key = body["idempotency_key"]
        if not isinstance(key, str) or not (1 <= len(key) <= 64):
            return 400, {"error": "invalid_request",
                         "message": "idempotency_key must be a string of "
                                    "1-64 chars (CON.2)"}
        return None

    def _guard(self, flow, *args):
        try:
            return flow(*args)
        except Exception as error:  # noqa: BLE001 - single error envelope
            return self.request_handler.error_response(error)
