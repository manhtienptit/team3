"""Composition root — one collapsed process standing for the I-9 locations.

Documented collapse (name-map.md): every I-4 container runs in this single
process with in-memory stores and an in-process bus. Module and container
classes keep the exact Lab 1 / Lab 3 strings; no container identity is
created or lost by the collapse.

Clock is injectable so tests can cross the CON.4 7-day authorization window
without sleeping.

S1: WEBHOOK_SECRET must be provided (env var or constructor arg). The runtime
refuses to start with an empty secret — no hardcoded default in source.
"""

import os
import time

from .api_gateway import APIGateway
from .expiry_job import ExpiryJob
from .mocks import AcquirerHostStub, MerchantPlatformFake
from .query_store import QueryStore
from .stores import IdempotencyStore, MessageQueue, PaymentStore
from .webhook_service import WebhookService
from .payment_orchestrator.acquirer_client import AcquirerClient
from .payment_orchestrator.event_publisher import EventPublisher
from .payment_orchestrator.fraud_gate import FraudGate
from .payment_orchestrator.idempotency_manager import IdempotencyManager
from .payment_orchestrator.input_validator import InputValidator
from .payment_orchestrator.persistence_manager import PersistenceManager
from .payment_orchestrator.request_handler import RequestHandler
from .payment_orchestrator.state_machine_engine import StateMachineEngine


class PaymentGatewayRuntime:
    """In-process Payment Gateway (I-1 system-in-focus), extended slice."""

    def __init__(self, clock=None, webhook_secret=None):
        self.clock = clock or time.time

        # S1: secret from constructor or environment — never a source default
        secret_raw = webhook_secret or os.environ.get("WEBHOOK_SECRET", "")
        if not secret_raw:
            raise RuntimeError(
                "S1: WEBHOOK_SECRET must be set (env or constructor arg); "
                "no hardcoded default in source")
        self._webhook_secret = secret_raw.encode() if isinstance(
            secret_raw, str) else secret_raw

        # I-3 externals — mocked (stub / in-process fake), never a real host
        self.acquirer_host = AcquirerHostStub()
        self.merchant_platform = MerchantPlatformFake()
        self.merchant_platform.secret = self._webhook_secret

        # I-4 data / queue containers — in-memory collapse
        self.idempotency_store = IdempotencyStore()
        self.payment_store = PaymentStore()
        self.message_queue = MessageQueue()
        self.webhook_service = WebhookService(self.message_queue,
                                              self.merchant_platform,
                                              self.payment_store,
                                              self._webhook_secret)

        # Payment Orchestrator (I-4) — the 8 modules of Lab 3 §2 / Lab 9 §3
        self.request_handler = RequestHandler(
            validator=InputValidator(),
            idempotency_manager=IdempotencyManager(self.idempotency_store),
            fraud_gate=FraudGate(self.idempotency_store),
            state_machine=StateMachineEngine(),
            acquirer_client=AcquirerClient(self.acquirer_host),
            persistence_manager=PersistenceManager(self.payment_store,
                                                   self.clock),
            event_publisher=EventPublisher(self.message_queue),
            clock=self.clock,
        )

        # Query Store (I-4) — read model (Lab 9 rel 3)
        self.query_store = QueryStore(self.payment_store)

        # Expiry Job (I-4) — CON.4 hourly tick (Lab 9 rel 10, 11)
        self.expiry_job = ExpiryJob(self.payment_store, self.message_queue)

        # API Gateway (I-4) — sync entry point
        self.api_gateway = APIGateway(self.request_handler, self.query_store,
                                      self.clock)

    # Merchant-facing surface (what the OpenAPI document describes)
    def handle(self, method, path, body):
        return self.api_gateway.handle(method, path, body)

    # Async half: deliver queued webhooks (never called inside the sync path)
    def drain_webhooks(self):
        self.message_queue.drain()

    # Expiry Job tick (collapsed: called by test or demo, not a real cron)
    def tick_expiry(self, now=None):
        return self.expiry_job.tick(now or self.clock())
