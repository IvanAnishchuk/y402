import pytest

from y402.errors import NoUsableOfferError
from y402.x402_client import parse_offers, select_offer

BODY = {
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


def test_parse_offers_reads_fields():
    offers = parse_offers(BODY)
    assert offers[0].network == "base-sepolia"
    assert offers[0].max_amount_atomic == 50000
    assert offers[0].domain_name == "USDC"


def test_select_offer_picks_enabled_registry_network():
    offer, network = select_offer(parse_offers(BODY), default_network="eip155:84532")
    assert network.id == "eip155:84532"
    assert offer.network == "base-sepolia"


def test_select_offer_raises_when_none_usable():
    only_solana = {"accepts": [BODY["accepts"][1]]}
    with pytest.raises(NoUsableOfferError):
        select_offer(parse_offers(only_solana), default_network="eip155:84532")
