# CLAUDE.md

y402 -- Self-custodial CLI USDC wallet that speaks x402

CLI tool built with typer + rich; src layout under `src/y402/`.

> **Conventions, review rules, and project invariants live in [`AGENTS.md`](AGENTS.md)** --
> the single source of truth for this repo; read it first. This file keeps only the
> quick command reference below.

## Commands

```bash
# Install dependencies
uv sync

# Run the CLI
uv run y402 --help

# Run tests with coverage
uv run pytest

# Lint + format
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/

# Type check
uv run mypy
uv run ty check
uv run basedpyright

# Full pre-commit suite
uv run pre-commit run --all-files

# Supply-chain audit (pip-audit + SBOM)
uv run python scripts/audit.py
```

## Architecture

Deterministic core: `money` (Decimal↔atomic), `registry` (EVM networks), `config`,
`audit` (JSONL), `policy` (tiered caps). Custody: `keystore` (OS keyring + encrypted-file
fallback) + `wallet` (eth-account; the trust root — the private key never leaves it). I/O:
`chain` (web3.py balances + broadcast), `x402_client` (gasless pay: parse 402 → select
offer → EIP-3009 sign → `X-PAYMENT`), `transfer` (self-settled send). `cli` (Typer) and
`skill/` are thin shims.

The gasless x402 pay path signs locally and uses **no RPC**; `balance`/`send` use web3.py.
Money is always `decimal.Decimal` — never `float`. See `docs/superpowers/specs/` for the
design and `docs/DEFERRED.md` for accepted-as-is findings.
