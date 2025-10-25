import { ethers } from "hardhat";

async function main() {
  const contractAddress = "PEGA_AQUÍ_LA_DIRECCION_DE_TU_CONTRATO";
  const gestorLicitaciones = await ethers.getContractAt("GestorLicitaciones", contractAddress);

  console.log("Creando licitaciones de prueba...");

  const tx1 = await gestorLicitaciones.crearLicitacion(
    "VNT-2025-001",
    "Adquisición de Equipamiento Informático",
    "0xhash_del_dbc_1"
  );
  await tx1.wait();
  console.log("Licitación 1 creada!");

  const tx2 = await gestorLicitaciones.crearLicitacion(
    "VNT-2025-002",
    "Construcción de Centro Comunitario",
    "0xhash_del_dbc_2"
  );
  await tx2.wait();
  console.log("Licitación 2 creada!");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});