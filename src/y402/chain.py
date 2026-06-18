"""On-chain interaction via web3.py: balances, gas/nonce, broadcasting."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from web3 import Web3

from y402.money import from_atomic

if TYPE_CHECKING:
    from y402.registry import Network
    from y402.wallet import Wallet

_ERC20_BALANCE_ABI = [
    {
        "constant": True,
        "name": "balanceOf",
        "inputs": [{"name": "owner", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    }
]
_ERC20_TRANSFER_ABI = [
    {
        "constant": False,
        "name": "transfer",
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    }
]


class ChainClient:
    def __init__(self, network: Network, w3: Any | None = None, rpc_url: str | None = None) -> None:
        self.network = network
        # rpc_url lets a Config.rpc_overrides entry point at a private/custom node;
        # falls back to the registry's default endpoint when unset.
        self.w3: Any = w3 or Web3(Web3.HTTPProvider(rpc_url or network.rpc_url))

    def eth_balance(self, address: str) -> Decimal:
        wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
        return Decimal(wei) / Decimal(10) ** 18

    def usdc_balance(self, address: str) -> Decimal:
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.network.usdc_address),
            abi=_ERC20_BALANCE_ABI,
        )
        atomic = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
        return from_atomic(atomic)

    def transfer_usdc(self, wallet: Wallet, to: str, atomic: int) -> str:
        """Build, sign, broadcast a USDC transfer. Needs ETH for gas. Returns tx hash."""
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.network.usdc_address),
            abi=_ERC20_TRANSFER_ABI,
        )
        tx = contract.functions.transfer(Web3.to_checksum_address(to), atomic).build_transaction(
            {
                "from": wallet.address,
                "nonce": self.w3.eth.get_transaction_count(wallet.address),
                "chainId": self.network.chain_id,
            }
        )
        signed = wallet.sign_transaction(tx)
        tx_hash: Any = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return str(tx_hash.to_0x_hex())
