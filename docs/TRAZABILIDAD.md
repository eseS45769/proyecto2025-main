# Correspondencia con el documento

Fuente: Saique_Proyecto_ER_Conectado.docx. Se implementan los 14 casos generales y las 55 operaciones hijas.

## Matriz de operaciones

| Caso | Operación | Interfaz | Método / API | Frontend | Backend |
|---|---|---|---|---|---|
| CU1.1 | Registrar ingreso por venta | P.5.1 | POST /api/finanzas/1 | frontend/modules/finanzas.js | backend/modules/finanzas.py |
| CU1.2 | Consultar ingresos por periodo | P.5.2 | GET /api/finanzas/2 | frontend/modules/finanzas.js | backend/modules/finanzas.py |
| CU1.3 | Controlar cuentas pendientes | P.5.3 | GET /api/finanzas/3 | frontend/modules/finanzas.js | backend/modules/finanzas.py |
| CU1.4 | Generar resumen financiero | P.5.4 | GET /api/finanzas/4 | frontend/modules/finanzas.js | backend/modules/finanzas.py |
| CU2.1 | Generar reporte de ventas | P.6.1 | GET /api/reportes/1 | frontend/modules/reportes.js | backend/modules/reportes.py |
| CU2.2 | Generar reporte financiero | P.6.2 | GET /api/reportes/2 | frontend/modules/reportes.js | backend/modules/reportes.py |
| CU2.3 | Ver productos más vendidos | P.6.3 | GET /api/reportes/3 | frontend/modules/reportes.js | backend/modules/reportes.py |
| CU2.4 | Ver clientes frecuentes | P.6.4 | GET /api/reportes/4 | frontend/modules/reportes.js | backend/modules/reportes.py |
| CU3.1 | Gestionar usuarios | P.7.1 | POST /api/administracion/1 | frontend/modules/administracion.js | backend/modules/administracion.py |
| CU3.2 | Gestionar roles y permisos | P.7.2 | POST /api/administracion/2 | frontend/modules/administracion.js | backend/modules/administracion.py |
| CU3.3 | Realizar backup | P.7.3 | POST /api/administracion/3 | frontend/modules/administracion.js | backend/modules/administracion.py |
| CU3.4 | Restaurar sistema | P.7.4 | POST /api/administracion/4 | frontend/modules/administracion.js | backend/modules/administracion.py |
| CU4.1 | Registrar reclamo | P.4.1 | POST /api/reclamos/1 | frontend/modules/reclamos.js | backend/modules/reclamos.py |
| CU4.2 | Consultar reclamo | P.4.2 | GET /api/reclamos/2 | frontend/modules/reclamos.js | backend/modules/reclamos.py |
| CU4.3 | Actualizar estado de reclamo | P.4.3 | POST /api/reclamos/3 | frontend/modules/reclamos.js | backend/modules/reclamos.py |
| CU4.4 | Cerrar reclamo | P.4.4 | POST /api/reclamos/4 | frontend/modules/reclamos.js | backend/modules/reclamos.py |
| CU5.1 | Registrar pago | P.3.1 | POST /api/pagos/1 | frontend/modules/pagos.js | backend/modules/pagos.py |
| CU5.2 | Verificar pago | P.3.2 | POST /api/pagos/2 | frontend/modules/pagos.js | backend/modules/pagos.py |
| CU5.3 | Generar comprobante | P.3.3 | POST /api/pagos/3 | frontend/modules/pagos.js | backend/modules/pagos.py |
| CU5.4 | Anular pago | P.3.4 | POST /api/pagos/4 | frontend/modules/pagos.js | backend/modules/pagos.py |
| CU6.1 | Registrar pedido | P.2.1 | POST /api/pedidos/1 | frontend/modules/pedidos.js | backend/modules/pedidos.py |
| CU6.2 | Consultar pedido | P.2.2 | GET /api/pedidos/2 | frontend/modules/pedidos.js | backend/modules/pedidos.py |
| CU6.3 | Actualizar pedido | P.2.3 | POST /api/pedidos/3 | frontend/modules/pedidos.js | backend/modules/pedidos.py |
| CU6.4 | Cancelar pedido | P.2.4 | POST /api/pedidos/4 | frontend/modules/pedidos.js | backend/modules/pedidos.py |
| CU7.1 | Registrar venta | P.1.1 | POST /api/ventas/1 | frontend/modules/ventas.js | backend/modules/ventas.py |
| CU7.2 | Ver detalle de venta | P.1.2 | GET /api/ventas/2 | frontend/modules/ventas.js | backend/modules/ventas.py |
| CU7.3 | Listar ventas | P.1.3 | GET /api/ventas/3 | frontend/modules/ventas.js | backend/modules/ventas.py |
| CU7.4 | Anular venta | P.1.4 | POST /api/ventas/4 | frontend/modules/ventas.js | backend/modules/ventas.py |
| CU8.1 | Registrar cliente | P.8.1 | POST /api/clientes/1 | frontend/modules/clientes.js | backend/modules/clientes.py |
| CU8.2 | Consultar clientes | P.8.2 | GET /api/clientes/2 | frontend/modules/clientes.js | backend/modules/clientes.py |
| CU8.3 | Actualizar datos | P.8.3 | POST /api/clientes/3 | frontend/modules/clientes.js | backend/modules/clientes.py |
| CU8.4 | Registrar historial de compra (automática, resultado consultable) | P.8.4 | GET /api/clientes/4 | frontend/modules/clientes.js | backend/modules/clientes.py |
| CU9.1 | Consultar inventario | P.9.1 | GET /api/inventario/1 | frontend/modules/inventario.js | backend/modules/inventario.py |
| CU9.2 | Actualizar stock | P.9.2 | POST /api/inventario/2 | frontend/modules/inventario.js | backend/modules/inventario.py |
| CU9.3 | Generar alerta de stock bajo (automática, resultado consultable) | P.9.3 | GET /api/inventario/3 | frontend/modules/inventario.js | backend/modules/inventario.py |
| CU9.4 | Registrar movimiento de inventario (automática, resultado consultable) | P.9.4 | GET /api/inventario/4 | frontend/modules/inventario.js | backend/modules/inventario.py |
| CU10.1 | Registrar producto | P.10.1 | POST /api/productos/1 | frontend/modules/productos.js | backend/modules/productos.py |
| CU10.2 | Actualizar producto | P.10.2 | POST /api/productos/2 | frontend/modules/productos.js | backend/modules/productos.py |
| CU10.3 | Desactivar producto | P.10.3 | POST /api/productos/3 | frontend/modules/productos.js | backend/modules/productos.py |
| CU10.4 | Publicar catálogo de productos | P.10.4 | POST /api/productos/4 | frontend/modules/productos.js | backend/modules/productos.py |
| CU11.1 | Registrar proveedor | P.11.1 | POST /api/proveedores/1 | frontend/modules/proveedores.js | backend/modules/proveedores.py |
| CU11.2 | Actualizar proveedor | P.11.2 | POST /api/proveedores/2 | frontend/modules/proveedores.js | backend/modules/proveedores.py |
| CU11.3 | Registrar compra de productos | P.11.3 | POST /api/proveedores/3 | frontend/modules/proveedores.js | backend/modules/proveedores.py |
| CU11.4 | Consultar proveedores | P.11.4 | GET /api/proveedores/4 | frontend/modules/proveedores.js | backend/modules/proveedores.py |
| CU12.1 | Publicar productos en TikTok | P.12.1 | POST /api/marketing/1 | frontend/modules/marketing.js | backend/modules/marketing.py |
| CU12.2 | Publicar productos en WhatsApp | P.12.2 | POST /api/marketing/2 | frontend/modules/marketing.js | backend/modules/marketing.py |
| CU12.3 | Responder consultas | P.12.3 | POST /api/marketing/3 | frontend/modules/marketing.js | backend/modules/marketing.py |
| CU12.4 | Visualizar estadísticas | P.12.4 | GET /api/marketing/4 | frontend/modules/marketing.js | backend/modules/marketing.py |
| CU13.1 | Registrar envío | P.13.1 | POST /api/envios/1 | frontend/modules/envios.js | backend/modules/envios.py |
| CU13.2 | Asignar transporte | P.13.2 | POST /api/envios/2 | frontend/modules/envios.js | backend/modules/envios.py |
| CU13.3 | Registrar número de guía | P.13.3 | POST /api/envios/3 | frontend/modules/envios.js | backend/modules/envios.py |
| CU13.4 | Confirmar entrega | P.13.4 | POST /api/envios/4 | frontend/modules/envios.js | backend/modules/envios.py |
| CU14.1 | Registrar compra | P.11.3 | POST /api/compras/1 | frontend/modules/compras.js | backend/modules/compras.py |
| CU14.2 | Consultar compras | P.11.5 | GET /api/compras/2 | frontend/modules/compras.js | backend/modules/compras.py |
| CU14.3 | Actualizar stock por compra (automática, resultado consultable) | P.11.6 | GET /api/compras/3 | frontend/modules/compras.js | backend/modules/compras.py |

