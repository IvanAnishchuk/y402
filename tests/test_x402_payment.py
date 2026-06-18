import base64
import json

from eth_account import Account
from eth_account.messages import encode_typed_data

from y402.registry import get_network
from y402.wallet import Wallet
from y402.x402_client import Offer, build_payment, encode_x_payment

KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
ADDR = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"  # corrected: address of KEY above


def _offer() -> Offer:
    return Offer(
        scheme="exact",
        network="base-sepolia",
        max_amount_atomic=50000,
        asset="0x036CbD53842c5426634e7929541eC2318f3dcf7e",
        pay_to="0x0000000000000000000000000000000000000abc",
        resource="https://api.example.com/data",
        max_timeout=60,
        domain_name="USDC",
        domain_version="2",
    )


def test_build_payment_signature_recovers_to_wallet() -> None:
    net = get_network("base-sepolia")
    assert net is not None
    payload = build_payment(_offer(), net, Wallet.from_key(KEY), now_ts=1_000_000)
    auth = payload["payload"]["authorization"]
    assert auth["from"] == ADDR
    assert int(auth["value"]) == 50000
    assert auth["validAfter"] == "0"
    assert int(auth["validBefore"]) == 1_000_000 + 60
    domain = {
        "name": "USDC",
        "version": "2",
        "chainId": 84532,
        "verifyingContract": net.usdc_address,
    }
    types = {
        "TransferWithAuthorization": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "validAfter", "type": "uint256"},
            {"name": "validBefore", "type": "uint256"},
            {"name": "nonce", "type": "bytes32"},
        ]
    }
    message = {
        "from": ADDR,
        "to": auth["to"],
        "value": 50000,
        "validAfter": 0,
        "validBefore": 1_000_060,
        "nonce": bytes.fromhex(auth["nonce"][2:]),
    }
    signable = encode_typed_data(domain, types, message)
    assert Account.recover_message(signable, signature=payload["payload"]["signature"]) == ADDR


def test_encode_x_payment_is_base64_json() -> None:
    payload = {"x402Version": 1, "scheme": "exact"}
    header = encode_x_payment(payload)
    assert json.loads(base64.b64decode(header)) == payload
