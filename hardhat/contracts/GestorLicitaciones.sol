// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract GestorLicitaciones is Ownable {

    // --- ESTRUCTURA PARA LAS PROPUESTAS ---
    struct Propuesta {
        address proponente; // Quién presenta la propuesta
        string hashPropuesta; // El hash del documento de la propuesta
        uint timestamp; // Cuándo la presentó
    }

    enum EstadoLicitacion { Publicada, EnEvaluacion, Adjudicada, Desierta, Finalizada }

    struct Licitacion {
        uint id;
        string cuce;
        string descripcion;
        EstadoLicitacion estado;
        address creador;
        string hashDBC;
        Propuesta[] propuestas; // <-- AÑADIMOS UNA LISTA DE PROPUESTAS
    }

    uint public contadorLicitaciones;
    mapping(uint => Licitacion) public licitaciones;

    // --- EVENTOS ---
    event LicitacionCreada(uint indexed id, string cuce);
    event PropuestaPresentada(uint indexed idLicitacion, address indexed proponente); // <-- NUEVO EVENTO
    event EstadoCambiado(uint indexed id, EstadoLicitacion nuevoEstado);

    constructor() Ownable(msg.sender) {}

    // --- FUNCIONES ---
    function crearLicitacion(string memory _cuce, string memory _descripcion, string memory _hashDBC) public onlyOwner {
        contadorLicitaciones++;
        // Nota que la lista de propuestas se inicializa vacía
        licitaciones[contadorLicitaciones].id = contadorLicitaciones;
        licitaciones[contadorLicitaciones].cuce = _cuce;
        licitaciones[contadorLicitaciones].descripcion = _descripcion;
        licitaciones[contadorLicitaciones].estado = EstadoLicitacion.Publicada;
        licitaciones[contadorLicitaciones].creador = msg.sender;
        licitaciones[contadorLicitaciones].hashDBC = _hashDBC;

        emit LicitacionCreada(contadorLicitaciones, _cuce);
    }

    // --- NUEVA FUNCIÓN PARA PRESENTAR PROPUESTAS ---
    function presentarPropuesta(uint _idLicitacion, string memory _hashPropuesta) public {
        // Verificamos que la licitación exista y esté en estado 'Publicada'
        require(licitaciones[_idLicitacion].id != 0, "La licitacion no existe.");
        require(licitaciones[_idLicitacion].estado == EstadoLicitacion.Publicada, "La licitacion no esta abierta a propuestas.");

        // Creamos la nueva propuesta
        Propuesta memory nuevaPropuesta = Propuesta({
            proponente: msg.sender,
            hashPropuesta: _hashPropuesta,
            timestamp: block.timestamp
        });

        // La añadimos a la lista de propuestas de esa licitación
        licitaciones[_idLicitacion].propuestas.push(nuevaPropuesta);

        emit PropuestaPresentada(_idLicitacion, msg.sender);
    }

    function adjudicar(uint _id) public onlyOwner {
        require(licitaciones[_id].id != 0, "La licitacion no existe.");
        licitaciones[_id].estado = EstadoLicitacion.Adjudicada;
        emit EstadoCambiado(_id, EstadoLicitacion.Adjudicada);
    }

    // --- NUEVA FUNCIÓN PARA LEER LAS PROPUESTAS ---
    function getPropuestas(uint _idLicitacion) public view returns (Propuesta[] memory) {
        return licitaciones[_idLicitacion].propuestas;
    }
}