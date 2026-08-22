"""Fraud Gate module (Lab 3 §2, CON.3).

5 rules, in-process, auth path only, first-block-wins. Runs INSIDE Payment
Orchestrator — Fraud Engine is not a standalone container (Lab 1 I-4 note).
Rule ids and order: FRAUD-01 card velocity, FRAUD-02 high-value,
FRAUD-03 merchant velocity, FRAUD-04 BIN country, FRAUD-05 daily cumulative.
Counters come from Idempotency Store (I-7: Fraud Counters).

Thresholds are simulated values — see ASSUMPTION rows in name-map.md.
"""

RULES = ("FRAUD-01", "FRAUD-02", "FRAUD-03", "FRAUD-04", "FRAUD-05")

# ASSUMPTION (one string each, used everywhere):
HIGH_VALUE_LIMIT = 200_000_000        # FRAUD-02: amount > 200,000,000 VND
CARD_VELOCITY_LIMIT = 10              # FRAUD-01: >10 auths/card/hour
MERCHANT_VELOCITY_LIMIT = 100         # FRAUD-03: >100 auths/merchant/hour
DAILY_CARD_LIMIT = 1_000_000_000      # FRAUD-05: >1B VND/card/day
REQUIRED_BIN_COUNTRY = "VN"           # FRAUD-04 (CON.8: BIN country != VN blocks)


class FraudBlocked(Exception):
    def __init__(self, rule_id):
        super().__init__(rule_id)
        self.rule_id = rule_id


class FraudGate:
    def __init__(self, idempotency_store):
        self.store = idempotency_store
        self.evaluations = 0  # test spy: proves CON.3 (never on capture/refund)

    def evaluate(self, card, amount, merchant_id):
        """Auth path only. Raises FraudBlocked on the first matching rule."""
        self.evaluations += 1
        card_ref = card["number"][-4:]
        if self.store.get_counter(f"velocity:card:{card_ref}") >= CARD_VELOCITY_LIMIT:
            raise FraudBlocked("FRAUD-01")
        if amount > HIGH_VALUE_LIMIT:
            raise FraudBlocked("FRAUD-02")
        if self.store.get_counter(f"velocity:merchant:{merchant_id}") >= MERCHANT_VELOCITY_LIMIT:
            raise FraudBlocked("FRAUD-03")
        if card.get("bin_country", REQUIRED_BIN_COUNTRY) != REQUIRED_BIN_COUNTRY:
            raise FraudBlocked("FRAUD-04")
        if self.store.get_counter(f"daily:card:{card_ref}") + amount > DAILY_CARD_LIMIT:
            raise FraudBlocked("FRAUD-05")
        self.store.bump_counter(f"velocity:card:{card_ref}")
        self.store.bump_counter(f"velocity:merchant:{merchant_id}")
        self.store.bump_counter(f"daily:card:{card_ref}", by=amount)
        return "pass"
