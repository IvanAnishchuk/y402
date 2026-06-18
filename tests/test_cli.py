"""Tests for the CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typer.testing import CliRunner

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

from y402.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "y402" in result.stdout


def test_init_creates_key_and_prints_address(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("Y402_PASSPHRASE", "pw")
    monkeypatch.setattr("y402.keystore._keyring_available", lambda: False)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "0x" in result.stdout


def test_config_get_shows_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    result = runner.invoke(app, ["config", "get"])
    assert result.exit_code == 0
    assert "eip155:84532" in result.stdout


def test_send_unknown_network_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    result = runner.invoke(app, ["send", "0xabc", "0.1", "--network", "bogus", "--yes"])
    assert result.exit_code == 1
    assert "Unknown network" in result.stdout
