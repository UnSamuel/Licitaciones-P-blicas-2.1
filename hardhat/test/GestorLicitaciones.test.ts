import { loadFixture } from "@nomicfoundation/hardhat-network-helpers";
import { expect } from "chai";
import hre from "hardhat";

describe("GestorLicitaciones", function () {

  async function deployFixture() {
    const [owner, otherAccount] = await hre.ethers.getSigners();

    // --- LÍNEA CORREGIDA ---
    // En lugar de obtener una "fábrica" y luego hacer .deploy(),
    // ahora desplegamos el contrato directamente con deployContract.
    const gestorLicitaciones = await hre.ethers.deployContract("GestorLicitaciones");

    return { gestorLicitaciones, owner, otherAccount };
  }

  // El resto del código de las pruebas no cambia
  it("Deberia desplegarse y asignar al desplegador como dueño", async function () {
    const { gestorLicitaciones, owner } = await loadFixture(deployFixture);
    expect(await gestorLicitaciones.owner()).to.equal(owner.address);
  });

  it("Deberia permitir al dueño crear una nueva licitacion", async function () {
    const { gestorLicitaciones, owner } = await loadFixture(deployFixture);
    const cuce = "VNT-2025-001";
    const descripcion = "Construccion de aula";
    const hashDBC = "0xabc123";

    await expect(gestorLicitaciones.crearLicitacion(cuce, descripcion, hashDBC))
      .to.emit(gestorLicitaciones, "LicitacionCreada")
      .withArgs(1, cuce);

    const licitacion = await gestorLicitaciones.licitaciones(1);
    expect(licitacion.cuce).to.equal(cuce);
  });

  it("NO deberia permitir a otra cuenta crear una licitacion", async function () {
    const { gestorLicitaciones, otherAccount } = await loadFixture(deployFixture);
    
    await expect(
      gestorLicitaciones.connect(otherAccount).crearLicitacion("FAIL-001", "Fallo", "0x000")
    ).to.be.revertedWithCustomError(gestorLicitaciones, "OwnableUnauthorizedAccount");
  });

  it("Deberia permitir a una cuenta presentar una propuesta a una licitacion abierta", async function () {
  const { gestorLicitaciones, owner, otherAccount } = await loadFixture(deployFixture);

  // Primero, el dueño crea una licitación
  await gestorLicitaciones.crearLicitacion("TEST-001", "Licitacion de prueba", "0xhash");

  // Luego, otra cuenta presenta una propuesta a la licitación con ID 1
  const hashPropuesta = "0xpropuesta_hash_123";
  await expect(
    gestorLicitaciones.connect(otherAccount).presentarPropuesta(1, hashPropuesta)
  ).to.emit(gestorLicitaciones, "PropuestaPresentada")
   .withArgs(1, otherAccount.address);

  // Verificamos que la propuesta se haya guardado
  const propuestas = await gestorLicitaciones.getPropuestas(1);
  expect(propuestas.length).to.equal(1);
  expect(propuestas[0].proponente).to.equal(otherAccount.address);
  expect(propuestas[0].hashPropuesta).to.equal(hashPropuesta);
});

});

