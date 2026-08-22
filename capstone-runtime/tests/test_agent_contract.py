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
from .fixtures.agent.violations import (
    A1_INVENTED_ROUTE,
    A1_TOKENIZE_ROUTE,
    A2_LOWERCASE_AUTHORIZED,
    A2_LOWERCASE_VOIDED,
    A2_LOWERCASE_FAILED,
    A3_SECRET_DEFAULT,
    A4_PACK_PATHS,
    A5_WRONG_I9,
    A6_QUERY_STORE_WRITE,
    A7_UNTRACED_ROUTE,
    A8_REAL_HOST,
    A9_LEFTOVER_LABELS,
    A10_SA_SIGN,
)

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
        """Fixture A1_INVENTED_ROUTE: POST /v1/3dsecure/authenticate → 404."""
        status, body = self.rt.handle(
            A1_INVENTED_ROUTE["method"],
            A1_INVENTED_ROUTE["path"],
            A1_INVENTED_ROUTE["body"])
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")

    def test_a1_tokenize_route_rejected(self):
        """Fixture A1_TOKENIZE_ROUTE: POST /v1/payments/tokenize → 404."""
        status, body = self.rt.handle(
            A1_TOKENIZE_ROUTE["method"],
            A1_TOKENIZE_ROUTE["path"],
            A1_TOKENIZE_ROUTE["body"])
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
        """Fixture A2_LOWERCASE_AUTHORIZED: runtime must NOT return lowercase."""
        status, body = self.authorize(amount=500000)
        self.assertNotEqual(body["status"], A2_LOWERCASE_AUTHORIZED["bad_value"])
        self.assertEqual(body["status"], A2_LOWERCASE_AUTHORIZED["correct_value"])

    def test_a2_void_returns_title_case(self):
        """Fixture A2_LOWERCASE_VOIDED: runtime must NOT return lowercase."""
        pid, _, _ = self.authorized_payment()
        status, body = self.void(pid)
        self.assertNotEqual(body["status"], A2_LOWERCASE_VOIDED["bad_value"])
        self.assertEqual(body["status"], A2_LOWERCASE_VOIDED["correct_value"])

    def test_a2_con6_failed_returns_title_case(self):
        """Fixture A2_LOWERCASE_FAILED: runtime must NOT return lowercase."""
        self.rt.acquirer_host.timeout_next_n = 99
        status, body = self.authorize(amount=500000)
        self.assertNotEqual(body["status"], A2_LOWERCASE_FAILED["bad_value"])
        self.assertEqual(body["status"], A2_LOWERCASE_FAILED["correct_value"])

    def test_a2_query_returns_title_case(self):
        pid, _, _ = self.authorized_payment()
        status, body = self.query(pid)
        self.assertNotEqual(body["status"], A2_LOWERCASE_AUTHORIZED["bad_value"])
        self.assertEqual(body["status"], A2_LOWERCASE_AUTHORIZED["correct_value"])

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
        """Fixture A3_SECRET_DEFAULT: grep for the violation pattern."""
        for py_file in RUNTIME_DIR.rglob("*.py"):
            content = py_file.read_text()
            self.assertNotIn(
                A3_SECRET_DEFAULT["code"], content,
                f"A3: fixture violation found in {py_file.name}")
            self.assertNotIn(
                '"simulated-webhook-secret"', content,
                f"A3: hardcoded secret in {py_file.name}")

    def test_a3_runtime_refuses_without_secret(self):
        """Empty secret with env popped → RuntimeError (like S1)."""
        from payment_gateway.runtime import PaymentGatewayRuntime
        old = os.environ.pop("WEBHOOK_SECRET", None)
        try:
            with self.assertRaises(RuntimeError):
                PaymentGatewayRuntime(webhook_secret="")
        finally:
            if old is not None:
                os.environ["WEBHOOK_SECRET"] = old


class A4NoPackEditTests(unittest.TestCase):
    """A4 (N4): No implementation inside Lb/ or Lb/before/.
    Fixture A4_PACK_PATHS classifies the forbidden paths."""

    def test_a4_fixture_paths_classified_as_forbidden(self):
        """Fixture A4_PACK_PATHS: these paths are classified as pack
        locations where runtime code must NEVER be placed. The checker
        verifies no payment_gateway .py content exists there."""
        repo_root = ROOT.parent  # team3 repo root
        for forbidden_path in A4_PACK_PATHS:
            full = repo_root / forbidden_path
            if full.exists() and full.suffix == ".py":
                content = full.read_text()
                self.assertNotIn(
                    "payment_gateway", content,
                    f"A4: runtime code in forbidden pack path "
                    f"{forbidden_path}")

    def test_a4_no_runtime_py_in_repo_pack_dirs(self):
        """Check the actual repo Lb/ dirs for runtime .py files."""
        repo_root = ROOT.parent
        pack_dirs = [repo_root / "Lb", repo_root / "Lb" / "before"]
        for pack_dir in pack_dirs:
            if pack_dir.exists():
                for py_file in pack_dir.rglob("*.py"):
                    content = py_file.read_text()
                    self.assertNotIn(
                        "from payment_gateway", content,
                        f"A4: runtime import in {py_file}")
                    self.assertNotIn(
                        "import payment_gateway", content,
                        f"A4: runtime import in {py_file}")


