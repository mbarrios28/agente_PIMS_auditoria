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
#set text(font: "Arial", size: 8.7pt, lang: "es")
#set par(leading: 0.43em, spacing: 0.6em)
#set heading(numbering: none)
#show heading: set text(size: 10pt, fill: rgb("#244e43"))
#align(center)[#text(size: 14pt, weight: "bold")[RIESGO-GESTITEL]
#linebreak()
#text(size: 9pt)[Ficha de entrega · Segunda entrega TIF / EC2 · Grupo 1]]
#v(0.1cm)
*Integrantes:* Barrios Medina Matias Alonso; Carbajal Gonzales Diego Alejandro; Cari Lipe Paul Andree; Mamani Huarsaya Jorge Luis.

= Objetivo, datos y alcance
Identificación, evaluación y tratamiento propuesto de riesgos de privacidad con base normativa exclusiva ISO/IEC 27701:2025. GESTITEL aporta activos, procesos, matriz, evaluaciones y controles como evidencia operativa. Un único agente selecciona herramientas; Python valida argumentos, referencias y cálculos. El resultado conserva supuestos, información faltante y revisión pendiente.

= Arquitectura y orquestación
#align(center)[#image("assets/arquitectura.svg", height: 8.5cm)]
Flask y RunStore ejecutan la tarea. RiskAgent recibe tool_calls del modelo, ejecuta herramientas y devuelve resultados. Groq es principal; Gemini, respaldo configurable. RAG: pypdf, fragmentos de 800 caracteres con 150 de solape, TF-IDF o BM25; solo PDF OCR ISO 27701:2025. SQLite conserva resultado y traza.

= Cláusulas y controles de referencia
#table(columns: (1.05fr, 2.6fr), stroke: 0.4pt + rgb("#bccac4"), inset: 5pt,
  table.header([*ISO/IEC 27701:2025*], [*Función y alcance del agente*]),
  [6.1.2], [Apoya identificación, análisis y evaluación mediante matriz recuperada y estimaciones justificadas. No determina aceptación corporativa.],
  [6.1.3], [Propone opciones, controles y acciones de tratamiento; no aprueba la SoA ni acepta riesgo residual.],
  [8.2 / 8.3], [Apoya reevaluación bajo solicitud y documentación del tratamiento propuesto; no acredita implementación de medidas.],
  [Anexos A / B], [Controles de referencia y orientación de implementación; recuperar fragmentos según rol y escenario. A.3.24 / B.3.24 para copias de información.],
)
#text(size: 7.6pt)[Copia aportada completa: 72 páginas PDF, incluido cuerpo de 64 páginas y anexos A–F. OCR sujeto a contraste visual. La matriz P×I proviene de GESTITEL, no de una fórmula prescrita por ISO. No se afirma certificación.]

= Demostración y acceso
*Demostración técnica, 12 minutos + 3 de preguntas:* entrada → arquitectura → skill → ciclo y herramientas → RAG ISO → conector y cálculo → resultado y evidencia → vista previa. Skill activa: `gestion_riesgos`; las otras tres skills del repositorio son históricas. Abrir la aplicación en `http://127.0.0.1:5000` o el puerto configurado. EC2-DEMO es ficticio y no contiene PII real. Credenciales en `.env`, fuera de la proyección.

*Límites:* contexto de solo lectura; la publicación de propuestas en GESTITEL requiere vista previa y confirmación explícita. La integración está realizada contra la API; no se modifica el frontend externo. Un campo sin evidencia no demuestra ausencia del control. La fórmula P×I está documentada en el Anexo 04 de GESTITEL, páginas PDF 6 y 10; la matriz se consulta en vivo.
