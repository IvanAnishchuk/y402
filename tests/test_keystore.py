import stat
import sys

import pytest

from y402 import keystore

KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"


def test_file_backend_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("Y402_PASSPHRASE", "correct horse battery staple")
    ks = keystore.FileKeystore()
    assert not ks.has_key()
    ks.save_key(KEY)
    assert ks.has_key()
    assert ks.load_key().lower() == KEY.lower()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file permissions")
def test_file_backend_keystore_is_owner_only(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("Y402_PASSPHRASE", "pw")
    keystore.FileKeystore().save_key(KEY)
    path = tmp_path / "y402" / "keystore.json"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_file_backend_wrong_passphrase_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("Y402_PASSPHRASE", "right")
    keystore.FileKeystore().save_key(KEY)
    monkeypatch.setenv("Y402_PASSPHRASE", "wrong")
    with pytest.raises(keystore.KeystoreError):
        keystore.FileKeystore().load_key()


def test_select_backend_prefers_keyring_when_available(monkeypatch):
    monkeypatch.setattr(keystore, "_keyring_available", lambda: True)
    assert isinstance(keystore.select_keystore(), keystore.KeyringKeystore)


def test_select_backend_falls_back_to_file(monkeypatch):
    monkeypatch.setattr(keystore, "_keyring_available", lambda: False)
    assert isinstance(keystore.select_keystore(), keystore.FileKeystore)
