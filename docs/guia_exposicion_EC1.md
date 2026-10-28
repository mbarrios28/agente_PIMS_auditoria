# Guía personal de exposición — PrivAudit / AgentArch-PIMS, versión con herramientas

Esta guía corresponde al avance implementado el 27 de octubre de 2026. La evaluación anterior se conserva en `evaluacion_inicial_EC1.md` como diagnóstico histórico; sus observaciones sobre ausencia de selección de herramientas ya no describen el núcleo actual.

## Lo principal que debes explicar

Ahora hay **un agente especializado con herramientas y autonomía acotada**, integrado a la aplicación web. El modelo de Groq selecciona acciones, recibe sus resultados, puede reformular búsquedas, obtiene errores de validación y decide cómo corregir el borrador. Python controla las herramientas permitidas, los argumentos, las condiciones de entrega y el presupuesto de ejecución.

El objetivo de una ejecución puede ser revisar un esquema SQL o investigar una consulta sobre arquitecturas de agentes y privacidad. El chat conversacional se conserva en una sección separada y no es la demostración principal.

Esto hace más defendible presentar software agéntico: hay decisiones del modelo sobre acciones ejecutables y retroalimentación real. La referencia conceptual que distingue un agente de un flujo totalmente prefijado es [Building effective agents, Anthropic](https://www.anthropic.com/research/building-effective-agents). No significa que el sistema sea un auditor autónomo certificado ni que su interpretación normativa sea infalible.

## Continuidad con el documento de EC1

En `organized.pdf`, el nombre es AgentArch-PIMS y el núcleo es una skill de «Consulta de Arquitecturas de Agentes de IA con Enfoque en Privacidad (PIMS)», probada en Coze. Ahora la aplicación ofrece esa consulta como una tarea documental con herramientas en **Agente PIMS · EC1**, además de la tarea de auditoría SQL en **Auditoría de privacidad**.

La interfaz, herramientas y control de ejecución son propios, en Python. La generación de lenguaje sigue dependiendo de Groq; no digas que toda dependencia externa desapareció.

Se incorporó el survey `2309.07864v3.pdf` de Xi et al., que aparece en el documento de EC1. Se añadieron textos de la ley publicados por SMV y el reglamento DS 016-2024-JUS desde el Congreso/El Peruano. Cada descarga tiene procedencia y hash en `ISOS/fuentes.json`.

Persisten diferencias con lo escrito en EC1: el recuperador es TF-IDF/BM25, no embeddings densos; no existe garantía de cero alucinaciones; la suficiencia documental es evaluada por el modelo, con validación literal de citas por Python, no una prueba matemática de implicación semántica. No ocultes esas diferencias.

## Arquitectura real

```text
Interfaz web
    │ objetivo / SQL
    ▼
Flask → ejecución acotada en memoria → PrivacyAgent
                                         │
                      ┌──────────────────┴───────────────────┐
                      │ Groq selecciona una herramienta      │
                      │ Python valida y ejecuta la acción    │
                      │ Resultado o error vuelve al modelo   │
                      └──────────────────┬───────────────────┘
                                         │ decisión siguiente
                                         ▼
                          Entrega validada o abstención
```

El motor está en `src/priv_audit/agent.py`. No se utiliza LangGraph en este núcleo: el bucle de herramientas está implementado directamente con el SDK de Groq. `graph.py` y `nodes.py` permanecen como prototipo histórico y no se ejecutan al pulsar los botones de la web.

Flujo fijo y agente no son lo mismo: Python establece límites y compuertas, pero no prescribe una secuencia completa de búsqueda. Por ejemplo, el modelo puede inspeccionar, buscar una norma, aplicar reglas, buscar otra fuente y validar; o inspeccionar, aplicar reglas y buscar después. La tarea de consulta no dispone de herramientas SQL.

## Herramientas que puede elegir

| Herramienta | Qué hace realmente | Restricción principal |
|---|---|---|
| `cargar_skill` | Lee instrucciones Markdown de una lista permitida | No acepta rutas arbitrarias. |
| `inspeccionar_esquema` | Devuelve tablas y campos obtenidos con SQLGlot | Solo en auditoría; nunca ejecuta SQL. |
| `aplicar_reglas_locales` | Detecta indicios por nombres de columnas | Exige inspección previa; no confirma infracciones. |
| `buscar_documentos` | Recupera pasajes con ID, archivo, página y procedencia | Corpus local; no navegación web en vivo. |
| `validar_informe` | Valida estructura, nombres, evidencia SQL y citas | Exige revisión declarada de todas las tablas y búsqueda documental. |
| `finalizar_auditoria` | Entrega por ID un borrador ya validado | No admite otro informe inventado al final. |
| `finalizar_consulta` | Entrega conclusiones con citas o una abstención | Cada conclusión necesita referencias recuperadas y texto literal. |

El modelo no tiene shell, acceso a registros reales, conexión a motores SQL ni capacidad de modificar sistemas. Esas acciones no forman parte de las herramientas expuestas.

## Skills: tres módulos explícitos

Las skills están en `src/priv_audit/skills/` y el modelo elige cargarlas con una herramienta. Ahora se leen como instrucciones completas durante la ejecución; no se confunden con evidencia normativa del RAG.

- `auditoria_sql.md`: cómo revisar el DDL, distinguir indicio de hecho confirmado y preparar el informe.
- `consulta_pims.md`: alcance de EC1, investigación documental, reformulación de búsquedas, propuestas y abstención.
- `control_evidencia.md`: revisión de la solidez del borrador y límites de las citas.

La skill es una unidad reutilizable de instrucciones aplicada junto con herramientas. El archivo de texto por sí solo no ejecuta una auditoría. La aplicación exige la skill principal de la tarea antes de ejecutar las otras acciones; la skill complementaria es opcional.

El antiguo `knowledge/skill_privacidad.md` se conserva para compatibilidad y se excluye del índice de fuentes. No sería correcto citar las propias instrucciones del agente como prueba legal.

## Prompts: cómo se forma cada solicitud

El prompt de sistema, `SYSTEM_PROMPT` en `agent.py`, establece el rol, el dominio, las herramientas, la forma de entrega, los límites y el tratamiento del SQL/documentos como datos no confiables. Pide motivos breves y públicos para las acciones; la actividad visible no contiene razonamiento interno del modelo.

La solicitud del usuario se envía como un objeto con tarea, objetivo, catálogo de documentos, skills disponibles y, cuando corresponde, SQL y dialecto. Las definiciones JSON de herramientas acompañan a la llamada al modelo.

Cada vez que el modelo pide una herramienta, el programa ejecuta la función permitida y agrega un mensaje de rol `tool` con su resultado o error. El siguiente paso lo selecciona el modelo considerando ese nuevo mensaje. Así funciona la retroalimentación.

La configuración del agente usa `openai/gpt-oss-120b` en Groq, temperatura 0.1 y llamadas a herramientas secuenciales. No se reentrenó el modelo ni se creó una red neuronal propia: se construyó un agente sobre un modelo disponible mediante API.

## Auditoría: qué entra y qué sale

Entrada: un esquema con `CREATE TABLE`, dialecto y objetivo adicional opcional. Se valida SQL no vacío, hasta 150 000 caracteres y un máximo de 100 tablas. La capacidad práctica del modo IA también depende del contexto y cuota del proveedor; para exponer usa el ejemplo breve.

SQLGlot interpreta tablas y columnas antes de iniciar el agente. La herramienta de inspección entrega ese resultado real. Las reglas detectan patrones de datos sensibles, credenciales, identificación/contacto y trazabilidad. Su resultado es una pista, no el veredicto definitivo.

Salida: hallazgos con tabla, campos, descripción, evidencia SQL, prioridad ALTO/MEDIO/BAJO, riesgo potencial, información faltante y recomendación. Se añaden referencias documentales, preguntas pendientes, tablas revisadas, skills cargadas, uso de tokens y traza.

Un ejemplo útil: `password VARCHAR(255)` no demuestra almacenamiento en texto plano. El agente puede recomendar verificar hash y acceso, dejando explícito qué evidencia falta. Lo mismo ocurre con cifrado de disco, finalidad o consentimiento: no se deducen únicamente del DDL.

## Validación y corrección

Para que el programa acepte un borrador debe pasar estas comprobaciones:

1. Contrato Pydantic y niveles de riesgo permitidos.
2. Tablas y campos existentes, con nombres exactos.
3. Evidencia SQL resuelta a un fragmento literal continuo del texto original. Si el modelo cambia únicamente los espacios, el programa localiza el pasaje y conserva el texto real; si cambia tipos o contenido, lo rechaza.
4. Declaración de revisión de todas las tablas reales. Esta declaración no prueba por sí sola profundidad ni cobertura semántica.
5. Referencias con ID de fragmento recuperado en esa misma tarea. Si el modelo aporta una cita, debe ser literal; si omite el texto, el servidor adjunta un extracto real de hasta 400 caracteres.
6. Para referencias normativas del informe, fuente marcada como primaria. Si no hay sustento, el programa asigna «pendiente de verificación».

Python obtiene archivo, página y URL desde su propio registro de fragmentos. No acepta que el modelo invente esos metadatos. El criterio normativo final se reconstruye a partir de las referencias aceptadas; no se conserva sin más el texto libre propuesto para ese campo.

Cuando una comprobación falla, el error vuelve al modelo. El modelo puede corregir, buscar otra fuente o cargar instrucciones complementarias. Solo se entrega el ID de un borrador validado.

Límite importante: que una cita exista no demuestra que respalde la interpretación, ni que el riesgo esté bien clasificado. La revisión humana permanece pendiente. El programa no certifica cumplimiento jurídico.

## Consulta de EC1: alcance, evidencia y abstención

La skill de consulta instruye al modelo a comprobar el dominio, buscar documentación y elaborar conclusiones sustentadas. Puede reformular en inglés para encontrar pasajes del survey, que está en inglés. Cada conclusión puede ser documentada o una propuesta de diseño; ambas llevan referencias, pero la propuesta debe identificarse como propuesta.

Hay tres estados de salida: `respondida`, `evidencia_insuficiente` y `fuera_de_alcance`. Para declarar evidencia insuficiente debe haber realizado una búsqueda. En estados de abstención no se entrega una lista de conclusiones sin respaldo: se muestran limitaciones.

El juicio de alcance y suficiencia lo realiza el modelo guiado por la skill. La compuerta programada comprueba la forma de salida y las referencias; no es un clasificador infalible de temas o pertinencia.

## RAG y fuentes

La recuperación usa TF-IDF con unigramas y bigramas, o BM25 si falta scikit-learn. Los documentos se fragmentan en 800 caracteres con solapamiento de 150; se conservan página y fuente cuando están disponibles. El agente puede elegir hasta seis fragmentos por búsqueda y filtrar por archivo.

El catálogo indica cuántos fragmentos hay realmente en cada archivo. Los PDF ISO sin texto extraíble se identifican como tales; no se finge que se han leído. Se incluyeron fichas públicas de ISO con su alcance general, sin inventar artículos o controles. Estas fichas no sustituyen el texto íntegro autorizado.

La copia histórica que mezcla la ley y material antiguo se conserva, pero se excluye del índice cuando está disponible el texto SMV añadido. La fecha de descarga y un hash facilitan trazabilidad; no garantizan por sí mismos que no existan modificaciones normativas posteriores.

Fuentes principales:

- [Survey de Xi et al., versión 3](https://arxiv.org/abs/2309.07864v3).
- [Ley 29733, publicación SMV](https://www.smv.gob.pe/Uploads/Ley_29733_vigente_2025.pdf).
- [DS 016-2024-JUS, Congreso/El Peruano](https://www3.congreso.gob.pe/Docs/DGP/DIDP/files/ds_016-2024-jus.pdf).
- [Ficha pública ISO/IEC 27701](https://www.iso.org/standard/27701).
- [Ficha pública ISO/IEC 42001](https://www.iso.org/standard/42001).

Las descargas se realizan explícitamente con `scripts/actualizar_fuentes.py`. El agente consulta el corpus local; no busca novedades en Internet por sí mismo.

## Qué parte sigue siendo chatbot

**Asistente de privacidad** sigue siendo conversación con RAG y memoria reciente. No selecciona herramientas, no inicia auditorías y no ejecuta el agente. Sirve para ejemplos y explicaciones.

Su historial no recibe automáticamente el informe de otra sección. El núcleo agéntico tiene su propio estado de tarea: skills cargadas, evidencia recuperada, borradores y herramientas. Esa memoria dura durante la ejecución; no aprende ni conserva objetivos entre sesiones.

## Cómo demostrarlo sin slides ni PDF

Ruta sugerida de 8 a 10 minutos, ajustable a la latencia de Groq:

**1. Contexto y EC1 — 1 minuto.** Explica que trasladaron la consulta especializada desde el banco de pruebas a Python e incorporaron una auditoría SQL. Identifica al chat como apoyo y las tareas con herramientas como núcleo.

**2. Consulta de EC1 — 2 minutos.** Abre Agente PIMS, carga el objetivo de ejemplo y ejecuta. Mientras trabaja, señala la carga de skill, la consulta documental y las acciones que realmente aparezcan. Al terminar, abre una cita y distingue la conclusión documental de la propuesta. No prometas un número fijo de pasos.

**3. Auditoría SQL — 3 minutos.** Carga el ejemplo en Auditoría, selecciona Agente IA y ejecuta. Muestra la actividad: qué eligió el modelo, qué devolvió la herramienta y si hubo correcciones. Abre un hallazgo, su evidencia y preguntas pendientes. Si no se produjo un error, no simules uno como si hubiera ocurrido.

**4. Código — 2 minutos.** Muestra `agent.py`: catálogo de herramientas, `execute()` y el bucle que devuelve resultados al modelo. Luego abre una skill. Explica que los límites los hace cumplir Python.

**5. Límites — 1 minuto.** Menciona recuperación léxica, verificación literal y revisión humana. El valor demostrado es completar una tarea con herramientas y evidencia, no garantizar toda decisión normativa.

Si Groq limita temporalmente la cuota, la actividad lo indica y el programa espera antes de reintentar. El modo local sigue disponible, pero debes presentarlo como reglas deterministas, no como una ejecución del agente.

## Respuestas breves para preguntas del ingeniero

**¿Qué lo hace agente?** El modelo elige herramientas disponibles, observa resultados y modifica su siguiente acción hasta entregar una tarea verificable o abstenerse. No se limita a responder una conversación.

**¿Dónde está la autonomía?** En seleccionar la acción y sus argumentos, reformular búsquedas y corregir borradores. La autonomía se limita a las herramientas y condiciones de esta aplicación.

**¿Usaron LangGraph?** Existe un prototipo histórico. La versión web actual ejecuta el bucle de herramientas directamente con el SDK de Groq; no atribuirle una integración inexistente.

**¿Crearon el modelo?** No entrenamos un LLM. Construimos el software, las skills, las herramientas, la memoria de ejecución y los validadores alrededor del modelo servido por Groq.

**¿Qué diferencia tiene con el chat?** La tarea del agente produce acciones ejecutadas, retroalimentación y resultados validados; el chat es conversacional y no dispone de esas herramientas.

**¿El informe está aprobado?** Está validado estructuralmente y con comprobaciones literales. Su interpretación y uso siguen pendientes de revisión humana.

**¿Es multiagente?** No. Es un agente especializado con varias herramientas y skills. No se necesitan múltiples agentes para demostrar agencia.

**¿El RAG garantiza la verdad?** No. Aporta documentos; el validador verifica procedencia y literalidad. La pertinencia y suficiencia pueden fallar.

## Límites prácticos de esta versión

El agente tiene hasta 16 decisiones del modelo y un presupuesto temporal comprobado entre llamadas de 300 segundos; una llamada ya iniciada puede durar hasta su timeout. Las llamadas de formato inválido consumen decisiones; las pausas por cuota permiten hasta ocho reintentos adicionales y siguen consumiendo tiempo. No siempre habrá un resultado final: si falla o alcanza límites, se muestra el error y la actividad, sin presentar un borrador no validado como éxito.

El servidor acepta dos tareas en curso. Conserva hasta 20 ejecuciones en memoria y elimina las terminadas por caducidad después de 30 minutos. Reiniciar el servidor borra ese estado. El historial de auditorías visible está en la pestaña. No hay aprendizaje permanente, login ni aprobación formal de un auditor.

No compartas `.env` en pantalla. En modo IA se envían SQL, objetivo y contexto a Groq. Utiliza solo esquemas de demostración sin registros personales ni secretos.

## Referencia de una ejecución real completada

En la verificación del avance, la consulta del survey se completó en unos 36 segundos. La auditoría de las seis tablas produjo cuatro hallazgos (dos altos y dos medios), corrigió dos borradores rechazados y finalizó en unos cuatro minutos por las pausas de cuota. Son resultados observados, no cifras garantizadas para otra ejecución. Para la exposición ejecuta una tarea a la vez y explica el código mientras trabaja. El registro está en `verificacion_agente.md`.

## Respaldo Gemini

Groq es el proveedor principal. Ante fallos temporales, cuota o respuesta vacía, el agente puede continuar con Gemini sin perder sus skills, evidencia y borradores. La actividad muestra la activación del respaldo; el chat identifica una respuesta de Gemini cuando corresponde. Google recibe el contexto necesario para continuar esa tarea.

El respaldo tiene límites por solicitud, tarea y proceso, descritos en README. Si llega al presupuesto o falla Gemini, se muestra el error y no se reintenta automáticamente Google. La integración se probó con simulaciones, sin gastar la clave de Gemini; no afirmar que esa clave está validada. La duración y los resultados reales anteriores corresponden a Groq.
