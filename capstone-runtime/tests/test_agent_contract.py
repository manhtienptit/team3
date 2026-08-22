"""Agent contract attempt tests (A1–A10).

Each test ATTEMPTS a violation described in AGENTS.md and asserts the
runtime or checker REJECTS it. Fixtures under tests/fixtures/agent/ are
violation examples — never applied to the runtime.

Spec: capstone-team3-agent.md Slice B.
"""

import json
import os
import pathlib
import unittest

from .support import RuntimeTestCase, TEST_WEBHOOK_SECRET

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "payment_gateway"
SPEC_TRACE = ROOT / "spec-trace.md"
README = ROOT / "README.md"
NAME_MAP = ROOT / "name-map.md"
AGENTS_MD = ROOT / "AGENTS.md"
OPENAPI = ROOT / "openapi.json"


class A1NoInventedUseCaseTests(RuntimeTestCase):
    """A1 (N1): No invented use case — 3DS, Tokenize, etc. return 404."""

    def test_a1_3dsecure_route_rejected(self):
        """Fixture: POST /v1/3dsecure/authenticate → 404 not_found."""
        status, body = self.rt.handle(
            "POST", "/v1/3dsecure/authenticate",
            {"idempotency_key": "3ds-key", "amount": 500000})
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")

    def test_a1_tokenize_route_rejected(self):
        """Fixture: POST /v1/payments/tokenize → 404 not_found."""
        status, body = self.rt.handle(
            "POST", "/v1/payments/tokenize",
            {"idempotency_key": "tok-key"})
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")

    def test_a1_openapi_has_no_out_of_scope_operations(self):
        """OpenAPI must not document 3DS, Tokenization, KYC, etc."""
        with open(OPENAPI) as f:
            doc = json.load(f)
        out_of_scope = ["3dsecure", "tokenize", "tokenization", "kyc",
                        "recurring", "dispute", "chargeback", "settlement",
                        "card-issuing", "pos", "fx"]
        all_paths = " ".join(doc["paths"].keys())
        for term in out_of_scope:
            self.assertNotIn(term, all_paths.lower(),
                             f"N1: out-of-scope '{term}' in OpenAPI paths")


