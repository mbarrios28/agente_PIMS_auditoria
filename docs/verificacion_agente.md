# Verificación del avance con herramientas

Ejecutada el 27 de octubre de 2026 (America/Lima). Se utilizó la clave existente en `.env`, sin mostrarla ni copiarla al repositorio. Las pruebas reales consumieron cuota de Groq.

## Consulta de EC1 — proveedor real

Objetivo: identificar los tres componentes generales de un agente LLM según el survey de Xi et al.

Resultado: una conclusión que identifica cerebro, percepción y acción, con referencia al archivo `2309.07864v3.pdf`, página 10. El extracto efectivamente contiene esa enumeración. Se ejecutaron carga de skill, búsqueda documental y finalización; el ciclo también manejó una llamada de herramienta rechazada por el proveedor y una pausa de cuota. Duración de la ejecución completada: 35.8 segundos.

## Auditoría SQL — proveedor real

Entrada: `web/demo.sql`, seis tablas. Resultado completado:

| Medida | Resultado |
|---|---|
| Tablas declaradas revisadas | 6 |
| Hallazgos | 4 |
| Prioridad alta / media / baja | 2 / 2 / 0 |
| Decisiones del modelo, incluidos borradores rechazados | 8 |
| Solicitudes, incluidas pausas/reintentos de cuota | 16 |
| Borradores rechazados antes de corregirse | 2 |
| Duración | 251.7 segundos |
| Fuente recuperada | `ley_29733_smv_2025.pdf` |
| Skill utilizada en esta ejecución | `auditoria_sql` |

Los hallazgos se refieren a `persona`, `usuario`, `tratamiento_dato` e `incidente_privacidad`. Los cuatro incluyen referencias y evidencia que existe literalmente en el SQL original. El programa verificó esta condición también sobre el resultado completo guardado temporalmente.

La secuencia observada incluyó cargar skill, inspeccionar esquema, buscar documentación, validar tres borradores y finalizar únicamente después de una validación aceptada. Esta ejecución no eligió las reglas locales ni la skill opcional de control: esas herramientas no son pasos obligatorios de una secuencia fija.

Estos resultados prueban una ejecución completa y sus controles estructurales. No constituyen una evaluación estadística de exactitud ni certifican la pertinencia jurídica o la cobertura de todos los riesgos. Las respuestas y latencias pueden variar.

## Pruebas automáticas y navegador

La suite contiene 42 pruebas sin llamadas remotas: contratos, SQL, recuperación, evidencias falsas, procedencia, compuertas de herramientas, corrección con retroalimentación, límites, pausas por cuota, compresión del contexto, tareas asíncronas, API, chat y PDF.

Se comprobó con Chromium el análisis local (6 tablas, 6 observaciones), la navegación de la nueva sección, la carga del objetivo de EC1 y la biblioteca (9 archivos, 3 avisos de no indexación). Se reprodujo el resultado real de consulta en la interfaz sin hacer otra llamada al proveedor: actividad y referencia visibles, sin errores JavaScript. El diseño móvil se comprobó a 390 píxeles sin desbordamiento horizontal.

## Cómo repetir una prueba real

```bash
.venv/bin/python scripts/verificar_agente.py consulta --salida /tmp/consulta.json
.venv/bin/python scripts/verificar_agente.py auditoria --salida /tmp/auditoria.json
```

Ejecuta una tarea a la vez para la exposición. «Groq configurado» indica presencia de clave, no disponibilidad ni cuota garantizadas. Las pausas por cuota se muestran en la actividad y pueden consumir buena parte del presupuesto de cinco minutos. Si el proveedor no permite completar la tarea dentro del límite, se entrega el error y la traza, sin presentar un borrador como resultado aprobado.

## Actualización: respaldo Gemini

La suite ampliada pasó 54 pruebas. El respaldo se verificó con errores simulados de Groq, límites de llamadas/contexto/salida y un transporte HTTP simulado del SDK que comprueba ruta, parámetros y conservación de metadatos de herramientas. También se verificó que un agente completara una tarea con el proveedor de respaldo simulado y reportara su modelo.

No se hicieron llamadas reales a la API Gemini. No se comprobó la validez, permisos ni cuota de la clave configurada. Las cuotas locales de protección se retiraron posteriormente; el comportamiento actual está documentado en README.


## Corrección del respaldo durante auditoría SQL — 29 de octubre de 2026

Se reprodujo con llamadas reales un HTTP 400 de Gemini: las llamadas previas de Groq carecían de `thought_signature`. Las pruebas simples anteriores no incluían ese historial y por eso respondían correctamente. El router ahora transmite esas acciones y resultados como contexto textual; mantiene intactas las firmas de las llamadas generadas por Gemini.

Después del cambio, el ejemplo SQL de seis tablas completó carga de skill, inspección, búsquedas, corrección de un borrador rechazado, validación y finalización. Duración aproximada: 37 segundos, cuatro llamadas Gemini, un hallazgo validado. La validación verifica estructura y evidencia; no acredita exhaustividad ni cumplimiento. La suite automática pasó 58 pruebas, incluida una regresión de la transición y conservación de firmas.
