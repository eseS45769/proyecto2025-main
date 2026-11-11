# Saique · Rediseño premium

## Alcance

Nueva identidad compartida para el acceso, la navegación y las superficies de los 14 módulos. Se conservan autenticación, endpoints, permisos, formularios y operaciones existentes.

- Azul noche `#101c30`, dorado `#d5ad6d`, verde `#22675f`, superficies claras.
- Inicio de sesión: Aladdín de Disney y Jazmín sobre la alfombra. Imagen 2D con perspectiva CSS, flotación y respuesta amortiguada al cursor (2.5D). **No es un modelo 3D/WebGL.**
- Glassmorphism: formulario de acceso y cabecera, con fondos legibles sin depender del desenfoque.
- Gradient mesh: iluminación de fondo y bienvenida.
- Kinetic type: entrada breve del título del acceso. Sin animación repetida en tablas o navegación de trabajo.
- Liquid morph: formas orgánicas de la escena; la bienvenida usa movimiento suave de luz con transform/opacity.
- Partículas: 18 elementos decorativos CSS, sin dependencia ni bucle JavaScript permanente.
- Perspectiva/isometría: plano orbital y alfombra; las tablas permanecen planas y legibles.
- Cómic: ilustración Disney en la escena del acceso.
- ASCII, blueprint y pixel art: no se aplican a las pantallas operativas porque introducirían estilos incompatibles con la dirección solicitada.

## Movimiento y accesibilidad

Pausar/activar animación, preferencia `prefers-reduced-motion`, interacciones por teclado, etiquetas visibles, estados de carga/error, mostrar/ocultar contraseña con `aria-pressed`, menú móvil con `aria-expanded`. La respuesta al cursor se desactiva para eventos táctiles y para movimiento reducido. Los listeners de preferencia se liberan al desmontar el acceso.

## Recursos y herramientas

`frontend/assets/aladdin-disney.webp` se convirtió desde el PNG transparente enlazado por https://www.pngaaa.com/detail/3604689 (https://image.pngaaa.com/689/3604689.png). Personajes © Disney. El sitio presenta el recurso para uso no comercial: esta propuesta debe permanecer en revisión hasta sustituirlo por un recurso autorizado para explotación comercial. No se afirma que esta ilustración sea un render 3D ni que sea arte generado por nosotros.

Se consultaron las fuentes de diseño de https://github.com/emilkowalski/skills, https://github.com/pbakaus/impeccable y https://github.com/Leonxlnx/taste-skill. No se instalaron skills en la cuenta del usuario. Figma MCP no está conectado; no se creó ni editó ningún archivo Figma.

## Verificación

- 22 pruebas de backend aprobadas; sintaxis JavaScript y `git diff --check`.
- Playwright del navegador conectado: imagen cargada, sin desbordamiento a 1363 px, pausa/activación y mostrar/ocultar contraseña.
- La suite completa `tests/browser.mjs` no pudo ejecutarse: el entorno rechaza el lanzamiento directo de Chromium (`socket() failed: Operation not permitted`). No se afirma cobertura visual móvil ni del panel autenticado.
- Revisión independiente del acceso de escritorio: ajustados el contraste del texto secundario y la alineación del bloque móvil; falta captura móvil para el visto bueno visual completo.
- El detector de Impeccable señaló el acento lateral y la fuente genérica; se ajustaron. Taste devolvió `GATE: OFF (no build active)`; no se presenta como aprobado.

## Desarrollo

La aplicación continúa ejecutándose con `python -m backend.server`. `npm run dev` es un acceso opcional al mismo servidor; `scripts/preview.py` admite los argumentos de los hosts de vista previa, sin añadir dependencias.
