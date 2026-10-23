# Verificación de la implementación

Fecha: 6 de octubre de 2026.

## Pruebas del backend

Comando ejecutado: `python -m unittest discover -s tests -v`.

**Resultado: 22 pruebas aprobadas, sin errores.**

| Criterio del documento | Resultado comprobado |
|---|---|
| PR01 · Recepción válida y repetida | Un documento del proveedor genera una sola compra y entrada, desde ambos módulos. |
| PR02 · Fallo del movimiento | Un fallo simulado revierte compra, detalle y stock. |
| PR03 · Pedidos simultáneos | Una unidad disponible admite una sola reserva; el otro pedido queda pendiente. |
| PR04 · Venta desde reserva | Consume reserva y descuenta físico una vez; bloquea segunda venta del mismo pedido. |
| PR05 · Ajuste bajo reserva | Rechaza el ajuste y conserva físico y documentos. |
| PR06 · Pago repetido | Verificación e ingreso únicos; recibo con el mismo número. |
| PR07 · Anulación de pago y venta | Revierte ingreso y saldo; exige resolver pagos y acreditar devolución o no despacho. |
| PR08 · Alerta y reposición | Una alerta activa por producto; la compra resuelve el stock bajo. |
| PR09 · Entrega | Exige tránsito y evidencia; incidencia conserva tránsito; entrega no cambia stock. |
| PR10 · Documentos ajenos | El cliente no consulta ni paga pedidos ajenos; no accede a Inventario. |
| PR11 · Datos vigentes e históricos | Cambio de precio y dirección actual no modifica la venta ni dirección pactada. |
| PR12 · Restauración | Recupera tablas y archivos, conserva copia previa y registro externo, y verifica integridad. |

Las diez pruebas adicionales comprueban las 55 operaciones, Excel válido sin fórmulas inyectadas, cuentas sin duplicar pedido/venta, métricas del último corte, ausencia de métricas inventadas, cierre secuencial de reclamos, pagos dentro del saldo, protección del último administrador, paneles sin escrituras y aislamiento de documentos en el panel del cliente.

## Prueba del navegador

Comando ejecutado: `node tests/browser.mjs`, usando Chrome sin ventana y datos temporales separados.

- 14 módulos padres abiertos.
- 55 operaciones hijas abiertas, con ruta de regreso al padre.
- Flujo realizado mediante formularios reales: cliente → proveedor → producto → recepción → pedido → pago → verificación → venta → comprobante → envío → transporte → guía → entrega.
- `ALF-001`: compra de 10 unidades, pedido de 3, pago de Bs 540,00 y stock final de 7.
- Envío y pedido entregados.
- Exportación XLSX obtenida correctamente mediante la API.
- Cero excepciones JavaScript registradas.
- Pantalla móvil de 390 píxeles sin desbordamiento horizontal.
- Capturas de escritorio y móvil revisadas visualmente contra las interfaces del documento.
- Estilo crema y menú beige, tablas con panel lateral y formularios hijos compactos.
- Selección de cliente, edición con datos precargados y formulario rápido de Finanzas verificados.
- Administración, Clientes, Pagos e Inventario comprobados también a 390 píxeles.

La evidencia reproducible queda en `test-results/browser.json`, `desktop.png`, `mobile.png` y `server-test.log`. Las pruebas no cargan datos ficticios en la instalación local de `data/`.

Estas comprobaciones cubren los escenarios indicados; no constituyen pruebas de carga ni certificación de un despliegue en producción.
