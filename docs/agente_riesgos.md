# Agente único de riesgos de GESTITEL

La aplicación expone únicamente el agente de riesgos y su historial. El usuario indica el objetivo;
el contexto operativo proviene exclusivamente de GESTITEL. No hay selector de fuente ni entrada
manual de contexto, metodología, SQL o casos ficticios. La validación también se aplica por API.
Los documentos locales son respaldo normativo, no una fuente alternativa de activos o evidencia operativa.

## Uso

Configura las credenciales de GESTITEL y Groq en `.env`, e inicia `./iniciar.sh`.
Abre la aplicación, indica qué revisar y ejecuta la evaluación. El agente consulta recursos permitidos,
identifica escenarios, propone estimaciones y tratamientos, y cita registros recuperados. Sin activos
suficientes declara evidencia insuficiente. Revisa la actividad y exporta la propuesta en JSON.
El historial muestra solo ejecuciones de riesgos; los registros de funciones anteriores no se borran.

## Metodología

El diseño toma como referencia el alcance público de ISO/IEC 27001 y 27005. No contiene el texto
completo de estas normas ni demuestra conformidad. P×I coincide con Anexo 04 del profesor, páginas PDF 6 y 10;
esta documentación no prueba la versión desplegada en el servidor externo. La matriz activa, escalas y rangos se recuperan de GESTITEL;
no pueden sustituirse desde el cliente. Sin matriz compatible no se ofrecen cálculos.
El servidor valida rangos y calcula el nivel; el modelo justifica los valores como estimaciones.
Los controles solo se vinculan a registros realmente recuperados. El riesgo residual sigue pendiente
hasta verificar las medidas. El modelo no acepta riesgos ni guarda modificaciones remotas por sí solo. La publicación separada requiere vista previa y confirmación explícita.

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

## Contrato de integración v1.2

`GET /api/risks/contract` devuelve esquemas JSON de entrada y propuesta, con fuente fija GESTITEL.

```json
{"tarea":"riesgos","objetivo":"Consulta activos y matriz activa; prepara propuestas con evidencia."}
```

Envía a `POST /api/agent/runs`. Devuelve 202 e ID. Consulta `GET /api/agent/runs/<id>` para actividad,
resultado o error. Se admite opcionalmente `riesgos: {"fuente":"gestitel"}`; cualquier contexto,
metodología manual o tarea diferente se rechaza. Un objetivo no se convierte en evidencia.
El resultado contiene versión, riesgos, metodología recuperada, alcance, referencias y limitaciones.
Cada riesgo exige un activo de GESTITEL y una referencia que corresponda a ese mismo activo.
Se conserva la propuesta en SQLite y se puede reabrir en el historial.

La plataforma externa aún no tiene instalado este agente. La aplicación actual es local e individual,
sin autenticación multiusuario. Una integración futura necesita un adaptador del servidor que derive
empresa y permisos de la sesión, compruebe acceso a cada recurso y requiera aprobación para guardar.
No trasladar credenciales ni tokens al navegador.

Máximo seis páginas por tarea, diez registros por página y páginas 1–20. Se conservan fecha y alcance.
La consulta es parcial. El conector no descarga adjuntos y omite responsables y metadatos de usuarios;
el texto libre no garantiza anonimización completa. Los errores de acceso no significan que el módulo
esté vacío. Las instrucciones incrustadas en registros no son órdenes para el agente.

Ver `docs/verificacion_riesgos.md` para el alcance de las pruebas realizadas.

## Revisión y exportación

`POST /api/history/<id>/review` registra revisor, decisión (`revisado` o `requiere_cambios`)
y comentario. Conserva eventos y huella del resultado sin alterarlo. Es revisión local,
no autenticación de identidad ni aceptación corporativa. `GET /api/risks/report/<id>` exporta
la evaluación persistida con referencias y revisiones en PDF.

La preparación agrupa página 1 de activos, procesos y matrices para evitar errores de navegación.
El detalle por `registro_id` permite recuperar un control sin cargar páginas enteras.
Las consultas siguen limitadas a recursos fijos y seis intentos por ejecución. Algunos endpoints
ignoran `search`; el resultado declara que el filtro es solicitado y requiere comprobar registros.
Tras un cálculo se ofrece la finalización para evitar repetición de acciones; pueden entregarse
escenarios sin puntuación cuando falta evidencia. En Groq se respetan pausas por cuota antes
de recurrir al respaldo por otros errores temporales.

La entrega de EC2 está en `docs/entrega_ec2/`, con PDF reproducible usando UNSAReport.

## Publicación aprobada

La aplicación también permite publicar desde el historial con vista previa y confirmación explícita.
El ciclo del modelo conserva sus herramientas de lectura: no puede aprobar envíos.
Este flujo amplía la versión inicial descrita arriba; ver `docs/publicar_riesgos.md` para los detalles.
