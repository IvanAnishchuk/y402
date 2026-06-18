# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Initial project scaffold (Python 3.14, `uv`, Typer + Rich, CC0-1.0).
- **Self-custodial wallet** — `Wallet` wraps an eth-account `LocalAccount` (the
  trust root; the private key never leaves it) with EIP-712 typed-data signing
  and raw transaction signing.
- **Key-at-rest** — `keystore` with an OS-keyring backend and an encrypted-file
  fallback (eth-account scrypt; the keystore file is written `0o600`).
- **Gasless x402 payments** — `pay()` parses a `402` response, selects an
  exact-scheme offer on an enabled network, applies the spending policy, signs
  an EIP-3009 `transferWithAuthorization` locally (no RPC, no facilitator), and
  retries with the `X-PAYMENT` header.
- **Self-settled transfers** — `send_usdc` broadcasts a USDC transfer via
  web3.py (needs ETH for gas).
- **Tiered spending policy** — per-payment cap, daily cap, an auto-pay threshold,
  and an `unattended` mode, backed by a JSONL audit log.
- **Network registry** — Base Sepolia (enabled) and Base mainnet (disabled) by
  default; money is always `decimal.Decimal`.
- **CLI** — `init`, `topup`, `balance`, `pay`, `send`, `config get|set`, `log`.
- **Claude skill** — `skill/SKILL.md` (`y402-pay`) so an agent can pay
  402-gated endpoints via `y402 pay --unattended <URL>`.
- Opt-in Base Sepolia end-to-end smoke test (gated on `Y402_E2E`).
