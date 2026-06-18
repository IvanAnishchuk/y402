"""USD <-> USDC atomic-unit conversion. All money is Decimal; never float."""

from decimal import Decimal

USDC_DECIMALS = 6
_SCALE = Decimal(10) ** USDC_DECIMALS


class SubAtomicPrecisionError(ValueError):
    """Raised when a USD amount has more precision than USDC supports (6 decimals)."""

    def __init__(self, usd: Decimal) -> None:
        super().__init__(f"sub-atomic precision in {usd!r}")


def to_atomic(usd: Decimal) -> int:
    """Convert a USD Decimal to integer USDC atomic units (6 decimals)."""
    scaled = usd * _SCALE
    if scaled != scaled.to_integral_value():
        raise SubAtomicPrecisionError(usd)
    return int(scaled)


def from_atomic(atomic: int) -> Decimal:
    """Convert integer USDC atomic units back to a USD Decimal."""
    return (Decimal(atomic) / _SCALE).normalize()
