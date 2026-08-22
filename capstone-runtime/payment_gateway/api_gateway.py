"""API Gateway container (I-4). Routing + request envelope checks; forwards
validated requests to Payment Orchestrator over the Lab 9 relationship
"Forward validated request [sync]".

Only the three in-scope I-11 routes exist. Any other path — including the
N/A Void Payment and Payment Query use cases — returns 404 not_found, so no
out-of-scope path is callable.
"""


class APIGateway:
    def __init__(self, request_handler):
        self.request_handler = request_handler

    def handle(self, method, path, body):
        """Returns (status, body-dict) for every call; never raises outward."""
        if method == "POST" and path == "/v1/payments":
            problem = self._require(body, ("idempotency_key", "amount", "card"))
            if problem:
                return problem
            return self._guard(self.request_handler.authorize, body)
        parts = path.split("/")
        if method == "POST" and len(parts) == 5 and parts[4] == "capture":
            problem = self._require(body, ("idempotency_key", "amount"))
            if problem:
                return problem
            return self._guard(self.request_handler.capture, parts[3], body)
        if method == "POST" and len(parts) == 5 and parts[4] == "refund":
            problem = self._require(body, ("idempotency_key", "amount"))
            if problem:
                return problem
            return self._guard(self.request_handler.refund, parts[3], body)
        return 404, {"error": "not_found",
                     "message": f"no route for {method} {path}"}

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
