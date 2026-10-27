import csv
from decimal import Decimal

from cargar_csv import load_fixture
from app.domain import DomainException, Money, OrderItem
from app.specifications import discount_rate


def intentar(fn):
    """Ejecuta una operación y devuelve OK o el motivo del rechazo."""
    try:
        fn()
        return "OK"
    except DomainException as exc:
        return f"RECHAZO {type(exc).__name__}: {exc}"


def pct(order):
    return f"{int(discount_rate(order) * 100)}%"


# Cada escenario recibe el pedido y devuelve (operación, resultado real)
def e_descuento(o):
    return "evaluar_descuento", f"descuento {pct(o)}"


def e_confirmar(o):
    return "confirmar", intentar(o.confirm)


def e_agregar(o):
    item = OrderItem("SKU003", 2, Money(Decimal("120.00")))
    return "agregar SKU003 x2", intentar(lambda: o.add_item(item))


def e_confirmar_y_enviar_sin_guia(o):
    r1 = intentar(o.confirm)
    r2 = intentar(lambda: o.ship(""))
    return "confirmar y enviar sin guía", f"confirm: {r1} | ship(''): {r2}"


def e_confirmar_dos_veces(o):
    r1 = intentar(o.confirm)
    r2 = intentar(o.confirm)
    return "confirmar dos veces", f"1.º: {r1} | 2.º: {r2}"


def e_cancelar_desde_shipped(o):
    r1 = intentar(o.confirm)
    r2 = intentar(lambda: o.ship("GUIA123"))
    r3 = intentar(lambda: o.cancel("Cliente lo solicitó"))
    return ("confirmar, enviar y cancelar",
            f"confirm: {r1} | ship: {r2} | cancel: {r3}")


def e_devolver(o):
    r1 = intentar(o.confirm)
    r2 = intentar(lambda: o.ship("GUIA123"))
    r3 = intentar(o.return_order)
    return ("confirmar, enviar y devolver",
            f"confirm: {r1} | ship: {r2} | return: {r3}")


def e_entregar(o):
    r1 = intentar(o.confirm)
    r2 = intentar(lambda: o.ship("GUIA123"))
    r3 = intentar(o.deliver)
    return ("confirmar, enviar y entregar",
            f"confirm: {r1} | ship: {r2} | deliver: {r3}")


ESCENARIOS = [
    ("E01", "O001", e_descuento),
    ("E02", "O002", e_descuento),
    ("E03", "O003", e_confirmar),
    ("E04", "O005", e_descuento),
    ("E05", "O006", e_descuento),
    ("E06", "O007", e_confirmar),
    ("E07", "O008", e_confirmar),
    ("E08", "O009", e_agregar),
    ("E09", "O010", e_descuento),
    ("E10", "O011", e_descuento),
    ("E11", "O012", e_confirmar_y_enviar_sin_guia),
    ("E12", "O013", e_confirmar_dos_veces),
    ("E13", "O014", e_cancelar_desde_shipped),
    ("E14", "O015", e_devolver),
    ("E15", "O016", e_entregar),
]


def main():
    filas = []
    for caso, pedido, fn in ESCENARIOS:
        orders = load_fixture()          # datos limpios para cada caso
        o = orders[pedido]
        estado_inicial = o.status.value
        operacion, resultado = fn(o)
        eventos = [e.name for e in o.events] or "sin eventos"
        filas.append([caso, pedido, estado_inicial, operacion,
                      resultado, o.status.value, str(eventos)])

        print(f"{caso} | {pedido} | {estado_inicial} -> {o.status.value}")
        print(f"     operación : {operacion}")
        print(f"     resultado : {resultado}")
        print(f"     eventos   : {eventos}")
        print()

    with open("bitacora.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["caso", "pedido", "estado_inicial", "operacion",
                    "resultado_real", "estado_final", "eventos"])
        w.writerows(filas)
    print("Bitácora guardada en bitacora.csv (ábrela con Excel).")


if __name__ == "__main__":
    main()
