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
