from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

from y402.audit import AuditRecord, append, read_all, spent_today


def _rec(amount: str, decision: str = "pay", ts: str = "2026-06-18T10:00:00+00:00") -> AuditRecord:
    return AuditRecord(
        ts=ts,
        kind="x402",
        amount_usd=amount,
        host="api.example.com",
        network="eip155:84532",
        resource="/data",
        decision=decision,
        tx=None,
    )


def test_append_then_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    append(_rec("0.05"))
    records = read_all()
    assert len(records) == 1
    assert records[0].amount_usd == "0.05"


def test_spent_today_sums_only_paid_today(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    append(_rec("0.05", decision="pay", ts="2026-06-18T09:00:00+00:00"))
    append(_rec("0.03", decision="pay", ts="2026-06-18T11:00:00+00:00"))
    append(_rec("0.20", decision="refuse", ts="2026-06-18T11:30:00+00:00"))
    append(_rec("9.00", decision="pay", ts="2026-06-17T11:00:00+00:00"))
    assert spent_today(today="2026-06-18") == Decimal("0.08")


def test_read_all_skips_corrupt_line(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    append(_rec("0.05", ts="2026-06-18T09:00:00+00:00"))
    # Simulate a torn/corrupt JSONL line wedged between two good records.
    log = tmp_path / "y402" / "audit.jsonl"
    with log.open("a", encoding="utf-8") as fh:
        fh.write("{not valid json\n")
    append(_rec("0.03", ts="2026-06-18T11:00:00+00:00"))
    records = read_all()  # must not raise
    assert len(records) == 2
    assert spent_today(today="2026-06-18") == Decimal("0.08")
