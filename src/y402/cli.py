"""CLI entry point for y402."""

from __future__ import annotations

import time
from decimal import Decimal, InvalidOperation
from typing import Annotated

import qrcode
import typer
from rich.console import Console
from web3 import Web3

from y402 import __version__, keystore
from y402.audit import read_all
from y402.chain import ChainClient
from y402.config import load_config, save_config
from y402.registry import enabled_networks, get_network
from y402.transfer import send_usdc
from y402.wallet import Wallet
from y402.x402_client import pay as x402_pay

app = typer.Typer(
    name="y402",
    help="Self-custodial CLI USDC wallet that speaks x402",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

config_app = typer.Typer(help="Read and write config values.")
app.add_typer(config_app, name="config")


def version_callback(value: bool) -> None:
    if value:
        console.print(f"y402 {__version__}")
        raise typer.Exit


@app.callback()
def main(
    _version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    """Self-custodial CLI USDC wallet that speaks x402."""


@app.command()
def init() -> None:
    """Initialize a new wallet and save the key to the keystore."""
    ks = keystore.select_keystore()
    if ks.has_key():
        console.print("wallet already initialized")
        raise typer.Exit(1)
    wallet = Wallet.create()
    ks.save_key(wallet.private_key)
    console.print(f"Created wallet: {wallet.address}")


@app.command()
def topup() -> None:
    """Show a QR code and address for funding the wallet."""
    wallet = Wallet.load()
    qr = qrcode.QRCode()
    qr.add_data(wallet.address)
    qr.print_ascii()
    console.print(f"Address: {wallet.address}")
    console.print("Fund with USDC (and a little ETH for gas).")


@app.command()
def balance(
    network: Annotated[
        str | None,
        typer.Option(
            "--network", help="Network ID (CAIP-2 or x402 name). Defaults to all enabled."
        ),
    ] = None,
) -> None:
    """Show USDC and ETH balances across enabled networks."""
    cfg = load_config()
    wallet = Wallet.load()
    if network is not None:
        net = get_network(network)
        if net is None:
            console.print(f"[red]Unknown network: {network}[/red]")
            raise typer.Exit(1)
        nets = [net]
    else:
        nets = enabled_networks()
    for net in nets:
        cc = ChainClient(net, rpc_url=cfg.rpc_overrides.get(net.id))
        console.print(
            f"{net.id}: {cc.usdc_balance(wallet.address)} USDC,"
            f" {cc.eth_balance(wallet.address)} ETH"
        )


@app.command()
def pay(
    url: Annotated[str, typer.Argument(help="URL of the x402-protected resource.")],
    unattended: Annotated[
        bool,
        typer.Option("--unattended", help="Skip confirmation prompts (auto-pay)."),
    ] = False,
) -> None:
    """Fetch a URL, paying any x402 payment request automatically."""
    cfg = load_config()
    if unattended:
        cfg.policy.unattended = True
    resp = x402_pay(
        url,
        config=cfg,
        wallet=Wallet.load(),
        now_ts=int(time.time()),
        confirm=typer.confirm,
    )
    console.print(resp.text)


def _usd(value: str) -> Decimal:
    """Parse a USD amount, exiting cleanly (not with a traceback) on bad input."""
    try:
        return Decimal(value)
    except InvalidOperation:
        console.print(f"[red]Invalid amount: {value}[/red]")
        raise typer.Exit(1) from None


@app.command()
def send(
    to: Annotated[str, typer.Argument(help="Recipient address.")],
    amount: Annotated[str, typer.Argument(help="Amount of USDC to send.")],
    network: Annotated[
        str | None,
        typer.Option(
            "--network",
            help="Network ID (CAIP-2 or x402 name). Defaults to the configured default_network.",
        ),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Send USDC to an address."""
    # Default to the configured network (consistent with `pay`), not whichever
    # registry entry happens to be first-enabled.
    cfg = load_config()
    key = network or cfg.default_network
    net = get_network(key)
    if net is None:
        console.print(f"[red]Unknown network: {key}[/red]")
        raise typer.Exit(1)
    # Validate recipient + amount up front so a typo is a clean error, not a
    # mid-send traceback (and never after we've already prompted/loaded the key).
    if not Web3.is_address(to):
        console.print(f"[red]Invalid recipient address: {to}[/red]")
        raise typer.Exit(1)
    amount_usd = _usd(amount)
    if amount_usd <= 0:
        console.print(f"[red]Amount must be positive: {amount}[/red]")
        raise typer.Exit(1)
    if not yes and not typer.confirm(f"Send {amount_usd} USDC to {to} on {net.id}?"):
        raise typer.Abort()
    tx = send_usdc(
        ChainClient(net, rpc_url=cfg.rpc_overrides.get(net.id)),
        Wallet.load(),
        to=to,
        amount=amount_usd,
    )
    console.print(f"sent: {tx}")


@config_app.command("get")
def config_get() -> None:
    """Print current config values."""
    cfg = load_config()
    console.print(f"default_network: {cfg.default_network}")
    console.print(f"unattended: {cfg.policy.unattended}")
    console.print(f"per_payment_cap: {cfg.policy.per_payment_cap}")


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Config key to set.")],
    value: Annotated[str, typer.Argument(help="New value.")],
) -> None:
    """Set a config value."""
    cfg = load_config()
    if key == "default_network":
        cfg.default_network = value
    elif key == "unattended":
        cfg.policy.unattended = value.lower() in ("1", "true", "yes", "on")
    elif key == "per_payment_cap":
        cfg.policy.per_payment_cap = _usd(value)
    else:
        console.print(f"[red]Unknown config key: {key}[/red]")
        raise typer.Exit(1)
    save_config(cfg)


@app.command("log")
def show_log() -> None:
    """Print the payment audit log."""
    for r in read_all():
        console.print(f"{r.ts} {r.decision} ${r.amount_usd} {r.host} {r.resource}")
