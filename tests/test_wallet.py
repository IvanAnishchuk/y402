from eth_account import Account
from eth_account.messages import encode_typed_data

from y402.wallet import Wallet

KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
ADDR = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"


def test_address_matches_known_key():
    assert Wallet.from_key(KEY).address == ADDR


def test_sign_typed_data_recovers_to_address():
    w = Wallet.from_key(KEY)
    domain = {
        "name": "USDC",
        "version": "2",
        "chainId": 84532,
        "verifyingContract": "0x036CbD53842c5426634e7929541eC2318f3dcf7e",
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
        "to": ADDR,
        "value": 1,
        "validAfter": 0,
        "validBefore": 9999999999,
        "nonce": b"\x00" * 32,
    }
    sig = w.sign_typed_data(domain, types, message)
    signable = encode_typed_data(domain, types, message)
    assert Account.recover_message(signable, signature=sig) == ADDR
