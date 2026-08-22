"""Input Validator module (Lab 3 §2). CON.1 amount range, Luhn, card expiry."""

import time


class ValidationError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def luhn_valid(number):
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 12:
        return False
    checksum = 0
    for i, d in enumerate(digits):
        if (len(digits) - 1 - i) % 2 == 1:  # every second digit from the right
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


class InputValidator:
    MIN_AMOUNT = 10_000            # CON.1
    MAX_AMOUNT = 500_000_000       # CON.1

    def validate(self, amount, card, now):
        if not isinstance(amount, int) or not (self.MIN_AMOUNT <= amount <= self.MAX_AMOUNT):
            raise ValidationError(
                "invalid_amount",
                "amount must be an integer between 10000 and 500000000 VND (CON.1)")
        number = card.get("number", "")
        if not luhn_valid(number):
            raise ValidationError("invalid_card", "card number failed Luhn check")
        exp_month, exp_year = card.get("exp_month"), card.get("exp_year")
        now = time.gmtime(now)
        if not (1 <= (exp_month or 0) <= 12):
            raise ValidationError("invalid_card", "invalid exp_month")
        if (exp_year, exp_month) <= (now.tm_year, now.tm_mon):
            raise ValidationError("invalid_card", "card is expired")
