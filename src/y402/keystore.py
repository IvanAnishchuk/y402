"""Key-at-rest: OS keyring primary, encrypted JSON file fallback."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Protocol

import keyring
from eth_account import Account
from eth_typing import HexStr
from keyring.backends.fail import Keyring as FailKeyring

from y402.config import config_dir
from y402.errors import KeystoreError

if TYPE_CHECKING:
    from pathlib import Path

_SERVICE = "y402"
_ACCOUNT = "wallet"

_ERR_MISSING_ENV = "Y402_PASSPHRASE is required for the file keystore"
_ERR_DECRYPT_FAILED = "could not decrypt keystore (wrong passphrase?)"
_ERR_NO_KEY_IN_KEYRING = "no key in keyring"


class Keystore(Protocol):
    """Protocol for pluggable key-at-rest backends."""

    def has_key(self) -> bool: ...
    def save_key(self, private_key: str) -> None: ...
    def load_key(self) -> str: ...


def _passphrase() -> str:
    pw = os.environ.get("Y402_PASSPHRASE")
    if not pw:
        raise KeystoreError(_ERR_MISSING_ENV)
    return pw


class FileKeystore:
    """Encrypted JSON keystore (eth-account scrypt) under the config dir."""

    def _path(self) -> Path:
        return config_dir() / "keystore.json"

    def has_key(self) -> bool:
        return self._path().exists()

    def save_key(self, private_key: str) -> None:
        encrypted = Account.encrypt(HexStr(private_key), _passphrase())
        path = self._path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(encrypted), encoding="utf-8")
        # Even though the contents are scrypt-encrypted, the keystore (and the
        # plaintext wallet address it embeds) should not be world-readable.
        path.chmod(0o600)

    def load_key(self) -> str:
        try:
            encrypted = json.loads(self._path().read_text(encoding="utf-8"))
            return "0x" + Account.decrypt(encrypted, _passphrase()).hex()
        except (ValueError, KeyError) as exc:
            raise KeystoreError(_ERR_DECRYPT_FAILED) from exc


class KeyringKeystore:
    """Stores the raw private key in the OS keyring."""

    def has_key(self) -> bool:
        return keyring.get_password(_SERVICE, _ACCOUNT) is not None

    def save_key(self, private_key: str) -> None:
        keyring.set_password(_SERVICE, _ACCOUNT, private_key)

    def load_key(self) -> str:
        key = keyring.get_password(_SERVICE, _ACCOUNT)
        if key is None:
            raise KeystoreError(_ERR_NO_KEY_IN_KEYRING)
        return key


def _keyring_available() -> bool:
    try:
        return not isinstance(keyring.get_keyring(), FailKeyring)
    except Exception:  # noqa: BLE001 - any keyring backend error => treat as unavailable
        return False


def select_keystore() -> Keystore:
    """Return the best available keystore backend."""
    return KeyringKeystore() if _keyring_available() else FileKeystore()
