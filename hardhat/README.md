# AIIA CTMS — Audit Anchor Smart Contract

Solidity contract + Hardhat deployment scaffold for Section 8's blockchain
anchor layer. One function only, by design — no clinical, patient, or
regulatory data ever goes on-chain, only a periodic Merkle root over
audit_trail.row_hash values.

## Deploy to Polygon Amoy testnet

1. `npm install`
2. Get free testnet MATIC for your wallet at https://faucet.polygon.technology
3. Copy `.env.example` to `.env` and fill in `AMOY_RPC_URL` and `PRIVATE_KEY`
4. `npx hardhat compile`
5. `npx hardhat run scripts/deploy.js --network amoy`
6. Copy the printed `CONTRACT_ADDRESS=0x...` line into your **FastAPI backend's**
   `.env` (the one at the repo root, not this one), alongside `AMOY_RPC_URL`
   and `PRIVATE_KEY` — the Python side (`app/web3_service.py`) needs all three
   to call `commitRoot`.

## Files

- `contracts/AuditAnchor.sol` — the contract itself
- `scripts/deploy.js` — deploys it and prints the address
- `hardhat.config.js` — network config for Amoy (chain ID 80002)
