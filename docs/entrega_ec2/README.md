# Exposición técnica y entrega EC2 — Grupo 1

## Material para exponer

- `assets/arquitectura_oscura.png` / `.pdf` / `.svg`: variante con fondo oscuro,
  iconos de trazo y bloques por componente, siguiendo la ficha visual de referencia.
  Regenerar con `python scripts/generar_arquitectura_oscura.py` (reportlab, svglib, pymupdf).
- `guia_exposicion.pdf`: guía de ensayo; 12 minutos de demostración y 3 de preguntas.
- `guion_exposicion.md`: fuente editable con tiempos, archivos, acciones y frases de apoyo.
- `assets/arquitectura.pdf`: diagrama vectorial para abrir y ampliar.
- `assets/arquitectura.png`: imagen de alta resolución para proyectar o insertar.
- `assets/arquitectura.svg`: versión vectorial generada con Graphviz.
- `assets/arquitectura.dot`: fuente Graphviz editable; es la fuente vigente del diagrama.
- `alcance_normativo.md`: referencias exclusivas de ISO/IEC 27701:2025.
- `main.pdf` / `main.typ`: ficha de una página para entrega académica.

El recorrido muestra cómo se carga la skill, cómo el modelo solicita herramientas,
cómo se recuperan datos y fragmentos ISO, y cómo Python calcula y valida el resultado.
Se listan las cuatro skills del repositorio y se identifica la única activa: gestion_riesgos.
La publicación ocupa como máximo un minuto y conserva la aprobación humana.

## Regenerar los gráficos y la guía

Con Node.js y Python disponibles, instalar las dependencias de autoría fuera del proyecto si se desea:

```powershell
npm install --prefix "$env:TEMP/pims-graphviz" --no-audit --no-fund @viz-js/viz@3.17.0
node scripts/render_arquitectura.mjs "$env:TEMP/pims-graphviz/node_modules/@viz-js/viz/dist/viz.js"
python -m pip install reportlab svglib pymupdf
python scripts/generar_material_exposicion.py
```

También se puede usar el CLI nativo Graphviz: `dot -Tsvg docs/entrega_ec2/assets/arquitectura.dot -o docs/entrega_ec2/assets/arquitectura.svg`.
La exportación PDF/PNG parte del SVG; no usa capturas de Markdown ni imágenes generadas por IA.

Para la ficha UNSAReport, desde `docs`: `unsarep docs build entrega_ec2 --no-input`.

## Evidencia histórica y ensayo

`evidencia_ejecucion.json`, `informe_caso_ec2.pdf` y `verificacion_ec2.md` conservan
un ensayo anterior. No se alteran sus resultados. Esa ejecución es previa al aislamiento
normativo actual: permite explicar la traza y el cálculo, no demostrar el RAG actual.
Identificar su fecha si se usa como respaldo durante la exposición.

Ensayo nuevo: `python scripts/ensayo_ec2.py` (consulta GESTITEL y consume cuota de IA).
No se ejecuta automáticamente al regenerar el material. Preparar credenciales antes de
proyectar; no mostrarlas. Para validaciones locales sin IA:

```powershell
python scripts/verificar_iso_27701.py
python scripts/mostrar_skills.py
python -m unittest discover -s tests -p test_risk_normative_scope.py -v
```

La copia completa ISO/IEC 27701:2025 ya está en el repositorio; no hace falta incorporar
otras normas para ampliar esta exposición. Las escrituras en GESTITEL requieren revisión,
vista previa y confirmación explícita. El envío a Moodle corresponde al grupo.
