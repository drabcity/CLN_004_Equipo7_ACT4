TECHSTORE U4 - NUCLEO DE NEGOCIO

Practica guiada de la Actividad 4, Unidad 4
Componentes de la Logica de Negocios - FIME, UANL

Equipo: EQUIPO7 - Modulo Netacad 24
Profesor: Miguel Angel Gomez Marroquin

INTEGRANTES
 Angelica Reyna Garcia ................ 2144918
 Nohemi Delgado Castillo .............. 2145346
 Joselyn Maria Quiroga Martinez ....... 2144717

OBJETIVO
 Implementar el nucleo de logica de negocio de una tienda ficticia (TechStore)
 aplicando principios de diseno orientado al dominio. Se modelan entidades y
 objetos de valor (Order, Customer, Money y OrderItem) que protegen sus propias
 reglas e impiden datos invalidos; se encapsulan las reglas de descuento con el
 patron Specification, combinadas con AND, OR y NOT; y se controla el ciclo de
 vida de cada pedido con una maquina de estados que registra Domain Events solo
 despues de transiciones validas. La logica se expone mediante una API REST con
 FastAPI (respuestas 200, 404, 409 y 422) y se valida con pruebas automaticas
 en pytest y con la ejecucion de 15 escenarios.

 Los datos viven en memoria: al cerrar el programa, los cambios se pierden.
 No se usa base de datos.

CONTENIDO DEL PAQUETE
 datos/clientes.csv ........... 12 clientes (es_vip y activo: 1=si, 0=no)
 datos/productos.csv .......... 12 productos (precio_mxn en formato decimal)
 datos/pedidos.csv ............ 16 pedidos, todos inicialmente DRAFT
 datos/detalle_pedidos.csv .... 21 lineas de articulos
 datos/escenarios.csv ......... 15 escenarios de evaluacion (E01 a E15)
 cargar_csv.py ................ convierte los CSV en objetos Order

REQUISITOS
 - Python 3.11 o superior
 - Paquetes: fastapi, uvicorn, pytest, httpx

INSTALACION
 1. Comprobar la version y crear el entorno virtual:
      python --version
      python -m venv .venv

 2. Activar el entorno virtual:
      Windows PowerShell:  .venv\Scripts\Activate.ps1
      Windows CMD:         .venv\Scripts\activate.bat
      macOS / Linux:       source .venv/bin/activate

    Si PowerShell bloquea la ejecucion de scripts, ejecutar antes:
      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

 3. Instalar las dependencias:
      python -m pip install fastapi uvicorn pytest httpx

EJECUCION
 Cargar y mostrar los 16 pedidos en DRAFT:
      python cargar_csv.py

 Ejecutar los escenarios E01 a E15 y generar bitacora.csv:
      python escenarios.py

 Levantar la API:
      uvicorn app.api:app --reload
    Documentacion (Swagger):  http://127.0.0.1:8000/docs
    Contrato OpenAPI:         http://127.0.0.1:8000/openapi.json

 Ejecutar las pruebas automaticas:
      python -m pytest -q

ESTRUCTURA DEL PROYECTO
 techstore-u4/
   datos/                  CSV de clientes, productos, pedidos, detalle y escenarios
   cargar_csv.py           Cargador de datos (load_fixture)
   escenarios.py           Ejecuta E01-E15 y genera bitacora.csv
   README.txt
   app/
     __init__.py
     domain.py             Money, Customer, OrderItem, Order, DomainEvent y excepciones
     specifications.py     Patron Specification y reglas de descuento
     api.py                API REST con FastAPI
   tests/
     test_domain.py        Pruebas del dominio y de las reglas
     test_api.py           Pruebas de la API (404, 409, 422)
   evidencias/             Capturas y bitacora

MODELO DE DOMINIO
 - Money (Value Object inmutable): amount como Decimal y moneda MXN. Rechaza
   montos negativos o no finitos y monedas distintas.
 - OrderItem (Value Object): SKU, cantidad y precio unitario. El subtotal se
   calcula, no se captura. Rechaza cantidad cero o negativa.
 - Customer: identificador, si es VIP y si esta activo.
 - Order (Aggregate Root): concentra las reglas del pedido, sus articulos,
   su estado y sus eventos.

REGLAS DE NEGOCIO
 - Money no admite importes negativos; se usa Decimal, no float.
 - Maximo 20 unidades por pedido: se suman cantidades, no se cuentan renglones.
 - Solo un pedido en DRAFT admite articulos, y solo en MXN.
 - Para confirmar, el pedido necesita articulos y un cliente activo.
 - La existencia (stock) del catalogo es solo contexto: no se implementa
   control de inventario.

DESCUENTOS (SPECIFICATIONS)
 Descuento 10%: cliente VIP, total mayor a 500 MXN (estrictamente), al menos
                4 unidades y sin promocion activa.
 Descuento 5%:  total mayor a 5000 MXN y sin promocion activa.
 Si se cumplen ambas, tiene prioridad el 10%.

 Las Specifications se combinan con & (AND), | (OR) y ~ (NOT) y responden
 verdadero o falso sin modificar el pedido.

