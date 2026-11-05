# Agente de riesgos de GESTITEL

Implementación del ticket #1. Se ejecuta desde este proyecto; no está desplegada dentro de
la página externa. No requiere el código de GESTITEL para consultar sus recursos permitidos.
La integración visual y las escrituras remotas quedan pendientes del equipo de la plataforma.

## Qué hace

El modelo selecciona herramientas para recuperar contexto, calcular una estimación y entregar
hasta cinco escenarios activo–amenaza–vulnerabilidad–consecuencia. Cada propuesta conserva
referencias, supuestos, información faltante, estrategia, acciones, función responsable propuesta,
plazo propuesto, evidencia a solicitar y necesidad de EIPD. La revisión humana queda pendiente.
Si no hay activos recuperados no puede inventar activos reales. Puede abstenerse de evaluar.

Herramientas: cargar_skill, buscar_documentos, consultar_contexto_riesgos, calcular_riesgo,
finalizar_riesgos. Reutiliza el ciclo del agente, trazas, presupuesto, respaldo de proveedor e
historial SQLite. No ejecuta SQL, no tiene shell y no escribe en GESTITEL.

## Uso

Configura `.env` siguiendo `.env.example`, instala las dependencias e inicia `./iniciar.sh`.
Abre **Agente de riesgos** en el menú.

1. Elige contexto manual o GESTITEL.
2. En manual, describe el activo, los controles conocidos y la evidencia. El botón de ejemplo
   carga un caso ficticio; no es una copia de la universidad ni de GESTITEL.
3. Revisa la metodología JSON. En manual es una propuesta configurable; en GESTITEL se lee
   la matriz activa con uso de riesgos o ambos, y no se permite suplantarla desde la solicitud.
4. Ejecuta. Revisa actividad, supuestos, puntuaciones y tratamiento.
5. Exporta JSON o reabre desde Historial. No hay un botón de aceptación ni publicación remota.

Requiere GROQ_API_KEY. GEMINI_API_KEY es un respaldo opcional. El contexto y registros
seleccionados se envían al proveedor. Las claves y el token de GESTITEL no se envían al modelo.

## Base metodológica

- ISO/IEC 27001 define requisitos del SGSI, incluidos evaluación y tratamiento de riesgos:
  https://www.iso.org/standard/27001
- ISO/IEC 27005 orienta la gestión de riesgos de seguridad:
  https://www.iso.org/standard/80585.html
- ISO/IEC 27002 puede apoyar la selección e implementación de controles.
- ISO/IEC 29134 orienta evaluaciones de impacto en privacidad:
  https://www.iso.org/standard/86012.html

El diseño usa estos alcances como referencia. No incorpora el texto completo de estas normas,
no valida conformidad por cláusula ni garantiza cumplimiento. Los códigos de controles solo
se vinculan a fragmentos del catálogo efectivamente recuperados. Sin ese catálogo, las medidas
se presentan como acciones propuestas y no como controles ISO verificados.

P×I es una decisión explícita del proyecto, no una fórmula obligatoria de ISO. Se comprueban
la escala, cobertura exacta de rangos y ausencia de superposición. El servidor calcula el resultado,
no confía en una cifra escrita por el modelo. Cada cálculo tiene un ID reproducible y conserva
la versión de la metodología y la justificación de los valores. Los valores siguen siendo estimaciones.

En GESTITEL se reutilizan las escalas y bandas de la matriz activa cuando son enteras de 1 a N.
La fórmula del backend de GESTITEL no se ha verificado: no se promete equivalencia de cálculo.
No se calcula riesgo residual ni eficacia a partir de medidas que solo fueron recomendadas.
No hay aceptación automática de riesgos ni aprobación por parte del agente.

## Con qué otros agentes o módulos se relaciona

Estas son dependencias funcionales propuestas, no agentes cuya existencia o interfaces se hayan
confirmado con otros equipos. El acceso actual es mediante API de módulos, no mensajes entre agentes.

| Agente o módulo relacionado | Qué busca el agente de riesgos | Qué devuelve o solicita |
|---|---|---|
| Inventario de activos | Activos, clasificación, valor CID, ubicación e impacto en privacidad | Activos sin contexto suficiente, riesgos asociados y revisión de valoración |
| Procesos | Objetivo, dependencias, criticidad y área | Consecuencias operativas y preguntas sobre tolerancia a interrupciones |
| Metodología | Matriz activa, escalas, criterios de evaluación y versión | Estimaciones reproducibles; solicitud de criterios de aceptación faltantes |
| Controles / cumplimiento / brechas | Controles aplicables, estado y evidencia; distinguir catálogo de implementación | Controles sugeridos, brechas de evidencia y prioridades de revisión |
| Gestión documental | Políticas, procedimientos, aprobaciones y pruebas | Evidencia a solicitar para sustentar probabilidad, impacto y controles |
| Incidentes | Escenarios materializados, causas, frecuencia e impacto | Solicitud de reevaluación y propuestas de tratamiento |
| Auditorías | Hallazgos, observaciones y seguimiento | Riesgos relacionados y evidencia necesaria para verificar acciones |
| Privacidad / EIPD | Tratamientos, categorías de datos, finalidades, transferencias e impacto en personas | Riesgos de privacidad y solicitud de evaluación EIPD |
| Consentimientos / ARCO-P | Señales de fallos del proceso, plazos y finalidades | Escenarios sobre tratamiento indebido o atención de derechos, sin copiar expedientes personales |
| Capacitaciones | Brechas de competencias y evidencia de formación | Acciones formativas como parte del tratamiento |
| Seguridad / usuarios y roles | Evidencia de acceso y segregación, con autorización | Verificaciones de acceso y trazabilidad |

