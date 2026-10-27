import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app import api
from cargar_csv import load_fixture


@pytest.fixture
def client():
    """Cliente de pruebas con los pedidos recargados antes de cada prueba."""
    api.orders.clear()
    api.orders.update(load_fixture())
    return TestClient(api.app)


# ---------------------------------------------------------------
# 404: pedido inexistente
# ---------------------------------------------------------------
def test_confirm_pedido_inexistente_404(client):
    r = client.post("/orders/O999/confirm")
    assert r.status_code == 404


def test_get_pedido_inexistente_404(client):
    r = client.get("/orders/O999")
    assert r.status_code == 404


# ---------------------------------------------------------------
# 200: operaciones exitosas
# ---------------------------------------------------------------
def test_get_pedido_o001(client):
    r = client.get("/orders/O001")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "DRAFT"
    assert data["units"] == 4
    assert Decimal(data["total"]) == Decimal("2100.00")


def test_confirm_exitoso_200(client):
    r = client.post("/orders/O013/confirm")
    assert r.status_code == 200
    assert r.json() == {"id": "O013", "status": "CONFIRMED"}


def test_flujo_confirmar_y_enviar(client):
    client.post("/orders/O012/confirm")
    r = client.post("/orders/O012/ship", json={"tracking_number": "GUIA123"})
    assert r.status_code == 200
    assert r.json()["status"] == "SHIPPED"


# ---------------------------------------------------------------
# 409: transición no permitida
# ---------------------------------------------------------------
def test_confirm_dos_veces_409(client):
    assert client.post("/orders/O013/confirm").status_code == 200
    r = client.post("/orders/O013/confirm")
    assert r.status_code == 409


def test_cancelar_desde_shipped_409(client):
    client.post("/orders/O014/confirm")
    client.post("/orders/O014/ship", json={"tracking_number": "GUIA123"})
    r = client.post("/orders/O014/cancel", json={"reason": "Ya no lo quiero"})
    assert r.status_code == 409


# ---------------------------------------------------------------
# 422: datos inválidos
# ---------------------------------------------------------------
def test_confirm_pedido_vacio_422(client):
    r = client.post("/orders/O007/confirm")
    assert r.status_code == 422


def test_confirm_cliente_inactivo_422(client):
    r = client.post("/orders/O003/confirm")
    assert r.status_code == 422


def test_ship_sin_guia_422(client):
    client.post("/orders/O012/confirm")
    r = client.post("/orders/O012/ship", json={"tracking_number": ""})
    assert r.status_code == 422
    # el pedido sigue CONFIRMED
    assert client.get("/orders/O012").json()["status"] == "CONFIRMED"