ESTADOS Y DOMAIN EVENTS
 Cada operacion sigue el mismo orden: validar, cambiar el estado y registrar
 el evento al final. Si la operacion es invalida, no cambia el estado ni se
 agrega ningun evento.

   DRAFT --confirm--> CONFIRMED --ship--> SHIPPED --deliver--> DELIVERED
                          |                  |
                       cancel              return
                          |                  |
                      CANCELLED           RETURNED

 Metodo                    Exige                                   Evento
 confirm()                 DRAFT, con articulos y cliente activo   OrderConfirmed
 ship(tracking_number)     CONFIRMED y guia no vacia               OrderShipped
 cancel(reason)            CONFIRMED y motivo no vacio             OrderCancelled
 deliver()                 SHIPPED                                 OrderDelivered
 return_order()            SHIPPED                                 OrderReturned

ENDPOINTS DE LA API
 GET   /orders/{id}           Consulta un pedido (estado, unidades, total,
                              renglones y eventos)
 POST  /orders/{id}/confirm   Confirma el pedido
 POST  /orders/{id}/ship      Envia el pedido. Cuerpo: {"tracking_number": "GUIA123"}
 POST  /orders/{id}/cancel    Cancela el pedido. Cuerpo: {"reason": "motivo"}

 Los endpoints solo buscan el pedido, llaman al metodo de Order y traducen el
 error; no repiten reglas de negocio.

 Codigos de respuesta:
   200  Operacion exitosa
   404  El pedido no existe
   409  Transicion de estado no permitida (InvalidOrderTransition)
   422  Datos invalidos (InvalidOrderData, OrderItemLimitExceeded)

 Los pedidos se cargan al iniciar el servidor. Para repetir una prueba desde
 el estado inicial, se reinicia el servidor.

ESCENARIOS E01 A E15
 Cada escenario se ejecuta con python escenarios.py, que recarga los datos
 antes de cada caso. Todos los pedidos parten de DRAFT.

 E01 | O001 | Evaluar descuento
     | Resultado: 10%
     | Evento: ninguno
     | Prueba: test_descuento_vip_10_por_ciento

 E02 | O002 | Evaluar descuento
     | Resultado: 0%
     | Evento: ninguno
     | Prueba: test_no_vip_sin_descuento

 E03 | O003 | Confirmar
     | Resultado: rechazo (InvalidOrderData), cliente inactivo
     | Evento: ninguno
     | Prueba: test_cliente_inactivo_no_confirma

 E04 | O005 | Evaluar descuento
     | Resultado: 0% (promocion activa)
     | Evento: ninguno
     | Prueba: test_promocion_activa_excluye_descuento

 E05 | O006 | Evaluar descuento
     | Resultado: 5%
     | Evento: ninguno
     | Prueba: test_descuento_5_por_ciento

 E06 | O007 | Confirmar
     | Resultado: rechazo (InvalidOrderData), sin articulos
     | Evento: ninguno
     | Prueba: test_pedido_vacio_no_confirma

 E07 | O008 | Confirmar
     | Resultado: OK, pasa a CONFIRMED (20 unidades exactas)
     | Evento: OrderConfirmed
     | Prueba: test_20_unidades_exactas_se_confirman

 E08 | O009 | Agregar SKU003 x2
     | Resultado: rechazo (OrderItemLimitExceeded), 19 + 2 = 21 unidades
     | Evento: ninguno
     | Prueba: test_agregar_supera_20_unidades

 E09 | O010 | Evaluar descuento
     | Resultado: 0% (total exactamente 500)
     | Evento: ninguno
     | Prueba: test_total_exacto_500_no_supera_umbral

 E10 | O011 | Evaluar descuento
     | Resultado: 0% (VIP con solo 3 unidades)
     | Evento: ninguno
     | Prueba: test_vip_con_3_unidades_sin_descuento

 E11 | O012 | Confirmar y enviar sin guia
     | Resultado: confirma OK; envio rechazado (InvalidOrderData)
     | Evento: OrderConfirmed
     | Prueba: test_envio_sin_guia

 E12 | O013 | Confirmar dos veces
     | Resultado: 1.o OK; 2.o rechazo (InvalidOrderTransition)
     | Evento: OrderConfirmed (uno solo)
     | Prueba: test_confirmacion_doble

 E13 | O014 | Confirmar, enviar y cancelar
     | Resultado: cancelacion rechazada (InvalidOrderTransition)
     | Eventos: OrderConfirmed, OrderShipped
     | Prueba: test_cancelar_desde_shipped

 E14 | O015 | Confirmar, enviar y devolver
     | Resultado: OK, termina en RETURNED
     | Eventos: OrderConfirmed, OrderShipped, OrderReturned
     | Prueba: test_devolucion_desde_shipped

 E15 | O016 | Confirmar, enviar y entregar
     | Resultado: OK, termina en DELIVERED
     | Eventos: OrderConfirmed, OrderShipped, OrderDelivered
     | Prueba: test_entrega_desde_shipped

PRUEBAS
 python -m pytest -q ejecuta las pruebas de dominio (tests/test_domain.py) y de
 API (tests/test_api.py). Cubren: Money negativo, limite de 21 unidades,
 cliente inactivo, pedido vacio, descuentos de 10% y 5%, promocion activa,
 total exacto de 500, envio sin guia, confirmacion doble, cancelacion desde
 SHIPPED y respuestas HTTP 404, 409 y 422.
 Si una prueba falla, se corrige la implementacion, nunca el resultado esperado.

EVIDENCIAS
 En la carpeta evidencias/:
 - Carga de los 16 pedidos
 - Bitacora E01-E15 (bitacora.csv)
 - Ejecucion de los escenarios en terminal
 - Resultado de pytest
 - Swagger /docs: operacion exitosa (200) y rechazos (404, 409 y 422)