Actualmente el conector de riesgos lee únicamente activos, procesos, evaluaciones de riesgo,
matrices, catálogo de controles, evaluaciones de controles y matriz de brecha. Documentos,
incidentes, auditorías, EIPD, consentimientos, ARCO-P, capacitación y seguridad son dependencias
futuras: no se recuperan automáticamente para el agente. No se contactó a otros equipos.

El agente busca responder: ¿qué puede pasar, a qué activo o proceso, por qué, con qué consecuencias,
qué tan prioritario resulta bajo los criterios definidos y qué debemos hacer y verificar?

## Contrato de integración v1.0

`GET /api/risks/contract` devuelve esquemas JSON de entrada y finalización, metodología de ejemplo
y limitaciones de publicación. El backend integrador debe mapear explícitamente los nombres
locales a sus modelos: este contrato no es una API de GESTITEL ni permite guardar allí.

Inicio manual (las credenciales de proveedor permanecen en el servidor):

```json
{
  "tarea": "riesgos",
  "objetivo": "Evaluar el escenario y proponer tratamiento sin confirmar incumplimientos.",
  "riesgos": {
    "fuente": "manual",
    "contexto": "CASO FICTICIO: servidor de matrículas sin pruebas de restauración disponibles."
  }
}
```

Inicio con GESTITEL:

```json
{
  "tarea": "riesgos",
  "objetivo": "Consulta activos, evaluaciones y matriz activa; no inventes activos si no existen.",
  "riesgos": {"fuente": "gestitel"}
}
```

Ambos se envían a `POST /api/agent/runs`, que devuelve 202 e ID. Consulta
`GET /api/agent/runs/<id>` para traza, estado y resultado. Un error no se presenta como éxito.
El resultado contiene `tipo: riesgos`, `version_contrato: 1.0`, `estado_respuesta`, `riesgos`,
`metodologia`, `alcance`, `fuente`, `limitaciones`, `traza`, `fuentes`, modelo y uso.
Cada propuesta conserva el cálculo completo o null, estado pendiente de revisión y residual null.
El resultado también queda en `/api/history/<id>` tras terminar. Los errores se conservan en historial.

Para una integración futura, cada intercambio entre equipos debería incluir versión de contrato,
ID de correlación, empresa/tenant, IDs de activo/proceso/riesgo, fecha, versión del registro,
fuente, evidencia, datos faltantes y estado de revisión. Esta versión no implementa un bus de
mensajes ni endpoints de recepción de eventos de otros agentes.

La web actual es local e individual, sin autenticación de usuarios ni separación multiempresa.
No debe publicarse como backend compartido. GESTITEL necesita un adaptador autenticado en servidor
que derive empresa y permisos de la sesión, compruebe autorización sobre cada recurso, controle
versiones/duplicados y solicite aprobación del propietario antes de guardar cualquier cambio.
No trasladar tokens ni credenciales al navegador. No se habilita CORS como sustituto de esa integración.

## Consultas y límites

Autenticación en `/business/login/`, y GET únicamente a recursos fijos de `https://unsa.27k.pe`.
Máximo seis páginas por tarea, diez registros por página, páginas 1–20. Se conservan fecha y alcance.
El conector selecciona campos permitidos, omite responsables/metadatos de usuarios y no descarga
adjuntos. El texto libre puede contener datos personales; no garantiza anonimización completa.
Escalas no soportadas, campos truncados, errores de permiso o falta de datos no autorizan inventar resultados.
La matriz se selecciona entre los registros recuperados: no se afirma haber revisado páginas omitidas.

## Validación

Pruebas automáticas: `python -m unittest discover -s tests -v`.
Cubren límites del cálculo, metodología, referencias falsas, controles no recuperados, separación de
herramientas, ausencia de activos, errores corregibles en el ciclo y contrato de API.
Las pruebas simuladas no miden calidad de identificación ni interpretación normativa.
Consultar `docs/verificacion_riesgos.md` para las comprobaciones reales de esta implementación.
