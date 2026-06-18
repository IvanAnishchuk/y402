"""x402 buyer client: parse offers, select, build EIP-3009 payment, pay()."""

from __future__ import annotations

import base64
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import httpx

from y402 import audit
from y402.errors import NoUsableOfferError, PolicyRefusedError
from y402.money import from_atomic
from y402.policy import Decision, evaluate
from y402.registry import get_network

if TYPE_CHECKING:
    from collections.abc import Callable
    from decimal import Decimal

    from y402.config import Config
    from y402.registry import Network
    from y402.wallet import Wallet

_ERR_NO_USABLE_OFFER = "no exact-scheme offer on an enabled network"
_ERR_MALFORMED_402 = "malformed 402 payment-required response"
_HTTP_PAYMENT_REQUIRED = 402
# Reject offers whose settlement window is non-positive or implausibly long: a
# signed EIP-3009 authorization stays settleable until validBefore, so an
# uncapped seller timeout would leave a live payment credential outstanding for
# years. One hour is generous for any legitimate facilitator.
_MAX_TIMEOUT_SECONDS = 3600


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
                resource=a.get("resource") or "",
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
        # Reject malformed/hostile seller inputs before we ever sign:
        # a non-positive amount would erode the daily-cap accounting and crash
        # signing; an asset other than the registry USDC we sign for is unpayable.
        if o.max_amount_atomic <= 0:
            continue
        if not 0 < o.max_timeout <= _MAX_TIMEOUT_SECONDS:
            continue
        net = get_network(o.network)
        if net is None or not net.enabled:
            continue
        if o.asset.lower() != net.usdc_address.lower():
            continue
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
        # Pin the EIP-712 domain to the registry, not seller-supplied fields.
        # select_offer guarantees offer.asset == network.usdc_address, so the
        # registry's canonical name/version are authoritative for this contract.
        "name": network.usdc_domain_name,
        "version": network.usdc_domain_version,
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


def pay(
    url: str,
    *,
    config: Config,
    wallet: Wallet,
    http: httpx.Client | None = None,
    now_ts: int,
    confirm: Callable[[str], bool] | None = None,
) -> httpx.Response:
    """GET `url`; if 402, select an offer, apply policy, sign, and retry with X-PAYMENT."""
    # Own (and therefore close) the client only when we created it; a
    # caller-supplied client's lifecycle belongs to the caller.
    owns_client = http is None
    client = http or httpx.Client()
    try:
        resp = client.get(url)
        if resp.status_code != _HTTP_PAYMENT_REQUIRED:
            return resp

        try:
            offers = parse_offers(resp.json())
        except (ValueError, KeyError, TypeError) as exc:
            # ValueError covers json.JSONDecodeError + int() of a bad amount;
            # KeyError a missing field; TypeError int(None) on a null field.
            raise NoUsableOfferError(_ERR_MALFORMED_402) from exc
        offer, network = select_offer(offers, config.default_network)
        amount = from_atomic(offer.max_amount_atomic)
        host = httpx.URL(url).host
        today = datetime.now(UTC).date().isoformat()
        decision = evaluate(amount, config.policy, audit.spent_today(today))

        if decision is Decision.REFUSE or (decision is Decision.CONFIRM and confirm is None):
            _audit(amount, host, network.id, offer.resource, "refuse", None)
            msg = f"refused ${amount} to {host}"
            raise PolicyRefusedError(msg)
        if (
            decision is Decision.CONFIRM
            and confirm is not None
            and not confirm(f"Pay ${amount} to {host} for {offer.resource}?")
        ):
            _audit(amount, host, network.id, offer.resource, "refuse", None)
            msg = "declined at confirmation"
            raise PolicyRefusedError(msg)

        payload = build_payment(offer, network, wallet, now_ts)
        paid = client.get(url, headers={"X-PAYMENT": encode_x_payment(payload)})
        # Charge against the daily cap on send, NOT on a 2xx response: the signed
        # EIP-3009 authorization is valid until validBefore and a seller can settle
        # it later even after returning an error here. Gating on paid.is_success
        # would be fail-open (a reject-then-settle seller could bypass the cap).
        _audit(amount, host, network.id, offer.resource, "pay", None)
        return paid
    finally:
        if owns_client:
            client.close()


def _audit(
    amount: Decimal,
    host: str,
    network_id: str,
    resource: str,
    decision: str,
    tx: str | None,
) -> None:
    audit.append(
        audit.AuditRecord(
            ts=datetime.now(UTC).isoformat(),
            kind="x402",
            amount_usd=str(amount),
            host=host,
            network=network_id,
            resource=resource,
            decision=decision,
            tx=tx,
        )
    )
