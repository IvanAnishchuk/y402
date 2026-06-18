"""Tests for the gasless x402 pay() flow."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING

import httpx
import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

from y402.config import default_config
from y402.errors import PolicyRefusedError
from y402.wallet import Wallet
from y402.x402_client import pay

KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
ACCEPT = {
    "scheme": "exact",
    "network": "base-sepolia",
    "maxAmountRequired": "5000",
    "asset": "0x036CbD53842c5426634e7929541eC2318f3dcf7e",
    "payTo": "0x0000000000000000000000000000000000000abc",
    "resource": "https://api.example.com/data",
    "maxTimeoutSeconds": 60,
    "extra": {"name": "USDC", "version": "2"},
}


def _handler(seen: dict[str, str]) -> Callable[[httpx.Request], httpx.Response]:
    def handle(request: httpx.Request) -> httpx.Response:
        if "X-PAYMENT" not in request.headers:
            return httpx.Response(402, json={"x402Version": 1, "accepts": [ACCEPT]})
        seen["header"] = request.headers["X-PAYMENT"]
        return httpx.Response(200, json={"ok": True})

    return handle


def test_pay_auto_pays_small_amount_and_attaches_header(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    seen: dict[str, str] = {}
    client = httpx.Client(transport=httpx.MockTransport(_handler(seen)))
    cfg = default_config()  # 0.005 USDC == 5000 atomic, below 0.01 threshold -> PAY
    resp = pay(
        "https://api.example.com/data",
        config=cfg,
        wallet=Wallet.from_key(KEY),
        http=client,
        now_ts=1_000_000,
    )
    assert resp.status_code == 200
    decoded = json.loads(base64.b64decode(seen["header"]))
    assert decoded["payload"]["authorization"]["value"] == "5000"


def test_pay_refuses_over_cap(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    big = dict(ACCEPT, maxAmountRequired="500000")  # 0.50 > 0.10 cap

    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(402, json={"x402Version": 1, "accepts": [big]})

    client = httpx.Client(transport=httpx.MockTransport(handle))
    with pytest.raises(PolicyRefusedError):
        pay(
            "https://api.example.com/data",
            config=default_config(),
            wallet=Wallet.from_key(KEY),
            http=client,
            now_ts=1_000_000,
        )
