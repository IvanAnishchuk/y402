# AGENTS.md — y402

y402 — Self-custodial CLI USDC wallet that speaks x402

Pure-Python CLI built with **typer + rich**, Python 3.14+,
src layout under `src/y402/`. Guidance for AI coding
agents working in this repo; humans get the same rules via `CLAUDE.md` and
`.github/copilot-instructions.md`.

## Build & run

```bash
uv sync                                              # install deps
uv run y402 --help        # run the CLI
uv run pytest                                        # tests + coverage
uv run ruff check --fix src/ tests/                  # lint
uv run ruff format src/ tests/                       # format
uv run mypy
uv run ty check
uv run basedpyright
uv run pre-commit run --all-files                  # full hook suite
uv run python scripts/audit.py                       # supply-chain audit
```

## Review priorities & invariants (this project)

- **CLI output goes through `rich.console.Console`, never bare `print()`**
  (ruff `T20` enforces this). `Console.print(...)` is correct — not a violation
  to "fix".
- Entry point is `y402.cli:app` (a `typer.Typer()`);
  `__main__.py` enables `python -m y402`. Keep a
  `help=` on every `typer.Option`.
- Exit codes: `0` success, `1` runtime error, `2` usage error (typer handles the
  last).
- Coverage floor is **50%** — deliberately low for
  an early-stage CLI. Raise it as the tool stabilizes; do not lower it, and do
  not add hollow tests purely to clear it.

<!-- universal:begin -->
<!--
  Universal conventions — shared verbatim across all python-project-templates.
  This block is byte-identical in every template's AGENTS.md; edit it in one
  place and propagate, or scripts/check_docs_sync.py will flag the drift.
-->
## Universal conventions

These apply to every project generated from these templates, regardless of type.

### Tooling

- **Package manager: `uv`** — never raw `pip`. Lock with `uv lock`, sync with
  `uv sync --frozen`. Run all tooling through `uv run`.
- **Lint + format: `ruff`** — line length 100, security rules (`S`/`BLE`/`TRY`)
  enabled. When a pylint (`PL`) limit is genuinely too tight, raise the
  threshold in `pyproject.toml`; do not silence the rule with a blanket ignore.
- **Type checking** — all public APIs typed; modern syntax (`list[str]`,
  `str | None`). The configured checkers run via `uv run` (see the build
  commands above for which are enabled in this project).
- **Testing: `pytest`** with branch coverage; the floor lives in
  `pyproject.toml`. Prefer fixtures and in-memory doubles over heavy mocking.
- **No checked-in shell scripts or Makefiles** — operational tooling lives in
  `scripts/*.py`, run via `uv run python scripts/<name>.py`.

### Code style

- **Imports go at the top of the file.** Do not silence ruff `PLC0415`
  (import-outside-top-level) to keep a diff small or to scope a name locally.
  The only acceptable inline imports are: a real circular dependency that
  `if TYPE_CHECKING:` cannot break, a heavy optional dependency that needs lazy
  loading, or deferred filesystem-touching imports inside test helpers.
- **Double quotes**, f-strings over `.format()`/`%`, `pathlib.Path` over
  `os.path`.
- **Every `# noqa` / `# type: ignore` must name the rule and say why.**

### Security & supply chain

- All `subprocess` calls use list args — never `shell=True`.
- Catch the narrowest exception possible; never bare `except:` or an
  unjustified `except Exception:`. Chain with `raise ... from err`.
- Validate URLs before fetching. Never hardcode secrets — use env vars or
  Pydantic Settings; `.env` is local-only and gitignored.
- Releases are signed (sigstore) and ship PEP 740 attestations + an SBOM.

### Workflow

- **Never push to `main`** — always a short-lived branch and a PR.
- **Conventional Commits** (`--strict`): `feat`, `fix`, `chore`, `security`,
  `perf`, `docs`, `test`, `refactor`, `ci`, `build`, `revert`, `style`.
- Run `uv run pre-commit run --all-files` before pushing; all CI checks must
  pass before merge.
- **Solo maintainer:** branch protection requires one approving review you
  cannot give your own PR — merge your reviewed PRs with `gh pr merge --admin`
  (permitted because `enforce_admins: false`).
- **Bump the version in both** `pyproject.toml` and `src/<package>/__init__.py`.
- **Changelog:** every PR adds an entry under `[Unreleased]` in `CHANGELOG.md`
  (Keep a Changelog format) — fixes, CI, and docs changes included.

### Review process

**When asked to "review", only review.** Do not create commits, push, or apply
fixes — report findings as review comments (with code suggestions where
applicable) or file a linked issue. Specifically:

- Triage every comment, including low-confidence hidden ones.
- Never dismiss a comment without explicit owner confirmation; reply with the
  linked issue number or a reason before resolving a conversation.
- Re-review after changes before approving.
- Verify `CHANGELOG.md` is updated for user-visible changes.
<!-- universal:end -->
