import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";
import "dotenv/config"; // Importamos la configuración de dotenv

// Leemos las variables del archivo .env
const SEPOLIA_RPC_URL = process.env.SEPOLIA_RPC_URL || "https://sepolia.infura.io/v3/example";
const PRIVATE_KEY = process.env.PRIVATE_KEY || "0xkey";

const config: HardhatUserConfig = {
  solidity: "0.8.20",
  networks: {
    // Añadimos la configuración para la red 'sepolia'
    sepolia: {
      url: SEPOLIA_RPC_URL,
      accounts: [PRIVATE_KEY],
      chainId: 11155111, // Este es el ID de la red Sepolia
    },
  },
};

export default config;