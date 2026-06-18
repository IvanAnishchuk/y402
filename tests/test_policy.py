from decimal import Decimal

from y402.config import Policy
from y402.policy import Decision, evaluate


def _p(unattended: bool = False) -> Policy:
    return Policy(
        auto_threshold=Decimal("0.01"),
        per_payment_cap=Decimal("0.10"),
        daily_cap=Decimal("1.00"),
        unattended=unattended,
    )


def test_auto_pay_below_threshold() -> None:
    assert evaluate(Decimal("0.005"), _p(), spent_today=Decimal("0")) is Decision.PAY


def test_confirm_in_band_interactive() -> None:
    assert evaluate(Decimal("0.05"), _p(), spent_today=Decimal("0")) is Decision.CONFIRM


def test_unattended_auto_pays_in_band() -> None:
    assert evaluate(Decimal("0.05"), _p(unattended=True), spent_today=Decimal("0")) is Decision.PAY


def test_refuse_above_per_payment_cap() -> None:
    assert (
        evaluate(Decimal("0.50"), _p(unattended=True), spent_today=Decimal("0")) is Decision.REFUSE
    )


def test_refuse_when_daily_cap_would_be_exceeded() -> None:
    assert (
        evaluate(Decimal("0.05"), _p(unattended=True), spent_today=Decimal("0.98"))
        is Decision.REFUSE
    )


def test_refuse_non_positive_amount() -> None:
    assert evaluate(Decimal("0"), _p(), spent_today=Decimal("0")) is Decision.REFUSE
    assert (
        evaluate(Decimal("-0.01"), _p(unattended=True), spent_today=Decimal("0")) is Decision.REFUSE
    )
