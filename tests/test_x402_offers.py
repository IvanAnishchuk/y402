from typing import Any

import pytest

from y402.errors import NoUsableOfferError
from y402.x402_client import parse_offers, select_offer

BODY: dict[str, Any] = {
    "x402Version": 1,
    "error": "payment required",
    "accepts": [
        {
            "scheme": "exact",
            "network": "base-sepolia",
            "maxAmountRequired": "50000",
            "asset": "0x036CbD53842c5426634e7929541eC2318f3dcf7e",
            "payTo": "0xabc",
            "resource": "https://api.example.com/data",
            "maxTimeoutSeconds": 60,
            "extra": {"name": "USDC", "version": "2"},
        },
        {
            "scheme": "exact",
            "network": "solana",
            "maxAmountRequired": "1",
            "asset": "x",
            "payTo": "y",
            "resource": "z",
            "maxTimeoutSeconds": 60,
        },
    ],
}


def test_parse_offers_reads_fields() -> None:
    offers = parse_offers(BODY)
    assert offers[0].network == "base-sepolia"
    assert offers[0].max_amount_atomic == 50000
    assert offers[0].domain_name == "USDC"


def test_select_offer_picks_enabled_registry_network() -> None:
    offer, network = select_offer(parse_offers(BODY), default_network="eip155:84532")
    assert network.id == "eip155:84532"
    assert offer.network == "base-sepolia"


def test_select_offer_raises_when_none_usable() -> None:
    only_solana: dict[str, Any] = {"accepts": [BODY["accepts"][1]]}
    with pytest.raises(NoUsableOfferError):
        select_offer(parse_offers(only_solana), default_network="eip155:84532")


def test_select_offer_rejects_asset_that_is_not_registry_usdc() -> None:
    wrong_asset: dict[str, Any] = {
        "accepts": [{**BODY["accepts"][0], "asset": "0x000000000000000000000000000000000000dEaD"}],
    }
    with pytest.raises(NoUsableOfferError):
        select_offer(parse_offers(wrong_asset), default_network="eip155:84532")


def test_select_offer_rejects_non_positive_amount() -> None:
    negative: dict[str, Any] = {
        "accepts": [{**BODY["accepts"][0], "maxAmountRequired": "-5000"}],
    }
    with pytest.raises(NoUsableOfferError):
        select_offer(parse_offers(negative), default_network="eip155:84532")
