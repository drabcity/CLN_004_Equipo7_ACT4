# TECHSTORE U4 - NÚCLEO DE NEGOCIO

> **Práctica guiada de la Actividad 4, Unidad 4**  
> **Componentes de la Lógica de Negocios** — FIME, UANL  
> **Equipo:** EQUIPO7
> **Profesor:** Miguel Ángel Gómez Marroquín  

---

## Integrantes

* **Angélica Reyna García** — 2144918
* **Nohemí Delgado Castillo** — 2145346
* **Joselyn María Quiroga Martínez** — 2144717

---

## Objetivo

Implementar el núcleo de lógica de negocio de una tienda ficticia (**TechStore**) aplicando principios de diseño orientado al dominio. Se modelan entidades y objetos de valor (**Order**, **Customer**, **Money** y **OrderItem**) que protegen sus propias reglas e impiden datos inválidos; se encapsulan las reglas de descuento con el patrón *Specification*, combinadas con `AND`, `OR` y `NOT`; y se controla el ciclo de vida de cada pedido con una máquina de estados que registra *Domain Events* solo después de transiciones válidas. La lógica se expone mediante una API REST con **FastAPI** (respuestas 200, 404, 409 y 422) y se valida con pruebas automáticas en **pytest** y con la ejecución de 15 escenarios.

> *Nota:* Los datos viven en memoria: al cerrar el programa, los cambios se pierden. No se usa base de datos.

---

## Contenido del Paquete

* `datos/clientes.csv` — 12 clientes (`es_vip` y `activo`: 1=sí, 0=no)
* `datos/productos.csv` — 12 productos (`precio_mxn` en formato decimal)
* `datos/pedidos.csv` — 16 pedidos, todos inicialmente `DRAFT`
* `datos/detalle_pedidos.csv` — 21 líneas de artículos
* `datos/escenarios.csv` — 15 escenarios de evaluación (E01 a E15)
* `cargar_csv.py` — Convierte los CSV en objetos `Order`

---

## Requisitos e Instalación

### Requisitos previos
* **Python 3.11** o superior
* Paquetes necesarios: `fastapi`, `uvicorn`, `pytest`, `httpx`

### Pasos de instalación

1. **Comprobar la versión y crear el entorno virtual:**
   ```bash
   python --version
   python -m venv .venv
   ```

