from decimal import Decimal

import pytest

from y402.money import USDC_DECIMALS, from_atomic, to_atomic


def test_decimals_constant() -> None:
    assert USDC_DECIMALS == 6


def test_to_atomic_rounds_to_six_places() -> None:
    assert to_atomic(Decimal("1.50")) == 1_500_000
    assert to_atomic(Decimal("0.000001")) == 1


def test_from_atomic_is_inverse() -> None:
    assert from_atomic(1_500_000) == Decimal("1.50")


def test_to_atomic_rejects_sub_atomic_precision() -> None:
    with pytest.raises(ValueError, match="sub-atomic"):
        to_atomic(Decimal("0.0000001"))
