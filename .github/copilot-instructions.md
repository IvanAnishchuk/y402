# Copilot instructions for y402

Pure-Python CLI tool (Python 3.14+) using uv, hatchling, typer, rich.
Source layout under `src/y402/`.

**All conventions, tooling, security, workflow, and project invariants live in
[`AGENTS.md`](../AGENTS.md)** -- the single source of truth for this repo. Read it
before reviewing or generating code. This file adds only the review-process rules
below.

## Review process

**When asked to "review", only review.** Do not create commits, push
changes, or apply fixes. The goal of a review is to provide feedback,
not to modify the code. If you find issues, report them as review
comments -- never fix them on behalf of the author.

When reviewing PRs:
- Triage every comment, including low-confidence hidden ones
- For actionable findings: report them as review comments (with code suggestions where applicable), or create a GitHub issue and link it
- Never dismiss comments without explicit owner confirmation
- Reply with linked issue number or reason before resolving conversations
- After changes are made, re-review before approving
- Verify that CHANGELOG.md is updated for user-visible changes
