"""User-initiated self-settled transfers (broadcast on-chain). Needs ETH for gas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from y402 import audit
from y402.money import to_atomic

if TYPE_CHECKING:
    from decimal import Decimal

    from y402.chain import ChainClient
    from y402.wallet import Wallet


def send_usdc(chain: ChainClient, wallet: Wallet, to: str, amount: Decimal) -> str:
    """Broadcast a USDC transfer and audit it. Returns the tx hash."""
    tx_hash = chain.transfer_usdc(wallet, to, to_atomic(amount))
    audit.append(
        audit.AuditRecord(
            ts=datetime.now(UTC).isoformat(),
            kind="send",
            amount_usd=str(amount),
            host=to,
            network=chain.network.id,
            resource="transfer",
            decision="pay",
            tx=tx_hash,
        )
    )
    return tx_hash
