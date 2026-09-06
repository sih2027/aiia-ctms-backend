// Deploys AuditAnchor to whatever network is passed via --network.
// Usage: npx hardhat run scripts/deploy.js --network amoy
const hre = require("hardhat");

async function main() {
  const AuditAnchor = await hre.ethers.getContractFactory("AuditAnchor");
  const contract = await AuditAnchor.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("AuditAnchor deployed to:", address);
  console.log("Add this to your FastAPI .env as:");
  console.log(`CONTRACT_ADDRESS=${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
