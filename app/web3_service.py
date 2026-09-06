"""
web3.py wrapper for committing a Merkle root to the AuditAnchor smart
contract on Polygon Amoy testnet. Drop in as app/web3_service.py.

Requires three .env vars that do NOT exist in the repo's current .env
yet — add them after deploying the contract (see hardhat/README.md and
scripts/deploy.js, which prints CONTRACT_ADDRESS for you):

    AMOY_RPC_URL     - an Amoy RPC endpoint (Alchemy/Infura free tier,
                        or a public RPC such as https://rpc-amoy.polygon.technology)
    PRIVATE_KEY      - the deployer/committer wallet's private key.
                        Testnet only — never reuse a mainnet key, and
                        never commit this to git.
    CONTRACT_ADDRESS - printed by:
                        npx hardhat run scripts/deploy.js --network amoy
"""

import json
import os
from typing import Optional

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

AMOY_RPC_URL = os.getenv("AMOY_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
AMOY_CHAIN_ID = 80002

# Minimal ABI covering only what this backend calls (commitRoot + the
# auto-generated commits getter). If you extend the contract, copy the
# full ABI from hardhat/artifacts/contracts/AuditAnchor.sol/AuditAnchor.json.
CONTRACT_ABI = json.loads(
    """
    [
        {"inputs":[{"internalType":"bytes32","name":"merkleRoot","type":"bytes32"}],
         "name":"commitRoot","outputs":[],"stateMutability":"nonpayable","type":"function"},
        {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],
         "name":"commits","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],
         "stateMutability":"view","type":"function"}
    ]
    """
)


def _get_web3() -> Web3:
    if not AMOY_RPC_URL:
        raise RuntimeError("AMOY_RPC_URL is not set — see app/web3_service.py docstring.")
    w3 = Web3(Web3.HTTPProvider(AMOY_RPC_URL))
    if not w3.is_connected():
        raise RuntimeError(f"Could not connect to Amoy RPC at {AMOY_RPC_URL}")
    return w3


def _get_contract(w3: Web3):
    if not CONTRACT_ADDRESS:
        raise RuntimeError("CONTRACT_ADDRESS is not set — see app/web3_service.py docstring.")
    return w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)


def commit_merkle_root(merkle_root_hex: str) -> dict:
    """
    Sends commitRoot(merkleRoot) to the deployed contract. Returns a dict
    with tx_hash and block_number, ready to store in audit_anchor.
    """
    if not PRIVATE_KEY:
        raise RuntimeError("PRIVATE_KEY is not set — see app/web3_service.py docstring.")

    w3 = _get_web3()
    contract = _get_contract(w3)
    account = w3.eth.account.from_key(PRIVATE_KEY)

    root_bytes = bytes.fromhex(merkle_root_hex)
    tx = contract.functions.commitRoot(root_bytes).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": AMOY_CHAIN_ID,
        }
    )
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "tx_hash": receipt.transactionHash.hex(),
        "block_number": receipt.blockNumber,
        "block_timestamp": w3.eth.get_block(receipt.blockNumber).timestamp,
    }


def read_committed_root_for_block(block_number: int) -> Optional[str]:
    """
    Given the block_number stored in audit_anchor, looks up that block's
    timestamp and reads commits[timestamp] from the contract. Used by
    /audit/verify to fetch the on-chain value to compare a freshly
    recomputed root against. Returns a hex string (no 0x prefix), or
    None if nothing was committed at that key.
    """
    w3 = _get_web3()
    contract = _get_contract(w3)
    block_timestamp = w3.eth.get_block(block_number).timestamp
    value = contract.functions.commits(block_timestamp).call()
    if value == b"\x00" * 32:
        return None
    return value.hex()
