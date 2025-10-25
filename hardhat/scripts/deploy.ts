import { ethers } from "hardhat";

async function main() {
  console.log("Desplegando el contrato GestorLicitaciones...");

  const gestorLicitaciones = await ethers.deployContract("GestorLicitaciones");

  await gestorLicitaciones.waitForDeployment();

  const address = await gestorLicitaciones.getAddress();
  console.log(`✅ Contrato GestorLicitaciones desplegado en la direccion: ${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});