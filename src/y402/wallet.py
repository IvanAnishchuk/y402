"""Wallet: the trust root. Wraps an eth-account LocalAccount; key never leaves."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from eth_account import Account
from eth_account.messages import encode_typed_data

from y402 import keystore

if TYPE_CHECKING:
    from eth_account.datastructures import SignedTransaction
    from eth_account.signers.local import LocalAccount


class Wallet:
    def __init__(self, account: LocalAccount) -> None:
        self._account = account

    @classmethod
    def from_key(cls, private_key: str) -> Wallet:
        return cls(Account.from_key(private_key))

    @classmethod
    def create(cls) -> Wallet:
        return cls(Account.create())

    @classmethod
    def load(cls, ks: keystore.Keystore | None = None) -> Wallet:
        if ks is None:
            ks = keystore.select_keystore()
        return cls.from_key(ks.load_key())

    @property
    def address(self) -> str:
        return str(self._account.address)

    @property
    def private_key(self) -> str:
        return "0x" + self._account.key.hex()

    def sign_typed_data(
        self,
        domain: dict[str, Any],
        types: dict[str, Any],
        message: dict[str, Any],
    ) -> str:
        signable = encode_typed_data(domain, types, message)
        return self._account.sign_message(signable).signature.to_0x_hex()

    def sign_transaction(self, tx: dict[str, Any]) -> SignedTransaction:
        return self._account.sign_transaction(tx)
