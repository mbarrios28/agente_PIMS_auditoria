# @unsareport/epis-lab-theming

Tokens de diseño y variables de estilo para informes de laboratorio de EPIS (UNSA). Define colores, tipografía, márgenes y dimensiones de tablas y secciones.

## Uso

```typst
#import "/components/@unsareport/epis-lab-theming/lib.typ": *

// Sobrescribir variables de estilo si es necesario
#let primary-color = rgb("#1a5276")
```

## Variables disponibles

- **Colores**: `primary-color`, `header-border-color`, `table-border-color`, `table-stroke`, `table-inset`, `code-bg-color`.
- **Tipografía y página**: `font-family`, `font-lang`, `page-paper`, `page-margin`, `page-header-ascent`.
- **Encabezado institucional**: `header-institution-text-size`, `header-meta-text-size`, `header-title-text-size`, `header-spacing-bottom`.
- **Tabla de información**: `info-table-text-size`, `info-header-text-size`, `info-header-fill`, `info-header-text-color`.
- **Encabezados y listas**: `heading-1-size`, `heading-2-size`, `list-indent`, `list-marker`, `enum-numbering`, `image-default-width`.
- **Secciones de laboratorio**: `section-align-mode`, `section-stroke`, `section-inset`, `section-header-fill`, `section-header-text-size`, `section-header-text-color`, `section-body-text-size`.