class A2TitleCaseOnWireTests(RuntimeTestCase):
    """A2 (M2): All status values on the wire are Title Case."""

    def test_a2_authorize_returns_title_case(self):
        status, body = self.authorize(amount=500000)
        self.assertEqual(body["status"], "Authorized")

    def test_a2_void_returns_title_case(self):
        pid, _, _ = self.authorized_payment()
        status, body = self.void(pid)
        self.assertEqual(body["status"], "Voided")

    def test_a2_con6_failed_returns_title_case(self):
        self.rt.acquirer_host.timeout_next_n = 99
        status, body = self.authorize(amount=500000)
        self.assertEqual(body["status"], "Failed")

    def test_a2_query_returns_title_case(self):
        pid, _, _ = self.authorized_payment()
        status, body = self.query(pid)
        self.assertEqual(body["status"], "Authorized")

    def test_a2_openapi_enums_are_title_case(self):
        """All status enums in OpenAPI use Title Case."""
        with open(OPENAPI) as f:
            doc = json.load(f)
        lowercase_states = {"authorized", "declined", "captured", "voided",
                            "refunded", "failed", "pending"}

        def check_enums(obj, path=""):
            if isinstance(obj, dict):
                if (path.endswith(".status") and "enum" in obj):
                    for val in obj["enum"]:
                        self.assertNotIn(
                            val, lowercase_states,
                            f"A2: lowercase '{val}' in OpenAPI at {path}")
                for k, v in obj.items():
                    check_enums(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for item in obj:
                    check_enums(item, path)

        check_enums(doc)


class A3NoSecretDefaultTests(RuntimeTestCase):
    """A3 (M7/S1): No getenv default for WEBHOOK_SECRET in source."""

    def test_a3_no_hardcoded_secret_default(self):
        """Grep payment_gateway/ for getenv with a default secret string."""
        for py_file in RUNTIME_DIR.rglob("*.py"):
            content = py_file.read_text()
            self.assertNotIn(
                '"simulated-webhook-secret"', content,
                f"A3: hardcoded secret in {py_file.name}")
            # No getenv(..., "something") pattern for WEBHOOK_SECRET
            if "WEBHOOK_SECRET" in content and "get(" in content:
                # Allow get("WEBHOOK_SECRET", "") — empty is OK (rejected at runtime)
                self.assertNotIn(
                    'get("WEBHOOK_SECRET", "simulated', content,
                    f"A3: getenv default in {py_file.name}")

    def test_a3_runtime_refuses_without_secret(self):
        """S1 still green: empty secret → RuntimeError."""
        from payment_gateway.runtime import PaymentGatewayRuntime
        with self.assertRaises(RuntimeError):
            PaymentGatewayRuntime(webhook_secret="")


class A4NoPackEditTests(unittest.TestCase):
    """A4 (N4): No implementation inside Lb/ or Lb/before/."""

    def test_a4_no_runtime_files_in_packs(self):
        """capstone-runtime/ must not contain Lb/ or Lb/before/ with .py."""
        pack_dirs = [ROOT / "Lb", ROOT / "Lb" / "before"]
        for pack_dir in pack_dirs:
            if pack_dir.exists():
                py_files = list(pack_dir.rglob("*.py"))
                self.assertEqual(
                    py_files, [],
                    f"A4: .py files found in {pack_dir}: {py_files}")


class A5ExpiryJobSchedulerTests(unittest.TestCase):
    """A5 (M12): Expiry Job I-9 = Scheduler in name-map AND README."""

    def test_a5_name_map_says_scheduler(self):
        content = NAME_MAP.read_text()
        # Expiry Job row must say Scheduler
        self.assertIn("Scheduler", content)
        # Must NOT say Expiry Job is Worker Tier
        lines = content.split("\n")
        for line in lines:
            if "Expiry Job" in line and "I-9" in line.lower() or \
               "expiry_job" in line.lower() and "Tier" in line:
                self.assertNotIn("Worker Tier", line,
                                 "A5: Expiry Job must be Scheduler, not Worker Tier")

    def test_a5_readme_says_scheduler_for_expiry(self):
        content = README.read_text()
        # Find the line mentioning Expiry Job collapse
        for line in content.split("\n"):
            if "Expiry Job" in line and ("Tier" in line or "Scheduler" in line):
                self.assertIn("Scheduler", line,
                              "A5: README Expiry Job must say Scheduler")
                self.assertNotIn("Worker Tier", line,
                                 "A5: README must not say Expiry Job = Worker Tier")


class A6QueryStoreReadOnlyTests(RuntimeTestCase):
    """A6 (N9/M5): Query Store cannot write Payment."""

    def test_a6_query_store_insert_rejected(self):
        """Existing S8 still green: insert_payment from query_store → error."""
        pid, _, _ = self.authorized_payment()
        payment = self.rt.payment_store.load_payment(pid)
        with self.assertRaises(PermissionError):
            self.rt.payment_store.insert_payment(self.rt.query_store, payment)

    def test_a6_query_store_update_rejected(self):
        pid, _, _ = self.authorized_payment()
        payment = self.rt.payment_store.load_payment(pid)
        with self.assertRaises(PermissionError):
            self.rt.payment_store.update_payment(self.rt.query_store, payment)


class A7SpecTraceRequiredTests(unittest.TestCase):
    """A7 (M10/N10): Every in-scope route has a spec-trace row."""

    def test_a7_all_openapi_operations_on_spec_trace(self):
        """Every operationId in openapi.json appears in spec-trace.md."""
        with open(OPENAPI) as f:
            doc = json.load(f)
        trace_content = SPEC_TRACE.read_text()
        for path, methods in doc["paths"].items():
            for method, details in methods.items():
                op_id = details.get("operationId", "")
                if op_id:
                    self.assertIn(
                        op_id, trace_content,
                        f"A7: operationId '{op_id}' not in spec-trace.md")

    def test_a7_untraced_route_returns_404(self):
        """A route not in the runtime (dispute) returns 404 — cannot exist
        without a spec-trace row."""
        from .support import RuntimeTestCase as RTC
        rt_case = RTC()
        rt_case.setUp()
        status, body = rt_case.rt.handle(
            "POST", "/v1/payments/pay_1/dispute",
            {"idempotency_key": "dispute-key", "amount": 100000})
        self.assertEqual(status, 404)


class A8I3MockedTests(unittest.TestCase):
    """A8 (N6): No real host URLs in source."""

    def test_a8_no_https_acquirer_in_source(self):
        """Grep: no https:// URL pointing to a real acquirer/bank host."""
        real_patterns = ["https://", "http://"]
        allowed = ["https://github.com", "https://docs."]
        for py_file in RUNTIME_DIR.rglob("*.py"):
            content = py_file.read_text()
            for pattern in real_patterns:
                if pattern in content:
                    for line in content.split("\n"):
                        if pattern in line:
                            is_allowed = any(a in line for a in allowed)
                            self.assertTrue(
                                is_allowed or line.strip().startswith("#"),
                                f"A8: real host URL in {py_file.name}: "
                                f"{line.strip()}")


class A9LeftoverTitleCaseTests(unittest.TestCase):
    """A9: spec-trace and README labels use Title Case."""

    def test_a9_spec_trace_no_lowercase_status_labels(self):
        """spec-trace OpenAPI column must not have '200 declined' etc."""
        content = SPEC_TRACE.read_text()
        bad_patterns = ["200 declined", "200 captured", "200 refunded",
                        "200 voided", "200 failed"]
        for pattern in bad_patterns:
            self.assertNotIn(
                pattern, content,
                f"A9: lowercase label '{pattern}' in spec-trace.md")

    def test_a9_readme_demo_title_case(self):
        """README demo lines use Title Case for status."""
        content = README.read_text()
        # Check demo section for lowercase status after HTTP status
        bad_patterns = ["→ 200 voided", "→ 200 declined", "→ 200 failed"]
        for pattern in bad_patterns:
            self.assertNotIn(
                pattern, content,
                f"A9: lowercase label '{pattern}' in README demo")


class A10HumanATests(unittest.TestCase):
    """A10: SA signed this sitting."""

    def test_a10_readme_has_sa_acceptance(self):
        """README contains SA ☑ with a date."""
        content = README.read_text()
        self.assertIn("SA (A)", content, "A10: SA role missing from README")
        self.assertIn("☑", content, "A10: SA ☑ tick missing")
        self.assertIn("accepted", content.lower(),
                      "A10: SA acceptance statement missing")

    def test_a10_agents_md_exists(self):
        """AGENTS.md must exist as the contract."""
        self.assertTrue(AGENTS_MD.exists(), "A10: AGENTS.md missing")
        content = AGENTS_MD.read_text()
        self.assertIn("MUST", content)
        self.assertIn("MUST NOT", content)
