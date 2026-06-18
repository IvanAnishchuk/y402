"""x402 buyer client: parse offers, select, build EIP-3009 payment, pay()."""

from __future__ import annotations

import base64
import json
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from y402.errors import NoUsableOfferError
from y402.registry import get_network

if TYPE_CHECKING:
    from y402.registry import Network
    from y402.wallet import Wallet

_ERR_NO_USABLE_OFFER = "no exact-scheme offer on an enabled network"


@dataclass(frozen=True, slots=True)
class Offer:
    scheme: str
    network: str  # x402 network string as sent by the seller
    max_amount_atomic: int
    asset: str
    pay_to: str
    resource: str
    max_timeout: int
    domain_name: str | None
    domain_version: str | None


def parse_offers(body: dict[str, Any]) -> list[Offer]:
    offers: list[Offer] = []
    for a in body.get("accepts", []):
        extra = a.get("extra") or {}
        offers.append(
            Offer(
                scheme=a["scheme"],
                network=a["network"],
                max_amount_atomic=int(a["maxAmountRequired"]),
                asset=a["asset"],
                pay_to=a["payTo"],
                resource=a.get("resource", ""),
                max_timeout=int(a.get("maxTimeoutSeconds", 60)),
                domain_name=extra.get("name"),
                domain_version=extra.get("version"),
            )
        )
    return offers


def select_offer(offers: list[Offer], default_network: str) -> tuple[Offer, Network]:
    """Keep exact-scheme offers on enabled registry networks; prefer the default,
    else the cheapest by max amount.
    """
    usable: list[tuple[Offer, Network]] = []
    for o in offers:
        if o.scheme != "exact":
            continue
        net = get_network(o.network)
        if net is not None and net.enabled:
            usable.append((o, net))
    if not usable:
        raise NoUsableOfferError(_ERR_NO_USABLE_OFFER)
    for o, net in usable:
        if net.id == default_network:
            return o, net
    return min(usable, key=lambda pair: pair[0].max_amount_atomic)


X402_VERSION = 1

_TRANSFER_TYPES: dict[str, list[dict[str, str]]] = {
    "TransferWithAuthorization": [
        {"name": "from", "type": "address"},
        {"name": "to", "type": "address"},
        {"name": "value", "type": "uint256"},
        {"name": "validAfter", "type": "uint256"},
        {"name": "validBefore", "type": "uint256"},
        {"name": "nonce", "type": "bytes32"},
    ]
}


def build_payment(
    offer: Offer,
    network: Network,
    wallet: Wallet,
    now_ts: int,
) -> dict[str, Any]:
    """Sign an EIP-3009 transferWithAuthorization and wrap it as an x402 payload."""
    nonce = secrets.token_bytes(32)
    valid_before = now_ts + offer.max_timeout
    domain: dict[str, Any] = {
        "name": offer.domain_name or network.usdc_domain_name,
        "version": offer.domain_version or network.usdc_domain_version,
        "chainId": network.chain_id,
        "verifyingContract": network.usdc_address,
    }
    message: dict[str, Any] = {
        "from": wallet.address,
        "to": offer.pay_to,
        "value": offer.max_amount_atomic,
        "validAfter": 0,
        "validBefore": valid_before,
        "nonce": nonce,
    }
    signature = wallet.sign_typed_data(domain, _TRANSFER_TYPES, message)
    return {
        "x402Version": X402_VERSION,
        "scheme": offer.scheme,
        "network": offer.network,
        "payload": {
            "signature": signature,
            "authorization": {
                "from": wallet.address,
                "to": offer.pay_to,
                "value": str(offer.max_amount_atomic),
                "validAfter": "0",
                "validBefore": str(valid_before),
                "nonce": "0x" + nonce.hex(),
            },
        },
    }


def encode_x_payment(payload: dict[str, Any]) -> str:
    """Base64-encode a JSON-serialised x402 payment payload for the X-PAYMENT header."""
    return base64.b64encode(json.dumps(payload).encode()).decode()
