"""Tests for chain.py: balances via mocked web3."""

from decimal import Decimal
from unittest.mock import MagicMock

from y402.chain import ChainClient
from y402.registry import get_network

ADDR = "0x0000000000000000000000000000000000000abc"


def _client_with_mock_w3() -> tuple[ChainClient, MagicMock]:
    net = get_network("eip155:84532")
    assert net is not None
    w3 = MagicMock()
    cc = ChainClient(net, w3=w3)
    return cc, w3


def test_eth_balance_converts_from_wei() -> None:
    cc, w3 = _client_with_mock_w3()
    w3.eth.get_balance.return_value = 2_000_000_000_000_000_000  # 2 ETH in wei
    assert cc.eth_balance(ADDR) == Decimal("2")


def test_usdc_balance_converts_from_atomic() -> None:
    cc, w3 = _client_with_mock_w3()
    contract = MagicMock()
    contract.functions.balanceOf.return_value.call.return_value = 1_500_000
    w3.eth.contract.return_value = contract
    assert cc.usdc_balance(ADDR) == Decimal("1.5")