2. **Activar el entorno virtual:**
   * **Windows PowerShell:** `.venv\Scripts\Activate.ps1`
   * **Windows CMD:** `.venv\Scripts\activate.bat`
   * **macOS / Linux:** `source .venv/bin/activate`

   > *Si PowerShell bloquea la ejecución de scripts, ejecutar antes:*  
   > `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

3. **Instalar las dependencias:**
   ```bash
   python -m pip install fastapi uvicorn pytest httpx
   ```

---

## Ejecución

* **Cargar y mostrar los 16 pedidos en `DRAFT`:**
  ```bash
  python cargar_csv.py
  ```

* **Ejecutar los escenarios E01 a E15 y generar `bitacora.csv`:**
  ```bash
  python escenarios.py
  ```

* **Levantar la API:**
  ```bash
  uvicorn app.api:app --reload
  ```
  * **Documentación (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
  * **Contrato OpenAPI:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

* **Ejecutar las pruebas automáticas:**
  ```bash
  python -m pytest -q
  ```

---

## Estructura del Proyecto

```text
techstore-u4/
├── datos/                  # CSV de clientes, productos, pedidos, detalle y escenarios
├── cargar_csv.py           # Cargador de datos (load_fixture)
├── escenarios.py           # Ejecuta E01-E15 y genera bitacora.csv
├── README.md               # Documentación general del proyecto
├── app/
│   ├── __init__.py
│   ├── domain.py           # Money, Customer, OrderItem, Order, DomainEvent y excepciones
│   ├── specifications.py   # Patrón Specification y reglas de descuento
│   └── api.py              # API REST con FastAPI
├── tests/
│   ├── test_domain.py      # Pruebas del dominio y de las reglas
│   └── test_api.py         # Pruebas de la API (404, 409, 422)
└── evidencias/             # Capturas y bitácora
```

---

## Modelo de Dominio

* **`Money` (Value Object inmutable):** `amount` como `Decimal` y moneda `MXN`. Rechaza montos negativos o no finitos y monedas distintas.
* **`OrderItem` (Value Object):** SKU, cantidad y precio unitario. El subtotal se calcula, no se captura. Rechaza cantidad cero o negativa.
* **`Customer`:** Identificador, si es VIP y si está activo.
* **`Order` (Aggregate Root):** Concentra las reglas del pedido, sus artículos, su estado y sus eventos.

---

## Reglas de Negocio

* `Money` no admite importes negativos; se usa `Decimal`, no `float`.
* **Máximo 20 unidades por pedido:** Se suman cantidades, no se cuentan renglones.
* Solo un pedido en `DRAFT` admite artículos, y solo en `MXN`.
* Para confirmar, el pedido necesita artículos y un cliente activo.
* La existencia (stock) del catálogo es solo contexto: **no se implementa control de inventario**.

---

## Descuentos (Specifications)

* **Descuento 10%:** Cliente VIP, total mayor a 500 MXN (estrictamente), al menos 4 unidades y sin promoción activa.
* **Descuento 5%:** Total mayor a 5000 MXN y sin promoción activa.
* **Prioridad:** Si se cumplen ambas, tiene prioridad el 10%.

> Las *Specifications* se combinan con `&` (AND), `|` (OR) y `~` (NOT) y responden verdadero o falso sin modificar el pedido.

---

## Estados y Domain Events

Cada operación sigue el mismo orden: validar, cambiar el estado y registrar el evento al final. Si la operación es inválida, no cambia el estado ni se agrega ningún evento.

```text
DRAFT --confirm--> CONFIRMED --ship--> SHIPPED --deliver--> DELIVERED
                    |                   |
                  cancel              return
                    |                   |
                CANCELLED            RETURNED
