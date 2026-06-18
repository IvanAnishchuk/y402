from y402.registry import REGISTRY, enabled_networks, get_network


def test_base_sepolia_present_and_enabled():
    n = get_network("eip155:84532")
    assert n is not None and n.enabled
    assert n.chain_id == 84532
    assert n.usdc_address.lower() == "0x036cbd53842c5426634e7929541ec2318f3dcf7e"


def test_lookup_by_x402_name_alias():
    assert get_network("base-sepolia") is REGISTRY["eip155:84532"]


def test_base_mainnet_present_but_disabled():
    n = get_network("eip155:8453")
    assert n is not None and not n.enabled


def test_unknown_network_returns_none():
    assert get_network("eip155:999999") is None


def test_enabled_networks_excludes_disabled():
    ids = {n.id for n in enabled_networks()}
    assert "eip155:84532" in ids
    assert "eip155:8453" not in ids
