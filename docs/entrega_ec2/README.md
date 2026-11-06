# Entrega EC2 — Grupo 1

- `main.pdf`: hoja única para Moodle, generada con UNSAReport.
- `main.typ`: fuente editable de la hoja.
- `assets/arquitectura.svg` y `arquitectura.mmd`: diagrama del agente único.
- `guion_exposicion.md`: recorrido de 12 minutos y tres de preguntas.
- `verificacion_ec2.md`: evidencia del ensayo real y comprobaciones.
- `informe_caso_ec2.pdf`: resultado de la ejecución real del caso.
- `evidencia_ejecucion.json`: resultado, fuentes y traza real, sin secretos.
- `alcance_normativo.md`: correspondencias de diseño y sus límites.

Compilar desde la raíz del repositorio:

```bash
cd docs
unsarep docs build entrega_ec2 --no-input
```

La hoja debe tener exactamente una página. La plantilla y recursos se instalaron con
`unsarep docs init @unsareport/epis-lab --report entrega_ec2 --none --no-input`.
El membrete usa el recurso EPIS de UNSAReport y su paleta; no incluye una portada separada.
El envío a Moodle y la presentación personal corresponden al grupo. No se publican credenciales.

## Incorporación de ISO pendiente

Cuando el grupo consiga copias autorizadas con texto:

```bash
.venv/bin/python scripts/incorporar_iso.py --norma 27001 --archivo /ruta/ISO27001.pdf
.venv/bin/python scripts/incorporar_iso.py --norma 27002 --archivo /ruta/ISO27002.pdf
.venv/bin/python scripts/incorporar_iso.py --norma 27005 --archivo /ruta/ISO27005.pdf
```

ISO/IEC 27701:2025 se incorpora con `--norma 27701` si se usa para ampliar el alcance de privacidad.
El script comprueba texto, número y año; registra huella y páginas, no acredita autenticidad.
Después hay que contrastar las correspondencias preparadas con el texto aportado. Esa revisión forma
parte de la incorporación de las normas y no se sustituye con una ficha pública ni con el catálogo.

Ensayo real reproducible: `.venv/bin/python scripts/ensayo_ec2.py` (consume cuota).
La revisión crítica de las estimaciones se encuentra en `verificacion_ec2.md`.
