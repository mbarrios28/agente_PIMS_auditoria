# Guía personal de exposición: PrivAudit y su relación con AgentArch-PIMS de EC1

Documento de apoyo personal. No es una presentación para el profesor ni un informe de cumplimiento normativo. Evaluación basada en `organized.pdf`, el código disponible y pruebas locales ejecutadas el 27 de octubre de 2026. No se modificó la aplicación para preparar esta guía.

## 1. Lo que necesitas tener claro antes de exponer

**Sí existe software funcional para mostrar un avance. Pero no conviene presentarlo como un agente autónomo completo ni como la implementación exacta de todo lo prometido en EC1.**

La aplicación actual tiene dos funciones distintas: un proceso de revisión de esquemas SQL que produce un informe estructurado, y un chat de apoyo con recuperación documental. La primera realiza trabajo sobre un artefacto y verifica parte de su resultado; la segunda conversa. Tu demostración debe concentrarse en la primera.

La clasificación técnica más precisa de la versión actual es **flujo de auditoría asistido por IA, con recuperación documental y corrección acotada por validadores**. Puedes explicar que constituye un avance hacia un agente especializado con autonomía limitada, aclarando exactamente quién decide cada paso. No debes sugerir que el modelo planifica o elige herramientas: eso no está implementado.

¿Cumple las expectativas del ingeniero? Con la única instrucción disponible —presentar el software agéntico de EC1, sin PDF ni diapositivas— cumple la parte de llevar software ejecutable. Cumple parcialmente la continuidad temática y deja pendiente una autonomía más clara. Sin rúbrica adicional no se puede asegurar la calificación ni que el docente acepte llamar agente a este flujo.

## 2. Cómo conectar EC1 con lo que vas a mostrar

En `organized.pdf`, el proyecto se llama **AgentArch-PIMS** y su skill se denomina «Consulta de Arquitecturas de Agentes de IA con Enfoque en Privacidad (PIMS)». Su tarea central es responder consultas sobre arquitecturas de agentes y privacidad a partir de documentos. Coze se presenta como banco de pruebas temporal, con intención de migrar a una implementación propia.

La aplicación actual se llama **PrivAudit** y desarrolla principalmente otra tarea: revisar estructuras SQL para preparar observaciones de privacidad. Conserva el dominio PIMS, un módulo de instrucciones y consulta documental, pero amplía y desplaza el caso de uso. Esa diferencia debe explicarse explícitamente.

Idea para enlazar las etapas, sin memorizarla: en EC1 diseñaron una skill de consulta especializada y la probaron en Coze; en este avance construyeron una aplicación Python propia y aplicaron la revisión de privacidad a un artefacto concreto, el esquema SQL. El chat documental permanece como apoyo. Esta explicación describe una evolución de alcance; no demuestra que toda la skill original haya sido trasladada.

| Lo que plantea EC1 | Lo que existe ahora | Cómo contarlo |
|---|---|---|
| Desacoplamiento de Coze | Flask y módulos Python propios | La interfaz y la orquestación ya son propias; la IA remota sigue dependiendo de Groq. |
| Consulta de arquitecturas de agentes | Chat centrado en privacidad y revisión SQL | El foco cambió; no afirmar equivalencia total. |
| Corpus con survey `2309.07864v3.pdf` y ley | Tres PDF en `ISOS/` y cuatro Markdown | El survey de EC1 no figura en el corpus actual. |
| Recuperación densa por embeddings | TF-IDF; alternativa BM25 | Existe recuperación documental, pero es léxica. |
| Compuerta de alcance estricta | Respuestas básicas y prompt de chat | No hay una compuerta programada que rechace todo tema ajeno al dominio. |
| Compuerta de suficiencia documental | Umbral de similitud y restricciones en prompts | No hay verificación semántica automática de todas las afirmaciones. |
| Síntesis exclusivamente documental | Chat permite explicaciones generales | El comportamiento actual es menos restrictivo que el documento. |
| Cero alucinaciones y verificación cruzada | Validación JSON, nombres y evidencia SQL en auditoría IA | Son controles concretos, no garantía de exactitud normativa. |
| ISO 27701:2019 como referencia | Archivos y prompts que mencionan edición 2025 | Es una diferencia documental que debe conciliarse, sin mezclar numeraciones. |