class A5ExpiryJobSchedulerTests(unittest.TestCase):
    """A5 (M12): Expiry Job I-9 = Scheduler in name-map AND README.
    Fixture A5_WRONG_I9 classifies the violation."""

    def test_a5_name_map_says_scheduler(self):
        content = NAME_MAP.read_text()
        self.assertIn(A5_WRONG_I9["correct"], content)
        lines = content.split("\n")
        for line in lines:
            if "Expiry Job" in line and "expiry_job" in line.lower():
                self.assertNotIn(A5_WRONG_I9["wrong"], line,
                                 "A5: Expiry Job must be Scheduler")

    def test_a5_readme_says_scheduler_for_expiry(self):
        content = README.read_text()
        for line in content.split("\n"):
            if "Expiry Job" in line and ("Tier" in line or "Scheduler" in line):
                self.assertIn(A5_WRONG_I9["correct"], line)
                self.assertNotIn(A5_WRONG_I9["wrong"], line,
                                 "A5: README Expiry Job = Scheduler")


class A6QueryStoreReadOnlyTests(RuntimeTestCase):
    """A6 (N9/M5): Query Store cannot write Payment.
    Fixture A6_QUERY_STORE_WRITE classifies the violation."""

    def test_a6_query_store_insert_rejected(self):
        """Fixture A6_QUERY_STORE_WRITE: attempt → PermissionError."""
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
    """A7 (M10/N10): Every in-scope route has a spec-trace row.
    Fixture A7_UNTRACED_ROUTE classifies a violation example."""

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

    def test_a7_untraced_fixture_route_returns_404(self):
        """Fixture A7_UNTRACED_ROUTE: a route with no spec-trace row
        must not exist in the runtime → 404."""
        from .support import RuntimeTestCase as RTC
        rt_case = RTC()
        rt_case.setUp()
        status, body = rt_case.rt.handle(
            A7_UNTRACED_ROUTE["method"],
            A7_UNTRACED_ROUTE["path"].replace("{id}", "pay_1"),
            {"idempotency_key": "dispute-key", "amount": 100000})
        self.assertEqual(status, 404)


class A8I3MockedTests(unittest.TestCase):
    """A8 (N6): No real host URLs in source.
    Fixture A8_REAL_HOST classifies the violation."""

    def test_a8_no_real_host_in_source(self):
        """Grep: no https:// URL pointing to a real acquirer/bank host.
        Fixture A8_REAL_HOST.url must not appear."""
        for py_file in RUNTIME_DIR.rglob("*.py"):
            content = py_file.read_text()
            self.assertNotIn(
                A8_REAL_HOST["url"], content,
                f"A8: fixture real host URL in {py_file.name}")
            # General check: no http(s):// in non-comment lines
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "https://" in stripped or "http://" in stripped:
                    # Allow known safe patterns
                    allowed = ["github.com", "docs."]
                    if not any(a in stripped for a in allowed):
                        self.fail(
                            f"A8: real host URL in {py_file.name}: "
                            f"{stripped}")


class A9LeftoverTitleCaseTests(unittest.TestCase):
    """A9: spec-trace and README labels use Title Case.
    Fixture A9_LEFTOVER_LABELS classifies the violations."""

    def test_a9_spec_trace_no_lowercase_status_labels(self):
        """Fixture A9_LEFTOVER_LABELS: none of the wrong patterns appear."""
        content = SPEC_TRACE.read_text()
        for pattern in A9_LEFTOVER_LABELS["wrong_patterns"]:
            self.assertNotIn(
                pattern, content,
                f"A9: lowercase label '{pattern}' in spec-trace.md")

    def test_a9_readme_demo_title_case(self):
        """README demo lines use Title Case for status."""
        content = README.read_text()
        bad_patterns = ["→ 200 voided", "→ 200 declined", "→ 200 failed"]
        for pattern in bad_patterns:
            self.assertNotIn(
                pattern, content,
                f"A9: lowercase label '{pattern}' in README demo")


class A10HumanATests(unittest.TestCase):
    """A10: SA signed this sitting.
    Fixture A10_SA_SIGN classifies what must be present."""

    def test_a10_readme_has_sa_acceptance(self):
        """README contains SA ☑ with a date."""
        content = README.read_text()
        self.assertIn(A10_SA_SIGN["required_field"], content,
                      "A10: SA role missing from README")
        self.assertIn("☑", content, "A10: SA ☑ tick missing")
        self.assertIn(A10_SA_SIGN["required_content"], content.lower(),
                      "A10: SA acceptance statement missing")

    def test_a10_agents_md_exists(self):
        """AGENTS.md must exist as the contract."""
        self.assertTrue(AGENTS_MD.exists(), "A10: AGENTS.md missing")
        content = AGENTS_MD.read_text()
        self.assertIn("MUST", content)
        self.assertIn("MUST NOT", content)
