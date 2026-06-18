"""Decide whether an automated x402 payment may proceed."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from decimal import Decimal

    from y402.config import Policy


class Decision(StrEnum):
    PAY = "pay"
    CONFIRM = "confirm"
    REFUSE = "refuse"


def evaluate(amount_usd: Decimal, policy: Policy, spent_today: Decimal) -> Decision:
    """Tiered policy. Caps hard-refuse; unattended turns the confirm band into PAY."""
    if amount_usd <= 0:
        return Decision.REFUSE
    if amount_usd > policy.per_payment_cap:
        return Decision.REFUSE
    if spent_today + amount_usd > policy.daily_cap:
        return Decision.REFUSE
    if amount_usd <= policy.auto_threshold:
        return Decision.PAY
    return Decision.PAY if policy.unattended else Decision.CONFIRM
