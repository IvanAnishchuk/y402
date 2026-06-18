from decimal import Decimal

from y402.config import default_config, load_config, save_config


def test_default_policy_values():
    p = default_config().policy
    assert p.auto_threshold == Decimal("0.01")
    assert p.per_payment_cap == Decimal("0.10")
    assert p.daily_cap == Decimal("1.00")
    assert p.unattended is False


def test_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = default_config()
    cfg.policy.unattended = True
    cfg.default_network = "eip155:8453"
    save_config(cfg)
    loaded = load_config()
    assert loaded.policy.unattended is True
    assert loaded.default_network == "eip155:8453"
    assert loaded.policy.per_payment_cap == Decimal("0.10")


def test_load_without_file_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert load_config().default_network == "eip155:84532"
