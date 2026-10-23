# Diseño de las interfaces

La referencia visual son las interfaces incrustadas en `Saique_Proyecto_ER_Conectado.docx`. La aplicación usa fondo crema, menú lateral beige, botones gris oscuro, indicadores pastel, tablas blancas y paneles de detalle. Los espacios y formularios se compactaron para reducir el desplazamiento.

| Pantalla | Distribución |
|---|---|
| Inicio | Indicadores, gráfico de ventas, productos destacados, alertas y pedidos recientes. |
| Finanzas | Resumen, movimientos y formulario lateral de ingreso. |
| Reportes | Resúmenes, productos destacados, consultas y exportación. |
| Administración | Usuarios, roles y respaldos en paneles laterales. |
| Reclamos | Lista y detalle del reclamo seleccionado. |
| Pagos | Indicadores, pagos y registro manual lateral. |
| Pedidos | Indicadores de estado, filtros y tabla. |
| Ventas | Totales por período, gráfico, tabla y registro rápido. |
| Clientes | Directorio y ficha del cliente con accesos a sus operaciones. |
| Inventario | Existencias, reservas, disponibilidad y alertas. |
| Productos | Catálogo y detalle de la alfombra seleccionada. |
| Proveedores | Directorio, ficha y acceso a compras. |
| Marketing Digital | Indicadores, publicaciones y consultas. |
| Envíos | Indicadores, estados y tabla de seguimiento. |
| Compras | Registros y acceso a recepción, con el mismo estilo de Proveedores. |

Las 55 operaciones hijas conservan rutas individuales y acceso al padre. Los formularios usan columnas compactas en escritorio y se apilan en móvil. Los accesos contextuales precargan el registro seleccionado. Los filtros operan sobre los datos disponibles y los indicadores se calculan desde la base de datos: las cifras ilustrativas de las capturas no se incorporan como registros.

La creación de cuentas sigue dentro de Administración. El inicio de sesión conserva su funcionamiento y no ofrece registro público.

Implementación: `frontend/panels.js`, `frontend/document-theme.css`, `frontend/app.js` y `backend/panels.py`. Las comprobaciones y capturas están descritas en `VERIFICACION.md`.
