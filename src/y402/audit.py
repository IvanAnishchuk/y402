"""Append-only JSONL audit log of payments and transfers."""

import json
import logging
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from y402.config import config_dir

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AuditRecord:
    ts: str  # ISO-8601 UTC
    kind: str  # "x402" | "send"
    amount_usd: str  # Decimal as string
    host: str
    network: str
    resource: str
    decision: str  # "pay" | "confirm" | "refuse"
    tx: str | None  # on-chain tx hash for self-settle, else None


def _log_path() -> Path:
    return config_dir() / "audit.jsonl"


def append(record: AuditRecord) -> None:
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(record)) + "\n")


def read_all() -> list[AuditRecord]:
    path = _log_path()
    if not path.exists():
        return []
    out: list[AuditRecord] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            out.append(AuditRecord(**json.loads(stripped)))
        except (ValueError, TypeError) as exc:
            # A torn/corrupt line must not brick spent_today (the cap check) or
            # `y402 log`; skip it loudly rather than aborting the whole read.
            logger.warning("skipping unparseable audit line %d: %s", lineno, exc)
    return out


def spent_today(today: str) -> Decimal:
    """Sum USD of records with decision=="pay" whose ts date == today (YYYY-MM-DD)."""
    total = Decimal("0")
    for r in read_all():
        if r.decision == "pay" and r.ts.startswith(today):
            total += Decimal(r.amount_usd)
    return total
