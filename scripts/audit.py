"""Run supply-chain audits locally (same checks as CI).

Fails with a non-zero exit code on any check failure.

Usage:
    uv run python scripts/audit.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console()
REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / ".reports" / "audit"

PROD_REQ = REPO_ROOT / "requirements.txt"
DEV_REQ = REPO_ROOT / "requirements-dev.txt"

TOTAL_STEPS = 5


def step(n: int, msg: str) -> None:
    console.print()
    console.print(f"[bold blue]==>[/] [bold]{n}/{TOTAL_STEPS}: {msg}[/]")


def ok(msg: str) -> None:
    console.print(f"   [bold green]ok[/] {msg}")


def warn(msg: str) -> None:
    console.print(f"   [bold yellow]!![/] {msg}")


def fail(msg: str) -> None:
    console.print(f"   [bold red]FAIL[/] {msg}")
    sys.exit(1)


def file_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_capture(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def load_sbom_components(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    return len(data.get("components", []))


def check_lock_in_sync() -> None:
    step(1, "uv.lock in sync with pyproject.toml")
    code, out = run_capture(["uv", "lock", "--check"])
    if code == 0:
        ok("uv.lock is up to date")
    else:
        console.print(out)
        fail("uv.lock is out of date -- run: uv run python scripts/regen_requirements.py")


def check_requirements_current() -> None:
    step(2, "requirements*.txt in sync with uv.lock")
    prod_before = file_sha256(PROD_REQ)
    dev_before = file_sha256(DEV_REQ)
    code, out = run_capture([sys.executable, str(REPO_ROOT / "scripts" / "regen_requirements.py")])
    if code != 0:
        console.print(out)
        fail("Failed to regenerate requirements files")
    prod_after = file_sha256(PROD_REQ)
    dev_after = file_sha256(DEV_REQ)
    stale = False
    if prod_before != prod_after:
        warn(f"requirements.txt was stale ({prod_before[:12]} -> {prod_after[:12]})")
        stale = True
    if dev_before != dev_after:
        warn(f"requirements-dev.txt was stale ({dev_before[:12]} -> {dev_after[:12]})")
        stale = True
    if stale:
        fail("Files were regenerated. Review and commit them.")
    ok("requirements.txt and requirements-dev.txt are current")


def pip_audit(step_n: int, req: Path, scope: str, logname: str) -> None:
    step(step_n, f"pip-audit on {req.name} ({scope})")
    log = REPORTS_DIR / logname
    code, out = run_capture(
        ["uv", "run", "pip-audit", "--strict", "--desc", "--requirement", str(req)]
    )
    log.write_text(out, encoding="utf-8")
    if code == 0:
        ok(f"No known vulnerabilities in {scope} dependencies")
    else:
        console.print(out)
        fail(f"pip-audit found vulnerabilities in {scope} -- see {log.relative_to(REPO_ROOT)}")


def generate_sbom(step_n: int, req: Path, scope: str, outname: str) -> None:
    step(step_n, f"CycloneDX SBOM ({scope})")
    sbom = REPORTS_DIR / outname
    code, out = run_capture(
        [
            "uv",
            "tool",
            "run",
            "--from",
            "cyclonedx-bom",
            "cyclonedx-py",
            "requirements",
            str(req),
            "--output-format",
            "json",
            "--output-file",
            str(sbom),
        ]
    )
    if code != 0:
        console.print(out)
        fail(f"cyclonedx-py failed for {scope}")
    components = load_sbom_components(sbom)
    ok(f"SBOM ({scope}) with {components} components -> {sbom.relative_to(REPO_ROOT)}")


def main() -> int:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    check_lock_in_sync()
    check_requirements_current()
    pip_audit(3, PROD_REQ, "prod", "pip-audit.log")
    pip_audit(4, DEV_REQ, "prod + dev", "pip-audit-dev.log")
    generate_sbom(5, PROD_REQ, "prod", "sbom.cdx.json")
    console.print()
    console.print("[bold green]All audits passed.[/]")
    console.print(f"Reports written to {REPORTS_DIR.relative_to(REPO_ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
