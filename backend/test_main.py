from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 1. Prueba: Verificar conexión (Endpoint /)
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

# 2. Prueba: Obtener lista de licitaciones (Endpoint /licitaciones)
def test_get_licitaciones():
    response = client.get("/licitaciones")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# 3. Prueba: Login exitoso de Administrador
def test_admin_login_success():
    response = client.post(
        "/token",
        data={"username": "admin", "password": "adminpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

# 4. Prueba: Login fallido (contraseña incorrecta)
def test_admin_login_fail():
    response = client.post(
        "/token",
        data={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Usuario o contraseña incorrectos"

# 5. Prueba: Registro de Proponente
def test_register_proponente():
    # Usamos un nombre aleatorio para no fallar si ya existe
    import random
    username = f"empresa_test_{random.randint(1, 10000)}"
    response = client.post(
        "/proponentes/registro",
        json={"username": username, "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "registrado exitosamente"