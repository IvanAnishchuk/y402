"""Config + Policy persisted as TOML under XDG config dir. Decimal money."""

import os
import tomllib
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import tomli_w

from y402.registry import DEFAULT_NETWORK

APP_NAME = "y402"


@dataclass(slots=True)
class Policy:
    auto_threshold: Decimal = Decimal("0.01")
    per_payment_cap: Decimal = Decimal("0.10")
    daily_cap: Decimal = Decimal("1.00")
    unattended: bool = False


@dataclass(slots=True)
class Config:
    policy: Policy = field(default_factory=Policy)
    default_network: str = DEFAULT_NETWORK
    rpc_overrides: dict[str, str] = field(default_factory=dict)


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_NAME


def config_path() -> Path:
    return config_dir() / "config.toml"


def default_config() -> Config:
    return Config()


def load_config() -> Config:
    path = config_path()
    if not path.exists():
        return default_config()
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    pol = data.get("policy", {})
    policy = Policy(
        auto_threshold=Decimal(str(pol.get("auto_threshold", "0.01"))),
        per_payment_cap=Decimal(str(pol.get("per_payment_cap", "0.10"))),
        daily_cap=Decimal(str(pol.get("daily_cap", "1.00"))),
        unattended=bool(pol.get("unattended", False)),
    )
    return Config(
        policy=policy,
        default_network=data.get("default_network", DEFAULT_NETWORK),
        rpc_overrides=dict(data.get("rpc_overrides", {})),
    )


def save_config(cfg: Config) -> None:
    config_dir().mkdir(parents=True, exist_ok=True)
    data = {
        "default_network": cfg.default_network,
        "policy": {
            "auto_threshold": str(cfg.policy.auto_threshold),
            "per_payment_cap": str(cfg.policy.per_payment_cap),
            "daily_cap": str(cfg.policy.daily_cap),
            "unattended": cfg.policy.unattended,
        },
        "rpc_overrides": cfg.rpc_overrides,
    }
    config_path().write_text(tomli_w.dumps(data), encoding="utf-8")
