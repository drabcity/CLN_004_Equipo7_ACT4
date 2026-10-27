import pytest
from decimal import Decimal

from app.domain import (
    InvalidOrderData,
    InvalidOrderTransition,
    Money,
    OrderItem,
    OrderItemLimitExceeded,
)
from app.specifications import discount_rate, ten_percent, five_percent
from cargar_csv import load_fixture


@pytest.fixture
def orders():
    """Datos limpios para cada prueba."""
    return load_fixture()


# ---------------------------------------------------------------
# Money y datos inválidos
# ---------------------------------------------------------------
def test_money_negativo():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("-1"))


def test_money_monedas_distintas():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("10"), "MXN").add(Money(Decimal("10"), "USD"))


def test_order_item_cantidad_cero():
    with pytest.raises(InvalidOrderData):
        OrderItem("SKU001", 0, Money(Decimal("600.00")))


# ---------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------
def test_pedido_o001_inicia_draft(orders):
    assert orders["O001"].status.value == "DRAFT"
    assert orders["O001"].units == 4
    assert orders["O001"].total.amount == Decimal("2100.00")


def test_se_cargan_16_pedidos(orders):
    assert len(orders) == 16


# ---------------------------------------------------------------
# Límite de 20 unidades
# ---------------------------------------------------------------
def test_agregar_supera_20_unidades(orders):
    order = orders["O009"]  # 19 unidades
    item = OrderItem("SKU003", 2, Money(Decimal("120.00")))
    with pytest.raises(OrderItemLimitExceeded):
        order.add_item(item)
    assert order.units == 19  # no se modificó


def test_20_unidades_exactas_se_confirman(orders):
    order = orders["O008"]
    assert order.units == 20
    order.confirm()
    assert order.status.value == "CONFIRMED"


# ---------------------------------------------------------------
# Confirmación
# ---------------------------------------------------------------
def test_cliente_inactivo_no_confirma(orders):
    order = orders["O003"]
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.status.value == "DRAFT"
    assert order.events == []


def test_pedido_vacio_no_confirma(orders):
    order = orders["O007"]
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.status.value == "DRAFT"
    assert order.events == []


def test_confirmacion_doble(orders):
    order = orders["O013"]
    order.confirm()
    assert order.status.value == "CONFIRMED"
    assert [e.name for e in order.events] == ["OrderConfirmed"]

    with pytest.raises(InvalidOrderTransition):
        order.confirm()
    assert [e.name for e in order.events] == ["OrderConfirmed"]


# ---------------------------------------------------------------
# Descuentos (Specifications)
# ---------------------------------------------------------------
def test_descuento_vip_10_por_ciento(orders):
    order = orders["O001"]
    assert ten_percent.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0.10")


def test_descuento_5_por_ciento(orders):
    order = orders["O006"]
    assert five_percent.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0.05")


def test_promocion_activa_excluye_descuento(orders):
    order = orders["O005"]
    assert discount_rate(order) == Decimal("0")


def test_total_exacto_500_no_supera_umbral(orders):
    order = orders["O010"]
    assert order.total.amount == Decimal("500.00")
    assert discount_rate(order) == Decimal("0")


def test_vip_con_3_unidades_sin_descuento(orders):
    order = orders["O011"]
    assert order.units == 3
    assert discount_rate(order) == Decimal("0")


# ---------------------------------------------------------------
# Envío, cancelación, entrega y devolución
# ---------------------------------------------------------------
def test_envio_sin_guia(orders):
    order = orders["O012"]
    order.confirm()
    with pytest.raises(InvalidOrderData):
        order.ship("")
    assert order.status.value == "CONFIRMED"
    assert [e.name for e in order.events] == ["OrderConfirmed"]


def test_cancelar_desde_shipped(orders):
    order = orders["O014"]
    order.confirm()
    order.ship("GUIA123")
    with pytest.raises(InvalidOrderTransition):
        order.cancel("Cliente lo solicitó")
    assert order.status.value == "SHIPPED"


def test_cancelar_sin_motivo(orders):
    order = orders["O013"]
    order.confirm()
    with pytest.raises(InvalidOrderData):
        order.cancel("")
    assert order.status.value == "CONFIRMED"


def test_devolucion_desde_shipped(orders):
    order = orders["O015"]
    order.confirm()
    order.ship("GUIA123")
    order.return_order()
    assert order.status.value == "RETURNED"
    assert [e.name for e in order.events] == [
        "OrderConfirmed", "OrderShipped", "OrderReturned"]


def test_entrega_desde_shipped(orders):
    order = orders["O016"]
    order.confirm()
    order.ship("GUIA123")
    order.deliver()
    assert order.status.value == "DELIVERED"
    assert [e.name for e in order.events] == [
        "OrderConfirmed", "OrderShipped", "OrderDelivered"]
