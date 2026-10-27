from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from cargar_csv import load_fixture
from app.domain import (
    InvalidOrderData,
    InvalidOrderTransition,
    OrderItemLimitExceeded,
)

app = FastAPI(title="TechStore U4")

# Pedidos en memoria: se cargan al iniciar y se pierden al cerrar el servidor.
orders = load_fixture()


# ---------------------------------------------------------------
# Cuerpos de las peticiones
# ---------------------------------------------------------------
class ShipRequest(BaseModel):
    tracking_number: str


class CancelRequest(BaseModel):
    reason: str


# ---------------------------------------------------------------
# Funciones auxiliares (el endpoint NO repite reglas de negocio)
# ---------------------------------------------------------------
def get_order_or_404(order_id: str):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe")
    return order


def execute(order, action):
    """Ejecuta un método de Order y traduce las excepciones a HTTP."""
    try:
        action()
    except InvalidOrderTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except (InvalidOrderData, OrderItemLimitExceeded) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"id": order.id, "status": order.status.value}


# ---------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------
@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = get_order_or_404(order_id)
    return {
        "id": order.id,
        "customer_id": order.customer.id,
        "status": order.status.value,
        "units": order.units,
        "total": str(order.total.amount),
        "currency": order.total.currency,
        "has_promotion": order.has_promotion,
        "items": [
            {
                "sku": i.sku,
                "quantity": i.quantity,
                "unit_price": str(i.unit_price.amount),
                "subtotal": str(i.subtotal.amount),
            }
            for i in order.items
        ],
        "events": [e.name for e in order.events],
    }


@app.post("/orders/{order_id}/confirm")
def confirm_order(order_id: str):
    order = get_order_or_404(order_id)
    return execute(order, order.confirm)


@app.post("/orders/{order_id}/ship")
def ship_order(order_id: str, body: ShipRequest):
    order = get_order_or_404(order_id)
    return execute(order, lambda: order.ship(body.tracking_number))


@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str, body: CancelRequest):
    order = get_order_or_404(order_id)
    return execute(order, lambda: order.cancel(body.reason))
