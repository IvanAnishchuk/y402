"""EVM network registry. Adding a chain = adding a Network entry."""

from dataclasses import dataclass

DEFAULT_NETWORK = "eip155:84532"  # Base Sepolia


@dataclass(frozen=True, slots=True)
class Network:
    id: str  # CAIP-2, e.g. "eip155:84532"
    x402_name: str  # the string sellers use in 402 `network`, e.g. "base-sepolia"
    chain_id: int
    rpc_url: str
    usdc_address: str
    usdc_domain_name: str  # EIP-712 domain name of the USDC contract
    usdc_domain_version: str  # EIP-712 domain version
    enabled: bool


REGISTRY: dict[str, Network] = {
    "eip155:84532": Network(
        id="eip155:84532",
        x402_name="base-sepolia",
        chain_id=84532,
        rpc_url="https://sepolia.base.org",
        usdc_address="0x036CbD53842c5426634e7929541eC2318f3dcf7e",
        usdc_domain_name="USDC",
        usdc_domain_version="2",
        enabled=True,
    ),
    "eip155:8453": Network(
        id="eip155:8453",
        x402_name="base",
        chain_id=8453,
        rpc_url="https://mainnet.base.org",
        usdc_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        usdc_domain_name="USD Coin",
        usdc_domain_version="2",
        enabled=False,
    ),
}


def get_network(key: str) -> Network | None:
    """Look up a network by CAIP-2 id or by x402 `network` name."""
    if key in REGISTRY:
        return REGISTRY[key]
    return next((n for n in REGISTRY.values() if n.x402_name == key), None)


def enabled_networks() -> list[Network]:
    return [n for n in REGISTRY.values() if n.enabled]
