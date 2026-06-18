"""Tests for the CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from y402.cli import app

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_hello_default() -> None:
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "Hello" in result.output
    assert "world" in result.output


def test_hello_with_name() -> None:
    result = runner.invoke(app, ["hello", "Alice"])
    assert result.exit_code == 0
    assert "Alice" in result.output


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    assert "Usage" in result.output or "Self-custodial CLI USDC wallet that speaks x402" in result.output
