"""CLI entry point for y402."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

from y402 import __version__

app = typer.Typer(
    name="y402",
    help="Self-custodial CLI USDC wallet that speaks x402",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"y402 {__version__}")
        raise typer.Exit


@app.callback()
def main(
    _version: Annotated[
        bool,
        typer.Option(
            "--version", "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    """Self-custodial CLI USDC wallet that speaks x402."""


@app.command()
def hello(
    name: Annotated[str, typer.Argument(help="Name to greet.")] = "world",
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output."),
    ] = False,
) -> None:
    """Say hello (placeholder command)."""
    if verbose:
        console.print("[dim]verbose mode enabled[/]")
    console.print(f"Hello, [bold]{name}[/]!")
