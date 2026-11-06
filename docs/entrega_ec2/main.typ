#import "/components/@unsareport/epis-lab/lib.typ": default-logo-epis
#import "/components/@unsareport/epis-lab-theming/lib.typ": primary-color
#set document(title: "Grupo 1 — Agente de riesgos GESTITEL — EC2", author: ("Barrios Medina Matias Alonso", "Carbajal Gonzales Diego Alejandro", "Cari Lipe Paul Andree", "Mamani Huarsaya Jorge Luis"))
#set page(paper: "a4", margin: (top: 3.0cm, bottom: 1.2cm, left: 1.6cm, right: 1.6cm), header: [#grid(columns: (2.2cm, 1fr), gutter: 0.5cm, align: horizon,
  default-logo-epis,
  [#set text(size: 8pt, weight: "bold")
  UNIVERSIDAD NACIONAL DE SAN AGUSTÍN DE AREQUIPA #linebreak()
  FACULTAD DE INGENIERÍA DE PRODUCCIÓN Y SERVICIOS #linebreak()
  ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS])
  #line(length: 100%, stroke: 0.7pt + primary-color)], footer: align(center)[#text(size: 7.5pt)[Grupo 1 · TIF / EC2 · Aplicación local · 2026]])
#set text(font: "DejaVu Sans", size: 8.7pt, lang: "es")
#set par(leading: 0.43em, spacing: 0.6em)
#set heading(numbering: none)
#show heading: set text(size: 10pt, fill: rgb("#244e43"))
#align(center)[#text(size: 14pt, weight: "bold")[RIESGO-GESTITEL]
#linebreak()
#text(size: 9pt)[Ficha de entrega · Segunda entrega TIF / EC2 · Grupo 1]]
#v(0.1cm)
*Integrantes:* Barrios Medina Matias Alonso; Carbajal Gonzales Diego Alejandro; Cari Lipe Paul Andree; Mamani Huarsaya Jorge Luis.

= Objetivo, datos y alcance
Apoyar la identificación, evaluación y tratamiento propuesto de riesgos de seguridad de la información. El contexto operativo proviene exclusivamente de GESTITEL: activos, procesos, matriz activa, evaluaciones y controles. El usuario indica el objetivo; el agente selecciona herramientas y devuelve escenarios, justificaciones, acciones y evidencia a solicitar. Un único agente; las dependencias de otros módulos son fuentes de datos, no agentes adicionales.

= Arquitectura y orquestación
#image("assets/arquitectura.svg", width: 100%)
Flujo: cargar skill → recuperar contexto → seleccionar herramientas → calcular y verificar → entregar propuesta o evidencia insuficiente → revisión local. Groq es principal y Gemini respaldo ante ciertos fallos. Python valida argumentos, escala, referencias y correspondencia del activo. Hay traza, presupuesto de ejecución e historial persistente.

= Cláusulas y controles de referencia
#table(columns: (1.05fr, 2.6fr), stroke: 0.4pt + rgb("#bccac4"), inset: 5pt,
  table.header([*Referencia ISO/IEC 27001:2022*], [*Función y alcance del agente*]),
  [6.1.2], [Apoya identificación, análisis y evaluación mediante matriz recuperada y estimaciones justificadas. No determina aceptación corporativa.],
  [6.1.3], [Propone opciones, controles y acciones de tratamiento; no aprueba la SoA ni acepta riesgo residual.],
  [8.2 / 8.3], [Apoya reevaluación bajo solicitud y documentación del tratamiento propuesto; no acredita implementación de medidas.],
  [A.5.9 / A.5.15], [Inventario de activos y control de acceso: referencias candidatas según el escenario y catálogo recuperado.],
  [A.8.13 / A.5.30], [Copias de seguridad y preparación TIC para continuidad: referencias candidatas para el caso académico.],
)
#text(size: 7.6pt)[Correspondencias de diseño basadas en el catálogo de GESTITEL. Pendiente incorporar los textos ISO autorizados y contrastar su redacción. ISO/IEC 27005 orienta la metodología; no se afirma certificación ni cobertura completa de las cláusulas.]

= Demostración y acceso
*Modalidad PC:* ejecutar `./iniciar.sh` y abrir `http://127.0.0.1:5000` (o el puerto configurado). No requiere cuenta web local; las credenciales de GESTITEL y proveedor se guardan en `.env` y no se incluyen en esta hoja. Caso EC2-DEMO: proceso y servidor ficticios registrados en GESTITEL, sin datos personales. Mostrar recuperación, evaluación, control citado, tratamiento, revisión, vista previa de publicación e informe. Tiempo previsto: 12 minutos + 3 de preguntas.

*Límites:* contexto de solo lectura; la publicación de propuestas en GESTITEL requiere vista previa y confirmación explícita. La integración está realizada contra la API; no se modifica el frontend externo. Un campo sin evidencia no demuestra ausencia del control. La fórmula P×I está documentada en el Anexo 04 de GESTITEL, páginas PDF 6 y 10; la matriz se consulta en vivo.