```

| Método | Exige | Evento |
| :--- | :--- | :--- |
| `confirm()` | `DRAFT`, con artículos y cliente activo | `OrderConfirmed` |
| `ship(tracking_number)` | `CONFIRMED` y guía no vacía | `OrderShipped` |
| `cancel(reason)` | `CONFIRMED` y motivo no vacío | `OrderCancelled` |
| `deliver()` | `SHIPPED` | `OrderDelivered` |
| `return_order()` | `SHIPPED` | `OrderReturned` |

---

## Endpoints de la API

* **`GET /orders/{id}`** — Consulta un pedido (estado, unidades, total, renglones y eventos).
* **`POST /orders/{id}/confirm`** — Confirma el pedido.
* **`POST /orders/{id}/ship`** — Envía el pedido. Cuerpo: `{"tracking_number": "GUIA123"}`.
* **`POST /orders/{id}/cancel`** — Cancela el pedido. Cuerpo: `{"reason": "motivo"}`.

> Los endpoints solo buscan el pedido, llaman al método de `Order` y traducen el error; no repiten reglas de negocio.

### Códigos de respuesta
* **`200`** — Operación exitosa.
* **`404`** — El pedido no existe.
* **`409`** — Transición de estado no permitida (`InvalidOrderTransition`).
* **`422`** — Datos inválidos (`InvalidOrderData`, `OrderItemLimitExceeded`).

*Los pedidos se cargan al iniciar el servidor. Para repetir una prueba desde el estado inicial, se reinicia el servidor.*

---

## Escenarios E01 a E15

Cada escenario se ejecuta con `python escenarios.py`, que recarga los datos antes de cada caso. Todos los pedidos parten de `DRAFT`.

* **E01 | O001** — Evaluar descuento  
  * **Resultado:** 10%  
  * **Evento:** ninguno  
  * **Prueba:** `test_descuento_vip_10_por_ciento`
* **E02 | O002** — Evaluar descuento  
  * **Resultado:** 0%  
  * **Evento:** ninguno  
  * **Prueba:** `test_no_vip_sin_descuento`
* **E03 | O003** — Confirmar  
  * **Resultado:** rechazo (`InvalidOrderData`), cliente inactivo  
  * **Evento:** ninguno  
  * **Prueba:** `test_cliente_inactivo_no_confirma`
* **E04 | O005** — Evaluar descuento  
  * **Resultado:** 0% (promoción activa)  
  * **Evento:** ninguno  
  * **Prueba:** `test_promocion_activa_excluye_descuento`
* **E05 | O006** — Evaluar descuento  
  * **Resultado:** 5%  
  * **Evento:** ninguno  
  * **Prueba:** `test_descuento_5_por_ciento`
* **E06 | O007** — Confirmar  
  * **Resultado:** rechazo (`InvalidOrderData`), sin artículos  
  * **Evento:** ninguno  
  * **Prueba:** `test_pedido_vacio_no_confirma`
* **E07 | O008** — Confirmar  
  * **Resultado:** OK, pasa a `CONFIRMED` (20 unidades exactas)  
  * **Evento:** `OrderConfirmed`  
  * **Prueba:** `test_20_unidades_exactas_se_confirman`
* **E08 | O009** — Agregar SKU003 x2  
  * **Resultado:** rechazo (`OrderItemLimitExceeded`), 19 + 2 = 21 unidades  
  * **Evento:** ninguno  
  * **Prueba:** `test_agregar_supera_20_unidades`
* **E09 | O010** — Evaluar descuento  
  * **Resultado:** 0% (total exactamente 500)  
  * **Evento:** ninguno  
  * **Prueba:** `test_total_exacto_500_no_supera_umbral`
* **E10 | O011** — Evaluar descuento  
  * **Resultado:** 0% (VIP con solo 3 unidades)  
  * **Evento:** ninguno  
  * **Prueba:** `test_vip_con_3_unidades_sin_descuento`
* **E11 | O012** — Confirmar y enviar sin guía  
  * **Resultado:** confirma OK; envío rechazado (`InvalidOrderData`)  
  * **Evento:** `OrderConfirmed`  
  * **Prueba:** `test_envio_sin_guia`
* **E12 | O013** — Confirmar dos veces  
  * **Resultado:** 1.º OK; 2.º rechazo (`InvalidOrderTransition`)  
  * **Evento:** `OrderConfirmed` (uno solo)  
  * **Prueba:** `test_confirmacion_doble`
* **E13 | O014** — Confirmar, enviar y cancelar  
  * **Resultado:** cancelación rechazada (`InvalidOrderTransition`)  
  * **Eventos:** `OrderConfirmed`, `OrderShipped`  
  * **Prueba:** `test_cancelar_desde_shipped`
* **E14 | O015** — Confirmar, enviar y devolver  
  * **Resultado:** OK, termina en `RETURNED`  
  * **Eventos:** `OrderConfirmed`, `OrderShipped`, `OrderReturned`  
  * **Prueba:** `test_devolucion_desde_shipped`
* **E15 | O016** — Confirmar, enviar y entregar  
  * **Resultado:** OK, termina en `DELIVERED`  
  * **Eventos:** `OrderConfirmed`, `OrderShipped`, `OrderDelivered`  
  * **Prueba:** `test_entrega_desde_shipped`

---

## Pruebas

`python -m pytest -q` ejecuta las pruebas de dominio (`tests/test_domain.py`) y de API (`tests/test_api.py`). Cubren:
* Money negativo
* Límite de 21 unidades
* Cliente inactivo
* Pedido vacío
* Descuentos de 10% y 5%
* Promoción activa
* Total exacto de 500
* Envío sin guía
* Confirmación doble
* Cancelación desde `SHIPPED`
* Respuestas HTTP 404, 409 y 422

> *Nota:* Si una prueba falla, se corrige la implementación, nunca el resultado esperado.

---

## Evidencias

En la carpeta `evidencias/`:
* Carga de los 16 pedidos
* Bitácora E01-E15 (`bitacora.csv`)
* Ejecución de los escenarios en terminal
* Resultado de `pytest`
* Swagger `/docs`: operación exitosa (200) y rechazos (404, 409 y 422)
