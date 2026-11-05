# Demostración práctica con código — Grupo 1 — 15 minutos

Objetivo: mostrar que RIESGO-GESTITEL ejecuta herramientas, consulta datos reales de la plataforma,
calcula con reglas y publica únicamente con confirmación. No dedicar tiempo a leer el informe.

## Dejar abierto antes de empezar

- Aplicación: http://127.0.0.1:5051 (`PORT=5051 ./iniciar.sh`).
- GESTITEL: https://unsa.27k.pe, con la sesión iniciada antes de proyectar.
- Editor con estas pestañas, en este orden:
  1. `src/priv_audit/agent.py`
  2. `src/priv_audit/gestitel.py`
  3. `src/priv_audit/risk.py`
  4. `src/priv_audit/publication.py`
  5. `src/priv_audit/skills/gestion_riesgos.md`
  6. `src/priv_audit/rag_loader.py` (si pregunta por ISO/RAG).
- Una terminal en la raíz del proyecto. No abrir `.env` ni mostrar contraseñas.

Usar Ctrl+P para abrir el archivo y Ctrl+F para localizar el método indicado abajo.
No recorrer el archivo entero: mostrar la función y enseguida su resultado en la interfaz.

## 0:00–1:00 — Datos de entrada y ejecución

**Mostrar:** GESTITEL → activo `ACT-HW-001`, proceso `EC2-DEMO` y matriz activa.

**Decir:** «Este es un caso ficticio autorizado que está registrado en GESTITEL. El agente no recibe
un contexto escrito a mano: recupera el activo, su proceso y la matriz mediante la API. El caso
no contiene datos personales reales; cualquier consecuencia de privacidad debe declararse como hipótesis».

Cambiar a la aplicación → **Usar objetivo de demostración EC2** → **Preparar evaluación de riesgos**.
Dejar la tarea ejecutándose y comenzar el recorrido de código mientras espera.

## 1:00–3:00 — Archivo principal: dónde está el agente

**Abrir:** `src/priv_audit/agent.py` → `class RiskAgent` → `run()`.

**Señalar:**

- `chat.completions.create`: solicitud al modelo con las herramientas disponibles.
- `message.tool_calls`: acciones propuestas por el modelo.
- `self.execute(name, raw)`: ejecución controlada en Python.
- Mensajes con `role: tool`: resultado real que recibe el modelo para decidir la siguiente acción.
- Límite de turnos/tiempo y manejo de cuota; no hay un bucle ilimitado.

**Decir:** «Aquí se ve el ciclo del agente: el modelo selecciona una acción, Python comprueba y ejecuta,
y el resultado vuelve al modelo. La preparación inicial agrupa consultas fijas; después el modelo
elige herramientas dentro de las permitidas. El texto libre por sí solo no entrega un resultado».

Buscar `available_tools()` y señalar cómo se restringen las acciones según la fase y cómo la
finalización ofrece solamente códigos y referencias que fueron recuperados.

Volver brevemente a **Actividad del agente** para relacionar una acción con este código.
Los motivos mostrados describen acciones; no son una exposición del razonamiento interno del modelo.

## 3:00–4:30 — Conexión comprobable a GESTITEL

**Abrir:** `src/priv_audit/gestitel.py` → `GestitelClient.read()`.

**Señalar:** módulos permitidos, validación de página/ID, ruta `/api/...`, token y selección de campos.
Mostrar únicamente los nombres de variables de entorno del código; nunca sus valores.

**Decir:** «Este conector obtiene registros de la plataforma y adjunta identificador, procedencia y fecha.
El modelo no recibe la contraseña. El contexto operativo sigue viniendo de GESTITEL. El conector de
lectura no permite que el modelo envíe una URL o comando arbitrario».

Si aparece una pausa de cuota en la interfaz, explicar que es una espera del proveedor, no un fallo
silencioso. Continuar con el código sin iniciar tareas duplicadas.

## 4:30–6:00 — Cálculo y validación: qué hace Python

**Abrir:** `src/priv_audit/risk.py` → `Methodology.coverage()` y `calculate()`.

**Señalar:** validación de rangos, multiplicación de probabilidad por impacto, clasificación mediante
las bandas de la matriz e identificador del cálculo.

**Decir:** «El modelo propone y justifica P e I, pero Python realiza el cálculo. La matriz se recupera
de GESTITEL. P×I es su fórmula documentada, no una fórmula universal obligatoria de ISO. Los valores
siguen siendo estimaciones; el valor CID del activo no demuestra automáticamente el impacto del escenario».

Buscar `RiskWorkflow.execute()` y señalar la finalización: resuelve referencias reales, comprueba
que el activo corresponda a la cita y rechaza cálculos inventados. No asigna riesgo residual verificado.

## 6:00–7:00 — Skill e ISO con páginas

**Abrir:** `src/priv_audit/skills/gestion_riesgos.md`.