## 3. Qué mostrar en la aplicación

Abre `http://127.0.0.1:5000`. Prioriza **Auditoría → Cargar ejemplo → Analizar privacidad → abrir un hallazgo**. Luego muestra filtros, historial y, solo como complemento, el chat.

El objeto que recibe la auditoría es un conjunto de sentencias `CREATE TABLE`. No recibe la base de datos real, no ejecuta SQL, no inspecciona filas y no se conecta a un motor de base de datos. Trabaja con nombres, tipos y definiciones de columnas.

El resultado contiene tablas interpretadas, observaciones, evidencia, riesgo potencial, información que falta verificar, recomendación, referencia, resumen, conteos, fuentes y pasos del proceso. Cada resultado lleva identificador, fecha y estado «Pendiente de revisión humana».

La exportación PDF es una salida del producto. Dado que el profesor pidió software, no necesitas abrir un PDF durante la exposición. Puedes mostrar directamente un hallazgo desplegado o el JSON si necesitas evidenciar la estructura.

## 4. Flujo real de auditoría, paso a paso

La interfaz envía el SQL, el modo y el dialecto a `POST /api/audit`. Flask llama a `audit()` en `src/priv_audit/service.py`.

### Entrada y extracción

1. Comprueba que el modo sea `local` o `ai`.
2. Exige SQL no vacío y limita la entrada a 150 000 caracteres.
3. Acepta dialectos MySQL, PostgreSQL, SQLite y T-SQL.
4. SQLGlot interpreta el SQL y obtiene definiciones `CREATE TABLE`, tablas, columnas y tipos.
5. Rechaza entradas sin tablas reconocibles y limita el análisis a 100 tablas.

Esto es análisis sintáctico mediante una biblioteca, no una extracción inventada por el modelo.

### Reglas locales

El programa compara los nombres de columnas con cuatro grupos de patrones:

| Grupo | Ejemplos de patrones | Prioridad que asigna |
|---|---|---|
| Datos de especial atención | `religion`, `salud`, `discapacidad`, `biometr` | ALTO |
| Credenciales y secretos | `password`, `token`, `secret` | ALTO |
| Identificación y contacto | `dni`, `correo`, `telefono`, `direccion` | MEDIO |
| Trazabilidad de personas | `ip_origen`, `ultimo_acceso`, `descripcion` | MEDIO |

Se genera una observación por grupo coincidente y tabla; no necesariamente una por columna ni una por tabla. Son coincidencias de nombres: un término ambiguo puede generar un falso positivo y un sinónimo no contemplado puede pasar inadvertido.

La presencia de `password VARCHAR(255)` permite pedir que se verifique cómo se protegen las credenciales; no permite concluir que las contraseñas están en texto plano. El DDL tampoco prueba por sí solo que falten cifrado de disco, permisos efectivos o consentimiento.

### Si se selecciona modo local

Finaliza con las observaciones de las reglas y un resumen programado. No invoca un LLM ni recupera documentos para esta auditoría. Es un mecanismo determinista útil para mostrar que el software funciona incluso sin servicio remoto; por sí solo no demuestra un agente basado en IA.

### Si se selecciona modo IA

1. Exige que exista `GROQ_API_KEY`.
2. Carga los documentos y construye un recuperador.
3. Busca hasta ocho fragmentos usando términos de privacidad más los nombres de las columnas.
4. Construye un prompt con instrucciones, esquema JSON de salida, tablas exactas, fragmentos y SQL original.
5. Invoca el modelo para generar el informe.
6. Valida la respuesta con Pydantic.
7. Comprueba que las tablas y campos mencionados existan en lo extraído.
8. Exige que cada evidencia sea un fragmento literal del SQL original.
9. Si falla una validación, incorpora el error al prompt y vuelve a generar. Hay como máximo tres intentos de generación y validación.
10. Si no logra una salida válida, devuelve un error; no entrega silenciosamente el resultado local como si fuera IA.

