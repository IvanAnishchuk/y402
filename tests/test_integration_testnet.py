"""Opt-in end-to-end smoke test against a real Base Sepolia x402 endpoint.

Skipped unless ``Y402_E2E`` is set; requires a funded wallet (an initialized
keystore with a little testnet USDC) and ``Y402_E2E_URL`` pointing at a live
402-gated resource. Manual / CI-gated — never runs in the normal suite.
"""

from __future__ import annotations

import os
import time

import pytest

from y402.config import default_config
from y402.wallet import Wallet
from y402.x402_client import pay

pytestmark = pytest.mark.skipif(
    not os.environ.get("Y402_E2E"),
    reason="set Y402_E2E=1, fund the wallet, and set Y402_E2E_URL to run",
)


def test_real_testnet_pay() -> None:
    """A funded Base Sepolia wallet pays a real x402 endpoint and gets 200."""
    url = os.environ["Y402_E2E_URL"]
    resp = pay(url, config=default_config(), wallet=Wallet.load(), now_ts=int(time.time()))
    assert resp.status_code == 200