**Decir:** «Esta skill es el procedimiento del mismo agente. Le exige separar hechos, hipótesis e
información faltante, y distinguir consecuencias para la organización y para las personas».

Si el profesor pregunta cómo llega la ISO al modelo, abrir `rag_loader.py` → `cargar_pdf()` y `_load()`:
extrae por página, divide en fragmentos, conserva procedencia y usa el PDF con OCR sin duplicar el original.
En `agent.py` → `execute()` mostrar los extractos de ISO 27701 incorporados al preparar contexto.

**Mostrar en el resultado:** una referencia a `ISO-IEC-27701-2025-OCR.pdf`, página PDF 13 o 14.
Explicar que es una copia aportada con OCR: las citas importantes y tablas se contrastan con la imagen.
A.8.13 del catálogo pertenece a ISO 27001; no lo presentar como un control renumerado de ISO 27701.

## 7:00–9:00 — Resultado que debe poder explicar cualquier integrante

**Mostrar:** activo, amenaza, vulnerabilidad, consecuencia, P/I, justificaciones, hipótesis,
impacto sobre personas, control citado, acciones y evidencia a solicitar.

**Decir:** «No estamos afirmando que el respaldo no exista. El registro del ejercicio declara copias
sin acta de restauración; por eso proponemos verificar y probar restauración. El cálculo es una
estimación explícita, no un incumplimiento certificado. Si el rol o los datos tratados no se verifican,
el agente debe indicarlo en lugar de inventarlos».

Abrir una referencia operativa y una normativa. Mostrar el resultado en Historial y la exportación
si hay tiempo. La ejecución comprobada con ISO tardó aproximadamente 142 segundos, con pausas,
y entregó un escenario en seis decisiones; no prometer ese tiempo en todas las ejecuciones.

## 9:00–12:00 — Guardado: mostrar código y luego el cambio real aprobado

**Abrir:** `src/priv_audit/publication.py` → `preview()` y `confirm()`.

**Señalar:**

- La vista previa se construye desde la propuesta persistida; el navegador no envía campos arbitrarios.
- `approved is not True`: sin confirmación explícita no se escribe.
- `_context()`: comprueba activo, matriz, período y controles; vuelve a revisar antes de enviar.
- Reserva en SQLite y marcador: evita repetir el envío desde esta instancia.
- `Gateway.write()`: POST para crear, PATCH para actualizar.
- `verify_remote()`: consulta y comprueba el registro devuelto. Si el resultado es incierto, se concilia
  mediante lectura; no se reintenta automáticamente el POST/PATCH.

**Volver a la aplicación:** Registrar en GESTITEL → crear → preparar vista previa.
Revisar datos, hipótesis y planes. Solo si el integrante autoriza esos datos, escribir su nombre,
marcar la aprobación y confirmar el envío. Abrir el panel de riesgos de GESTITEL y comprobar el código
remoto devuelto. Si falla, mostrar el error y no afirmar que se guardó.

**Decir:** «La aprobación del registro no equivale a aceptar riesgo residual ni demostrar que las
medidas fueron implementadas. La aplicación registra una propuesta y conserva la trazabilidad».

Para actualizar debe ser un riesgo abierto del mismo activo y sin evaluación residual; no improvisar
sobre un riesgo ajeno. Los planes y vínculos existentes se conservan durante esa actualización.

## 12:00–15:00 — Preguntas y una prueba de código si la solicita

Para demostrar una validación sin tocar GESTITEL:

```bash
.venv/bin/python -m unittest discover -s tests -p test_publication.py -v
```

Estas pruebas usan datos simulados y verifican aprobación, duplicados, cambios remotos y conciliación.
No presentarlas como envíos reales. La prueba visible en el panel, después de confirmar, es la evidencia
operativa de publicación. Si pide la suite completa: `.venv/bin/python -m unittest discover -s tests -v`.

Respuestas breves:

- **¿Por qué es agente?** Selecciona herramientas, observa resultados y adapta acciones dentro de límites.
- **¿Dónde está la matemática?** `risk.py`, `calculate()`; los parámetros propuestos requieren revisión.
- **¿Dónde está la integración?** `gestitel.py` para lectura y `publication.py` para publicación aprobada.
- **¿Dónde está la ISO?** PDF OCR indexado, fragmentos con página; el original sigue intacto.
- **¿Varios agentes?** Un agente de riesgos; las fuentes son módulos de GESTITEL, no agentes adicionales.
- **¿Qué no demuestra?** Ni conformidad integral, ni implementación efectiva de controles, ni aceptación corporativa.

## Si falla el proveedor durante la exposición

Mostrar la traza y el error. Abrir una ejecución anterior desde Historial y decir expresamente que
es guardada. Continuar con el mismo recorrido de código. No presentarla como ejecución nueva ni
repetir el botón de análisis mientras haya una tarea activa. Mantener la revisión y aprobación de
publicación incluso cuando se use un resultado guardado.