Importante: en modo IA se calculan primero las observaciones locales, pero **no se incluyen como lista de hallazgos en el prompt ni se fusionan con la respuesta**. Cuando la IA produce una respuesta válida, sus observaciones sustituyen las locales. No es un consenso entre dos auditores.

La evidencia literal comprueba que el texto existe en el SQL. No comprueba que el fragmento respalde lógicamente toda la conclusión ni que la norma citada sea correcta. Tampoco se verifica automáticamente la cobertura completa de tablas o la coherencia del conteo que el modelo escribe dentro del resumen; los indicadores de la aplicación sí se calculan desde los hallazgos recibidos.

## 5. Qué tiene de agente y qué le falta

Conviene distinguir una definición amplia de sistema agéntico de una definición estricta de agente. Como referencia técnica, Anthropic diferencia flujos con rutas prefijadas por código de agentes en los que el LLM dirige dinámicamente el proceso y el uso de herramientas. Con ese criterio, esta implementación se acerca más a un workflow. Fuente: [Building effective agents](https://www.anthropic.com/research/building-effective-agents).

| Elemento | Evidencia actual | Límite |
|---|---|---|
| Objetivo concreto | Producir una revisión estructurada del SQL | Lo dispara el usuario. |
| Herramientas | Parser, recuperación, validadores, exportación | El código decide cuándo se usan. |
| Trabajo de varias etapas | Extraer, recuperar, generar, verificar | La secuencia está prefijada. |
| Retroalimentación | Errores del validador regresan al modelo | Corrige restricciones verificadas; no hace una auditoría independiente de veracidad. |
| Estado | Tablas, hallazgos, errores, intentos y resultado durante la ejecución | No hay memoria persistente de objetivos. |
| Autonomía limitada | Completa la tarea tras una solicitud, con reintentos automáticos | No planifica nuevas tareas ni selecciona herramientas. |
| Revisión humana | Informe etiquetado como pendiente | No hay un proceso formal de aprobación y reanudación. |

La parte más defendible como comportamiento agéntico es el ciclo de generación, observación del error y corrección sin pedir al usuario que reformule cada intento. Aun así, ese ciclo está controlado por Python. Tener un bucle o utilizar LangGraph no convierte automáticamente un programa en agente autónomo.

Para responder «¿por qué no es solo un chatbot?», céntrate en el producto completo: recibe un artefacto técnico, lo interpreta, ejecuta una revisión con varias etapas y entrega un objeto estructurado con comprobaciones. Para responder «¿el modelo decide qué hacer?», la respuesta actual es que decide el contenido del informe, mientras la aplicación controla las etapas y validaciones.

## 6. El grafo LangGraph: existe, pero no es el flujo de la web

En `graph.py`, `nodes.py` y `state.py` hay un prototipo con esta estructura:

```text
Inicio → validar → extraer → evaluar → autoevaluar
            │                           │
            └ error → fin               ├ aprobado → fin
                                        ├ menos de 3 intentos → evaluar
                                        └ límite alcanzado → fin
```

El estado incluye SQL, tablas extraídas, hallazgos, errores, iteraciones, aprobación y resumen. El nodo evaluador lee `skill_privacidad.md`, solicita JSON al modelo y, cuando hay reintento, agrega una advertencia.

Pero `web_app.py` invoca `service.audit()`, y la alternativa de consola también usa ese servicio para la auditoría. **No presentes el grafo como si estuviera ejecutándose al pulsar el botón de la web.**

Además, el control de calidad del prototipo es débil: comprueba si la referencia contiene alguno de ciertos números de norma y si el riesgo pertenece a la lista permitida. No verifica el artículo, el control concreto ni su pertinencia. Aunque un mensaje de consola diga que las citas son correctas, esa conclusión excede lo que comprueba el código. La extracción de tablas del prototipo también es más simple que SQLGlot.

## 7. Skills: qué significa aquí exactamente

El archivo `src/priv_audit/knowledge/skill_privacidad.md` reúne identidad, marco de referencia, categorías de datos, escala de riesgo y reglas de redacción. Es un módulo textual de instrucciones y conocimiento del dominio.

Hay que distinguir tres cosas:

- **Prompt:** instrucciones que se entregan al modelo en una invocación.
- **Módulo textual de skill:** instrucciones especializadas reutilizables almacenadas en un archivo.
- **Capacidad ejecutable:** proceso completo que combina instrucciones, funciones, validación y salida.

El archivo Markdown no ejecuta acciones por sí mismo. En el prototipo LangGraph se lee íntegramente y se incorpora al prompt. En la web actual se carga junto con los demás Markdown, se fragmenta y solo sus pasajes recuperados pueden aparecer como contexto. **No se inyecta íntegramente como una skill obligatoria en cada auditoría web.**

No existe un catálogo de skills seleccionadas dinámicamente por el modelo, un gestor de activación ni un sistema de permisos por skill. Llamarlo «módulo de conocimiento e instrucciones especializado en privacidad» describe mejor su implementación actual.

## 8. Prompts y configuración del modelo

### Prompt de auditoría web

Se construye en `service.py`. La instrucción principal es:

> Evalúa riesgos potenciales del esquema, sin afirmar ausencia de controles por ausencia en DDL.

Después indica que SQL y documentos son datos, exige referencias sustentadas o pendientes de verificación y agrega el JSON Schema de `InformeAuditoria`, nombres exactos, contexto y SQL. En reintentos añade «Corrige estos errores:» y el error detectado. Se entrega como una cadena a `llm.invoke()`; no existe aquí la misma separación explícita de mensajes system/usuario que tiene el chat.

### Prompt de chat

`SYSTEM_PROMPT` está en `rag_chat.py` y sí se envía con rol `system`. Define español natural, extensión breve por defecto, alcance de privacidad, límites de la revisión y reglas para no inventar artículos o controles. Permite conversación general y ejemplos, y solicita fuente y página cuando una afirmación normativa tiene apoyo documental.

Los mensajes siguientes son hasta ocho mensajes recientes de historial y una consulta nueva con fragmentos de referencia. Ocho mensajes no significa ocho conversaciones ni ocho pares de pregunta y respuesta.

### Prompt del prototipo LangGraph

`nodes.py` combina el contenido completo de la skill, SQL y una estructura JSON. Pide referencias con número de control y una observación por tabla con riesgo. Sus exigencias y su validador no son equivalentes a los del servicio web; no mezcles ambas implementaciones al explicarlas.

### Modelo configurado

`llm.py` configura `openai/gpt-oss-120b` mediante `ChatGroq`: temperatura 0.1 y formato JSON para auditoría; temperatura 0.2 para chat; timeout de 90 segundos y `max_retries=1` del cliente. Esto describe el código local, no una comprobación de disponibilidad actual del proveedor.

Los reintentos del cliente por errores de llamada son distintos del bucle de hasta tres generaciones por validación. Temperatura baja reduce variación, pero no garantiza determinismo ni veracidad.

## 9. RAG: qué hace y qué no hace

RAG consiste aquí en recuperar fragmentos y agregarlos al contexto del modelo; no reentrena el modelo.

El cargador lee todos los `.md` de `knowledge/` y los PDF de `ISOS/`. Normaliza espacios y crea fragmentos de 800 caracteres con solapamiento de 150. Para PDF conserva archivo y página. No usa OCR ni interpreta automáticamente imágenes.

La búsqueda utiliza TF-IDF con unigramas y bigramas y similitud coseno; si falta scikit-learn, utiliza BM25 simplificado. El chat solicita hasta cinco fragmentos y la auditoría IA hasta ocho. El umbral TF-IDF de 0.01 filtra similitud baja, pero no demuestra que haya evidencia suficiente para responder.

**Hallazgo de la comprobación local:** se cargaron 291 fragmentos: 34 de Markdown y 257 del PDF de la ley. Los PDF `ISO 27701-2025.pdf` e `ISO-42001-2023.pdf` aportaron cero fragmentos. Por tanto, aparecer en Documentos no demuestra que un archivo sea consultable. Para esas ISO el sistema dispone de los resúmenes Markdown, no de texto recuperado de esos PDF en esta ejecución.

`organized.pdf` y los anexos de `profesor/` no se indexan automáticamente. Tampoco está presente en el corpus actual el survey sobre agentes citado en EC1.

Los Markdown incluyen afirmaciones normativas que necesitan revisión. Recuperar una afirmación del archivo de skill no equivale a verificarla contra una norma primaria. Esta guía no valida artículos ni controles legales: evita citar sus números en la exposición como si hubieran sido certificados.

## 10. Qué parte es chatbot

La sección de chat llama a `POST /api/chat`. Sin clave, responde algunos saludos y preguntas básicas con texto programado; para otras consultas muestra fragmentos o explica que no puede elaborar una respuesta abierta. Con clave, combina prompt, historial y documentos y llama al modelo.

Ese módulo no invoca automáticamente `audit()`, no ejecuta el grafo, no solicita herramientas al modelo y no dispara una exportación por iniciativa propia. Además, el informe de auditoría no se adjunta automáticamente al historial del chat: si preguntas «explica mi resultado», el chat no recibe el objeto del informe solo por estar visible en otra sección.

La memoria conversacional está en la pestaña del navegador; se envían los últimos mensajes al servidor para formar la petición. El historial de auditorías también vive en la pestaña y desaparece al recargar. Esto no es aprendizaje ni memoria persistente del agente.

## 11. Ruta sugerida para la exposición: 7 a 10 minutos

### Apertura: problema y continuidad con EC1 — 1 minuto

Ubica la necesidad: revisar estructuras con posibles datos personales y producir observaciones trazables. Explica la evolución de Coze a una aplicación propia y reconoce el cambio de consulta documental a revisión SQL.

### Demostración principal — 3 minutos

Carga el ejemplo. Señala `religion` y `discapacidad` en `persona`, `password` en `usuario` y las columnas de trazabilidad. Ejecuta el modo local para tener una referencia reproducible: **6 tablas, 6 observaciones, 2 altas, 4 medias y 0 bajas** en el código revisado.

Abre una observación y recorre su evidencia, riesgo potencial, información faltante y recomendación. Explica por qué existencia de un campo y ausencia de una política en el DDL no prueban incumplimiento. Usa un filtro para mostrar prioridad.

Si la IA está operativa antes de exponer, muestra también ese modo y explica la recuperación, generación y validación. El número y contenido de observaciones puede variar. No prometas que habrá tres intentos: si la primera salida pasa, se realiza uno. El texto de pasos es un resumen posterior, no una traza detallada en tiempo real de cada herramienta.

### Arquitectura y autonomía — 2 minutos

Muestra `service.py` en el editor: parser, rama IA, construcción del prompt, bucle de tres intentos y validación literal. Esta es la evidencia principal de que hay un proceso ejecutable más allá de la conversación. Si muestras `graph.py`, identifícalo como prototipo que no está integrado en la web.

### Skill y documentos — 1 minuto

Abre `skill_privacidad.md`, explica cómo se reutiliza y distingue su incorporación al prototipo de su recuperación parcial en la web. Muestra un fragmento del chat con su fuente para explicar RAG. No uses la mera lista de documentos como prueba de lectura de todas las ISO.

### Cierre técnico — 1 minuto

Expón lo conseguido y lo pendiente: aplicación propia, revisión SQL estructurada, evidencia verificable y corrección acotada; falta selección dinámica de herramientas, mayor verificación documental y conciliar la skill de EC1 con el alcance actual.

## 12. Preguntas que pueden hacerte

**¿Dónde está el agente?** El núcleo que realiza trabajo es `audit()` con su ciclo de generación y corrección. Con criterio estricto es un workflow con autonomía limitada; el modelo no controla libremente las herramientas.

**¿Por qué no basta ChatGPT?** Aquí el programa interpreta SQL, exige un contrato de salida, contrasta nombres con la entrada y verifica evidencia literal. Son controles específicos implementados alrededor del modelo. No afirmes que un chat genérico jamás podría integrar herramientas semejantes.

**¿Qué decide la IA?** Redacta y propone hallazgos, prioridades, recomendaciones y resumen. Python decide la secuencia, recuperación, validación y reintento.

**¿La autoevaluación es otra IA?** En la web es validación programada con Pydantic y comprobaciones adicionales. No existe un segundo LLM auditor independiente.

**¿Tiene varias skills o agentes?** Hay un archivo especializado y módulos funcionales. No hay un equipo multiagente ni selección dinámica de varias skills.

**¿El RAG elimina alucinaciones?** Aporta contexto. Las validaciones reducen errores concretos, pero no garantizan exactitud normativa ni relevancia de cada cita.

**¿Audita toda la base de datos?** Revisa el DDL interpretado y riesgos potenciales. No observa datos, permisos efectivos ni procesos organizativos.

**¿Puede funcionar sin Internet?** La auditoría local sí, con dependencias instaladas. La generación IA depende de Groq y conexión. La conversación local es limitada.

**¿Qué demuestra que funciona?** El ejemplo produjo el resultado local indicado y pasaron 19 pruebas. Las pruebas de chat IA emplean un modelo simulado; no prueban al proveedor real ni la calidad de un informe generado en vivo.

**¿Qué dato sale del equipo?** En modo IA se envían a Groq el SQL o la consulta, los fragmentos y, en chat, el historial reciente. El modo local de auditoría no necesita enviar el SQL a ese servicio.

## 13. Qué falta para defender mejor la palabra agente

Estas son mejoras propuestas; no están implementadas por preparar este informe:

1. Unificar el alcance y nombre con EC1 o explicar formalmente la evolución del proyecto.
2. Dar al modelo acciones acotadas como inspeccionar esquema, buscar evidencia y solicitar información faltante; permitirle seleccionar la siguiente acción según resultados, con límites de pasos.
3. Conservar estado de la tarea y mostrar decisiones, herramienta elegida, resultado y motivo de continuación o parada.
4. Integrar las instrucciones de la skill de manera explícita y distinguirlas de documentos recuperados.
5. Corregir la extracción de PDF, revisar el corpus y comprobar sustento de citas. Establecer una política clara de suficiencia y abstención.
6. Demostrar un caso donde el sistema cambie su siguiente acción por un resultado intermedio. Eso evidencia autonomía mejor que añadir etiquetas de «agente» a la interfaz.

Integrar el grafo existente sin cambiar su lógica haría visible la orquestación, pero por sí solo no resolvería la selección dinámica de herramientas ni la veracidad normativa.

## 14. Preparación práctica antes de entrar

- Iniciar con `./iniciar.sh` y comprobar que la página carga.
- Tener el ejemplo listo y recordar los resultados locales de referencia.
- Probar el modo IA antes de la exposición: «IA configurada» solo indica presencia de una variable, no una llamada remota exitosa. Durante esta revisión no se hizo una llamada real a Groq.
- Mantener abiertas las pestañas del editor con `service.py`, `schemas.py`, `rag_chat.py` y `skill_privacidad.md`.
- Mantener oculta la clave `.env` al compartir pantalla.
- No depender del chat como demostración central ni de abrir PDFs o slides.
- No decir «cero alucinaciones», «cumplimiento certificado», «LangGraph está corriendo en la web» o «usa embeddings»: el código revisado no respalda esas afirmaciones.

Tu idea central para recordar: **el avance tiene valor porque convierte la revisión en un proceso ejecutable con salida estructurada y controles; su siguiente salto es que el modelo dirija acciones acotadas y verificables.**
