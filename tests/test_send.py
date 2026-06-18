from decimal import Decimal
from unittest.mock import MagicMock

from y402.audit import read_all
from y402.registry import get_network
from y402.transfer import send_usdc
from y402.wallet import Wallet

KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"


def test_send_usdc_broadcasts_and_audits(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    chain = MagicMock()
    chain.transfer_usdc.return_value = "0xdeadbeef"
    chain.network = get_network("eip155:84532")
    tx = send_usdc(
        chain,
        Wallet.from_key(KEY),
        to="0x0000000000000000000000000000000000000abc",
        amount=Decimal("0.25"),
    )
    assert tx == "0xdeadbeef"
    chain.transfer_usdc.assert_called_once()
    # atomic units passed through
    assert chain.transfer_usdc.call_args.args[2] == 250000
    assert read_all()[0].decision == "pay"
    assert read_all()[0].tx == "0xdeadbeef"
