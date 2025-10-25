import json
import traceback
import hashlib
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from web3 import Web3
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import List

# --- CONFIGURACIÓN ---
SEPOLIA_RPC_URL = "https://sepolia.infura.io/v3/fb6f15c8f10a441d9517c7de47824903"
CONTRACT_ADDRESS = "0x5b94EEFBdbF46A8cD5c0323A70e7FB27c074F759"
OWNER_PRIVATE_KEY = "c981f8e45694694629b65b079631ae464b04dba92252a7f01985258438f63e4f"

with open("GestorLicitaciones.json", "r") as f:
    CONTRACT_ABI = json.load(f)["abi"]

# --- SIMULACIÓN DE BASE DE DATOS ---
proponentes_db = {}

# --- MODELOS DE DATOS (PYDANTIC) ---
class ProponenteCreate(BaseModel):
    username: str
    password: str

class Licitacion(BaseModel):
    cuce: str
    descripcion: str
    hashDBC: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Propuesta(BaseModel):
    proponente: str
    hashPropuesta: str
    timestamp: int

# --- CONFIGURACIÓN DE SEGURIDAD ---
SECRET_KEY = "tu_clave_secreta_super_dificil"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- INICIALIZACIÓN ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- CONEXIÓN A BLOCKCHAIN ---
w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
owner_account = w3.eth.account.from_key(OWNER_PRIVATE_KEY)
w3.eth.default_account = owner_account.address
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# --- RUTAS PÚBLICAS ---
@app.get("/")
def read_root():
    return {"message": "Backend funcionando", "is_connected": w3.is_connected()}

@app.get("/licitaciones")
def get_all_licitaciones():
    total = contract.functions.contadorLicitaciones().call()
    resultado = []
    for i in range(1, total + 1):
        data = contract.functions.licitaciones(i).call()
        resultado.append({"id": data[0], "cuce": data[1], "descripcion": data[2], "estado": data[3]})
    return resultado

# --- NUEVO ENDPOINT CON DEPURACIÓN ---
@app.get("/licitaciones/{licitacion_id}")
def get_licitacion_by_id(licitacion_id: int):
    print(f"--- Buscando licitacion con ID: {licitacion_id} ---")
    try:
        data = contract.functions.licitaciones(licitacion_id).call()
        print(f"Datos recibidos del contrato: {data}")
        
        if data[0] == 0:
            print("--- Licitacion NO encontrada (ID recibido del contrato es 0) ---")
            raise HTTPException(status_code=404, detail="Licitacion no encontrada")

        resultado = {
            "id": data[0], "cuce": data[1], "descripcion": data[2], 
            "estado": data[3], "creador": data[4], "hashDBC": data[5]
        }
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener la licitacion: {str(e)}")


# --- RUTAS DE AUTENTICACIÓN Y CREACIÓN ---
@app.post("/proponentes/registro")
async def registrar_proponente(proponente: ProponenteCreate):
    if proponente.username in proponentes_db:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    proponentes_db[proponente.username] = proponente.password
    return {"username": proponente.username, "status": "registrado exitosamente"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == "adminpass":
        token_data = {"sub": form_data.username, "role": "admin"}
    elif form_data.username in proponentes_db and proponentes_db[form_data.username] == form_data.password:
        token_data = {"sub": form_data.username, "role": "proponente"}
    else:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    
    jwt_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": jwt_token, "token_type": "bearer"}

@app.post("/licitaciones")
async def create_licitacion(licitacion: Licitacion, token: str = Depends(oauth2_scheme)):
    try:
        tx = contract.functions.crearLicitacion(
            licitacion.cuce, licitacion.descripcion, licitacion.hashDBC
        ).build_transaction({
            'from': owner_account.address, 'nonce': w3.eth.get_transaction_count(owner_account.address)
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=OWNER_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return {"status": "exitoso", "tx_hash": tx_hash.hex()}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/licitaciones/{licitacion_id}/propuesta")
async def submit_propuesta(licitacion_id: int, file: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    try:
        contents = await file.read()
        file_hash = "0x" + hashlib.sha256(contents).hexdigest()
        print(f"Archivo recibido: {file.filename}, Hash calculado: {file_hash}")

        tx = contract.functions.presentarPropuesta(
            licitacion_id, file_hash
        ).build_transaction({
            'from': owner_account.address, 'nonce': w3.eth.get_transaction_count(owner_account.address)
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=OWNER_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {"status": "propuesta recibida", "file_hash": file_hash, "tx_hash": tx_hash.hex()}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- RUTA PROTEGIDA PARA VER LAS PROPUESTAS DE UNA LICITACIÓN ---
@app.get("/licitaciones/{licitacion_id}/propuestas", response_model=List[Propuesta])
async def get_propuestas_de_licitacion(licitacion_id: int, token: str = Depends(oauth2_scheme)):
    try:
        # Llamamos a la función 'getPropuestas' de nuestro contrato inteligente
        propuestas_data = contract.functions.getPropuestas(licitacion_id).call()
        
        # Formateamos la respuesta para que coincida con nuestro modelo Pydantic
        resultado = []
        for p in propuestas_data:
            resultado.append({
                "proponente": p[0],
                "hashPropuesta": p[1],
                "timestamp": p[2]
            })
            
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
# RUTA PROTEGIDA PARA VER LAS PROPUESTAS DE UNA LICITACIÓN
@app.get("/licitaciones/{licitacion_id}/propuestas", response_model=List[Propuesta])
async def get_propuestas_de_licitacion(licitacion_id: int, token: str = Depends(oauth2_scheme)):
    try:
        # Llamamos a la función 'getPropuestas' de nuestro contrato inteligente
        propuestas_data = contract.functions.getPropuestas(licitacion_id).call()

        # Formateamos la respuesta para que coincida con nuestro modelo Pydantic
        resultado = []
        for p in propuestas_data:
            resultado.append({
                "proponente": p[0],
                "hashPropuesta": p[1],
                "timestamp": p[2]
            })

        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
# --- RUTA PROTEGIDA PARA ADJUDICAR UNA LICITACIÓN ---
@app.post("/licitaciones/{licitacion_id}/adjudicar")
async def adjudicar_licitacion(licitacion_id: int, token: str = Depends(oauth2_scheme)):
    try:
        # Aquí podríamos añadir una lógica para verificar que el rol del token es 'admin'.
        # Por ahora, solo verificamos que el usuario esté logueado.

        print(f"--- Intentando adjudicar licitacion con ID: {licitacion_id} ---")

        # Construimos y enviamos la transacción para llamar a la función 'adjudicar'
        tx = contract.functions.adjudicar(
            licitacion_id
        ).build_transaction({
            'from': owner_account.address,
            'nonce': w3.eth.get_transaction_count(owner_account.address)
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=OWNER_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"--- Licitacion {licitacion_id} adjudicada exitosamente. ---")

        return {"status": "licitacion adjudicada", "tx_hash": tx_hash.hex()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))