# PrivAudit / AgentArch-PIMS

Aplicación local para revisar esquemas SQL e investigar arquitecturas de agentes y privacidad. El agente usa Groq para seleccionar herramientas y adaptar sus acciones a sus resultados. El chat de apoyo se mantiene separado.

## Iniciar

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# Configura GROQ_API_KEY en .env siguiendo .env.example.
./iniciar.sh
```

Abre **http://127.0.0.1:5000**. `PORT=5050 ./iniciar.sh` permite cambiar el puerto.

- **Auditoría de privacidad:** carga `CREATE TABLE`, selecciona dialecto y modo. El modo local aplica reglas sin llamadas remotas. El modo Agente IA selecciona herramientas y muestra actividad incremental.
- **Agente PIMS · EC1:** investiga arquitecturas de agentes, RAG y privacidad con el survey de EC1 y documentos primarios. Entrega conclusiones con citas o declara evidencia insuficiente/fuera de alcance.
- **Asistente de privacidad:** chat con RAG; no ejecuta herramientas del agente ni recibe automáticamente los informes de otra sección.
- **Base de conocimiento:** muestra fragmentos realmente extraídos, avisos de archivos no consultables y enlaces de procedencia.

## Agente y herramientas

`src/priv_audit/agent.py` implementa el ciclo de llamadas a herramientas con el SDK de Groq y `openai/gpt-oss-120b`. El modelo selecciona entre cargar una skill, inspeccionar SQL, aplicar reglas, buscar documentos, validar un informe y finalizar. Python comprueba argumentos y condiciones de entrega. No utiliza el grafo LangGraph histórico para la interfaz actual.

Las skills completas están en `src/priv_audit/skills/`: `auditoria_sql`, `consulta_pims` y `control_evidencia`. El agente debe cargar la skill principal. Sus instrucciones no se indexan como evidencia normativa.

Los informes exigen nombres existentes, evidencia SQL resuelta al texto literal original (tolerando solo diferencias de espacios en la propuesta) y declaración de revisión de todas las tablas. Las citas necesitan ID recuperado y texto literal; archivo, página y URL se resuelven en el servidor. Las referencias normativas del informe requieren fuente primaria o se marcan pendientes. La validación no prueba implicación semántica, exactitud jurídica ni exhaustividad de la revisión.

Hay un máximo de 16 decisiones del modelo y un presupuesto de 300 segundos comprobado entre llamadas. Una llamada en curso puede durar hasta el timeout de 20 segundos para Groq o 25 para Gemini. Los errores de formato de herramientas se devuelven al modelo. Las pausas temporales de cuota tienen hasta ocho reintentos adicionales, sin consumir decisiones, dentro del presupuesto temporal. No se entrega un resultado no validado como éxito.

## Corpus y procedencia

`ISOS/fuentes.json` registra URLs, hashes, fechas y páginas de los recursos públicos descargados. Para obtenerlos explícitamente:

```bash
.venv/bin/python scripts/actualizar_fuentes.py
```

Incluye el survey `2309.07864v3.pdf` de Xi et al., la publicación SMV de la Ley 29733 y el reglamento DS 016-2024-JUS publicado por El Peruano y alojado en el Congreso. Las fichas públicas ISO son síntesis de alcance, no copias íntegras de las normas ni catálogos de controles.

RAG utiliza fragmentos de 800 caracteres con solapamiento de 150, TF-IDF y alternativa BM25. No usa embeddings densos ni OCR. Los PDF sin texto se identifican en la biblioteca. La copia histórica de la ley se conserva pero se excluye del índice cuando está disponible la publicación SMV. `organized.pdf` y `profesor/` no se indexan automáticamente. El agente no navega en Internet en vivo; consulta este corpus local.

## API y estado

- `GET /api/status`: configuración y diagnóstico documental.
- `POST /api/audit`: análisis sincrónico compatible (`mode: local|ai`).
- `POST /api/agent/runs`: inicia tarea `auditoria` o `consulta`, responde 202 con ID.
- `GET /api/agent/runs/<id>`: estado, actividad y resultado/error.
- `POST /api/chat`: chat de apoyo.
- `GET /api/history?limit=50&offset=0`: historial persistente paginado.
- `GET /api/history/<id>`: resultado guardado y objetivo de la consulta.
- `POST /api/report`: PDF de un informe estructurado.

Dos tareas simultáneas; hasta 20 ejecuciones en memoria, con caducidad de terminadas a los 30 minutos. Reiniciar borra las ejecuciones. El historial se guarda en SQLite en `data/history.sqlite3` y permanece después de recargar o reiniciar. Incluye auditorías, consultas EC1, GESTITEL y respuestas del chat; las tareas asíncronas fallidas también conservan error y traza. Desde Historial puedes abrir resultados previos y exportar otra vez los informes SQL. Las ejecuciones activas siguen en memoria: reiniciar no las reanuda. No hay autenticación.

## Privacidad y alcance

Escucha en `127.0.0.1`, para uso individual local. El SQL nunca se ejecuta ni se conecta a bases de datos. No hay un límite específico de 150 000 caracteres ni de 150 KB por archivo SQL; la API conserva un máximo de 1 000 000 bytes por solicitud (incluido el JSON) y de 100 tablas por auditoría. En modo IA se envían a Groq el objetivo/SQL, fragmentos y resultados de herramientas; en chat, también historial reciente. Usa datos de demostración y mantén la clave en `.env`.

La revisión del DDL no observa registros, permisos efectivos, cifrado del servidor ni procesos organizativos. Las prioridades no son incumplimientos confirmados. Ninguna cita o resultado garantiza cumplimiento; requiere revisión humana.

## Validación y exposición

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Las pruebas automáticas no consumen API. Cubren el ciclo con cliente simulado, errores de validación, citas, límites, API y el flujo local. Los scripts históricos de prueba pueden realizar llamadas remotas.

La guía personal actual está en [docs/guia_exposicion_EC1.md](docs/guia_exposicion_EC1.md). El diagnóstico anterior a estas mejoras está en `docs/evaluacion_inicial_EC1.md`.

La verificación con Groq real y las limitaciones observadas están en [docs/verificacion_agente.md](docs/verificacion_agente.md). La auditoría completa del ejemplo tardó aproximadamente cuatro minutos con las pausas de cuota de esta cuenta.

## Respaldo Gemini sin cuotas locales de consumo

Groq sigue siendo el proveedor principal. Si se configura `GEMINI_API_KEY` en `.env`, un timeout, error de conexión, respuesta vacía, HTTP 408/429 o error 5xx puede activar Gemini para continuar la misma tarea. Los errores de autenticación, formato o contexto de Groq no activan Google. Una vez activado, el agente conserva su estado y continúa con Gemini; el chat también dispone del respaldo.

El modelo de respaldo por defecto es `gemini-3.5-flash-lite` y se configura con `GEMINI_MODEL`. La implementación usa la [API compatible de Google](https://ai.google.dev/gemini-api/docs/openai) mediante el SDK de compatibilidad OpenAI apuntando al endpoint de Google. Al cambiar de proveedor, transmite las acciones y resultados previos de Groq como contexto textual: esas llamadas no tienen firmas de Google. Las llamadas nuevas de Gemini conservan íntegros sus metadatos y firmas. El estado y la traza muestran el proveedor utilizado.

La aplicación no impone cuotas de solicitudes, caracteres ni tokens acumulados a Gemini, por tarea o por proceso. Tampoco recorta el contexto a 24 000 caracteres ni limita la salida a 1 536 tokens: transmite el máximo de salida solicitado por el chat o agente. Los contadores de consumo son informativos. Siguen vigentes las cuotas y capacidades de Google, el timeout de 25 segundos y los límites generales del agente (16 decisiones y 300 segundos). No hay reintentos automáticos de errores de Gemini.

Si se activa el respaldo, Google recibe el objetivo, contexto y resultados de herramientas necesarios para continuar.

Las pruebas automáticas de Gemini usan clientes y transporte HTTP simulados. El 29 de octubre de 2026 también se hicieron solicitudes reales de diagnóstico: la clave y el modelo configurado respondieron, y se reprodujo un HTTP 400 al reenviar llamadas de Groq sin firmas Google. Tras corregir la transición, una auditoría real del ejemplo de seis tablas finalizó en 37 segundos con Groq y cuatro llamadas a Gemini; entregó un hallazgo validado. Esto comprueba el flujo, no la exhaustividad de los hallazgos ni la disponibilidad o cuota futura. La clave permanece solo en `.env`, excluido de Git.

## Evaluación de evidencia de GESTITEL

En **Agente PIMS → Fuente de la tarea → Evaluar evidencia de GESTITEL**, escribe un objetivo acotado, por ejemplo revisar la primera página de la matriz de brecha y proponer evidencia a solicitar. Configura `GESTITEL_USERNAME` y `GESTITEL_PASSWORD` en `.env`. La tarea requiere Groq y admite el respaldo Gemini configurado.

El modelo puede seleccionar `consultar_gestitel`, buscar respaldo documental y finalizar con citas a registros recuperados. La conexión usa exclusivamente `https://unsa.27k.pe`: inicia sesión y consulta mediante GET la matriz de brecha, las evaluaciones y el catálogo de controles. No modifica evaluaciones ni asigna niveles. Cada ejecución permite seis consultas de hasta diez registros, con páginas entre 1 y 20: la revisión es parcial y no certifica cumplimiento. Las respuestas restringidas o fallidas se comunican al agente como errores.

Los registros se conservan en memoria durante la tarea y su resultado; las citas incluyen procedencia y el texto recuperado. Cada fragmento registra fecha de consulta. Solo se recuperan campos permitidos, sin responsables ni metadatos de usuarios. El texto libre de evidencia puede contener información personal introducida en GESTITEL: los registros seleccionados se envían a Groq y, si corresponde, Gemini. Solicitudes ARCOP e incidentes no están habilitados en esta integración. Los anexos de `profesor/` siguen sin indexarse automáticamente.

## Material para exponer la integración

- [Guía detallada de uso, arquitectura y exposición con GESTITEL](docs/guia_exposicion_GESTITEL.md).
- [SQL ficticio de prueba para PostgreSQL](ejemplos/prueba_pims_exposicion.sql): importar desde Auditoría de privacidad. Resultado local verificado: 7 tablas, 7 observaciones, 2 altas y 5 medias. No es un volcado de GESTITEL.

El historial conserva objetivos, respuestas, evidencias y trazas en el equipo local; no almacena claves ni credenciales de conexión. La carpeta `data/` está excluida de Git. Puedes cambiar la ubicación con `PIMS_HISTORY_DB`. Las consultas anteriores a esta mejora que ya se perdieron al recargar no se pueden recuperar.
