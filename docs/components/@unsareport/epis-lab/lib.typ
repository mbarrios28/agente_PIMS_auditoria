#import "/components/@unsareport/epis-lab-theming/lib.typ": *
#import "/components/@unsareport/define/lib.typ": define, get-var, get-all-vars
#import "/components/@unsareport/gdocs-code-block/lib.typ": code-block, extract-named-snippet

#let lab-section(
  title,
  align-mode: section-align-mode,
  stroke: section-stroke,
  inset: section-inset,
  header-fill: section-header-fill,
  ..bodies,
) = {
  let cell-items = bodies.pos().map(b => [
    #set text(size: section-body-text-size)
    #b
  ])

  grid(
    align: align-mode,
    stroke: stroke,
    inset: inset,
    columns: 1fr,
    grid.header(
      repeat: false,
      [#grid.cell(fill: header-fill)[
        #set text(size: section-header-text-size, weight: "bold", fill: section-header-text-color)
        #align(center)[#title]
      ]],
    ),
    ..cell-items,
  )
}

#let default-logo-epis = image("img/epis.png", width: 95%)
#let default-logo-abet = image("img/abet.png", width: 97%)

#let page-header(logo-epis: default-logo-epis, logo-abet: default-logo-abet) = block(
  width: 100%,
  inset: (bottom: header-spacing-bottom),
)[
  #table(
    align: center + horizon,
    stroke: table-border-width + header-border-color,
    columns: (1fr, 2fr, 1fr),
    align(horizon)[#if logo-epis != none { logo-epis }],
    table.cell(align: center + horizon)[
      #set text(size: header-institution-text-size, weight: "bold")
      UNIVERSIDAD NACIONAL DE SAN AGUSTÍN \
      FACULTAD DE INGENIERÍA DE PRODUCCIÓN Y SERVICIOS \
      ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS
    ],
    align(horizon)[#if logo-abet != none { logo-abet }],
    table.cell(colspan: 3)[
      #set text(size: header-meta-text-size)
      #text(weight: "bold")[Formato: ]
      Guía de Práctica de Laboratorio / Talleres / Centros de Simulación
    ],
    table.cell[
      #set text(size: header-meta-text-size, weight: "bold")
      Aprobación: 2022/03/01
    ],
    table.cell[
      #set text(size: header-meta-text-size, weight: "bold")
      Código: GUIA-PRLE-001
    ],
    context table.cell(align: right + horizon)[
      #set text(size: header-meta-text-size, weight: "bold")
      Página: #counter(page).display("1")
    ],
  )
]

#let basic-info-table(
  course-name,
  lab-title,
  lab-number,
  year,
  sem-code,
  presentation-date,
  presentation-hour,
  member-list,
  instructor-name,
) = [
  #show table.cell: set text(size: info-table-text-size)
  #table(
    align: left + horizon,
    stroke: table-stroke,
    inset: table-inset,
    columns: (1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    table.cell(colspan: 6, fill: info-header-fill, align: center + horizon)[
      #set text(size: info-header-text-size, weight: "bold", fill: info-header-text-color)
      INFORMACIÓN BÁSICA
    ],
    [#text(weight: "bold")[ASIGNATURA:]],
    table.cell(colspan: 5)[#course-name],
    [#text(weight: "bold")[TÍTULO DE LA PRÁCTICA:]],
    table.cell(colspan: 5)[#lab-title],
    [#text(weight: "bold")[NÚMERO DE LA PRÁCTICA:]],
    [#lab-number],
    [#text(weight: "bold")[AÑO LECTIVO:]],
    [#year],
    [#text(weight: "bold")[NRO. SEMESTRE:]],
    [#sem-code],
    [#text(weight: "bold")[FECHA DE PRESENTACIÓN:]],
    [#presentation-date],
    [#text(weight: "bold")[HORA DE PRESENTACIÓN:]],
    table.cell(colspan: 3)[#presentation-hour],
    table.cell(colspan: 4)[
      #text(weight: "bold")[INTEGRANTE(s):] \
      #for member in member-list {
        [
          - #member
        ]
      }
    ],
    [#text(weight: "bold")[NOTA (0 - 20):]],
    [Nota colocada por el docente],
    table.cell(colspan: 6)[
      #text(weight: "bold")[DOCENTE: ] \
      #instructor-name
    ],
  )
]

#let unsa-report(
  course_name: none,
  lab_title: none,
  lab_number: none,
  instructor_name: none,
  members: (),
  year: none,
  presentation_date: none,
  sem_code: none,
  presentation_hour: "11:59:00",
  logo-epis: default-logo-epis,
  logo-abet: default-logo-abet,
  custom_variables: (:),
  body,
) = {
  define("course_name", course_name)
  define("lab_title", lab_title)
  define("lab_number", lab_number)
  define("instructor_name", instructor_name)
  define("members", members)

  let gen-time = datetime.today()
  let resolved-year = if year != none { year } else { gen-time.year() }
  let resolved-presentation-date = if presentation_date != none {
    presentation_date
  } else {
    gen-time.display("[day]/[month]/[year]")
  }
  let resolved-sem-code = if sem_code != none {
    sem_code
  } else {
    if gen-time.month() < 8 { "A" } else { "B" }
  }

  define("year", resolved-year)
  define("presentation_date", resolved-presentation-date)
  define("sem_code", resolved-sem-code)
  define("presentation_hour", presentation_hour)

  for (name, value) in custom_variables {
    define(name, value)
  }

  set text(font: font-family, lang: font-lang)
  show heading.where(level: 1): set text(size: heading-1-size)
  show heading.where(level: 2): set text(size: heading-2-size)
  set list(indent: list-indent, marker: list-marker)
  set enum(numbering: enum-numbering)
  set image(width: image-default-width)
  show image: set align(center)

  set page(
    paper: page-paper,
    margin: page-margin,
    header: page-header(logo-epis: logo-epis, logo-abet: logo-abet),
    header-ascent: page-header-ascent,
  )

  align(center)[#text(size: header-title-text-size, weight: "bold")[INFORME DE LABORATORIO]]

  basic-info-table(
    course_name,
    lab_title,
    lab_number,
    resolved-year,
    resolved-sem-code,
    resolved-presentation-date,
    presentation_hour,
    members,
    instructor_name,
  )

  body
}