## Coherencia del modelo

- Las 35 tablas del diccionario están en backend/schema.sql. sesiones es una tabla técnica adicional.
- pedidos.cliente_id y ventas.cliente_id generan el historial derivado; no hay una tabla de historial duplicada.
- CU11.3 y CU14.1 llaman a backend.business.purchase, bajo una única transacción. CU14.3 consulta la entrada ya realizada.
- Registrar venta consume reservas y registra movimiento de salida. Entregar cambia únicamente seguimiento y pedido.
- Verificar un pago reconoce ingresos.pago_id único. El recibo usa comprobantes_pago.pago_id único.
- Las cantidades físicas se modifican junto al movimiento y el documento, con BEGIN IMMEDIATE y rollback ante error.
- Se usa SQLite con claves foráneas, índices únicos y montos enteros en centavos. Es una adaptación del tipo numeric(12,2) del documento con precisión monetaria exacta.
- Las métricas respetan indicador, valor, fuente y fecha_medicion; los acumulados muestran el último corte, sin sumar cortes anteriores.
- respaldos y restauraciones conservan checksum, copia previa e integridad; el registro externo sobrevive a la restauración.

## Referencias repetidas en el documento

El documento contiene tablas posteriores que repiten por error P.2 para Pagos, P.12 para Envíos y algunos números de hijos. Se sigue la especificación esencial y la tabla RF de la Iteración 3: Pagos P.3, Pedidos P.2 y Envíos P.13. Compras conserva P.11.3, P.11.5 y P.11.6, como exige su reutilización de Proveedores. Los nombres y los códigos CU se mantienen.

## Canales externos

Las instrucciones y prompts de herramientas contenidos en el documento se interpretan como material de especificación del sistema. No conceden autorización para enviar mensajes, publicar contenidos ni contratar servicios. TikTok y WhatsApp se operan con preparación, acción de compartir y evidencia confirmada por el operador.

## Pruebas

tests/test_consistencia.py implementa PR01 a PR12 y comprobaciones adicionales. tests/browser.mjs recorre cada padre e hijo y realiza el flujo del documento mediante formularios. README.md indica cómo repetir las pruebas.
