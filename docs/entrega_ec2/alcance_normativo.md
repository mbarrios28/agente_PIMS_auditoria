# Correspondencia de diseño del agente — pendiente contraste con ISO completas

Norma principal elegida para el alcance académico: ISO/IEC 27001:2022. ISO/IEC 27005:2022
orienta el proceso de riesgos; ISO/IEC 27002:2022 aportará orientación de controles cuando se incorpore.
La extensión PIMS de ISO/IEC 27701 no se declara cubierta sin su texto y mapeo específico.

| Referencia | Función implementada | Evidencia del proyecto | Límite |
|---|---|---|---|
| 6.1.2 | Identificar escenarios y estimar P/I con matriz recuperada | RiskAgent, calcular_riesgo, referencias y traza | No establece criterios corporativos de aceptación ni certifica una evaluación exhaustiva. |
| 6.1.3 | Proponer estrategia, controles, acciones, rol, plazo y evidencia | finalizar_riesgos y propuesta persistida | No aprueba SoA, no implementa medidas ni acepta riesgo residual. |
| 8.2 | Ejecutar reevaluaciones bajo solicitud y conservar resultados | Ejecuciones e historial SQLite | No hay programación automática por calendario o evento de terceros. |
| 8.3 | Documentar tratamiento propuesto y revisión | Informe JSON/PDF y bitácora de revisión | No demuestra ejecución del tratamiento en la organización. |
| A.5.9 | Fundamentar el escenario en inventario recuperado | Referencia del activo y validación de correspondencia | No administra todo el ciclo de vida del inventario. |
| A.5.15 | Sugerir verificaciones de acceso según escenario | Catálogo recuperable y acciones propuestas | No inspecciona permisos efectivos ni configura accesos. |
| A.8.13 | Proponer verificaciones de copias y restauración | Control del catálogo y caso EC2-DEMO | No ejecuta copias ni prueba restauraciones. |
| A.5.30 | Proponer verificaciones de preparación TIC para continuidad | Catálogo recuperable y acciones propuestas | No realiza pruebas de continuidad. |

Estos códigos y nombres se observaron en los recursos de requisitos y controles de GESTITEL el
5 de noviembre de 2026. Son correspondencias propuestas, no una declaración de cumplimiento
ni transcripción del texto ISO. La validación de redacción y pertinencia queda integrada en la
incorporación pendiente de las normas autorizadas. No se asignan subincisos por analogía.
