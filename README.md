# Agente de riesgos de GESTITEL

Aplicación dedicada exclusivamente al agente de riesgos. El contexto operativo y la matriz
se recuperan de GESTITEL; no admite contexto manual, SQL ni metodologías enviadas por el cliente.
El usuario escribe únicamente el objetivo de revisión.

## Inicio

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# Configura .env siguiendo .env.example.
./iniciar.sh
```

Abre http://127.0.0.1:5000. Puedes cambiar el puerto con `PORT=5051 ./iniciar.sh`.
Requiere `GROQ_API_KEY`, `GESTITEL_USERNAME` y `GESTITEL_PASSWORD`.
`GEMINI_API_KEY` habilita respaldo opcional ante fallos temporales del proveedor principal.

## Funcionamiento

El agente consulta activos, procesos, evaluaciones de riesgos, matriz y controles mediante recursos
permitidos de https://unsa.27k.pe. Propone escenarios, estimaciones y tratamientos con referencias,
supuestos e información faltante. Si no hay activos suficientes, declara evidencia insuficiente.
La publicación en GESTITEL requiere vista previa y confirmación explícita; el modelo no escribe ni acepta riesgos por sí solo. La integración visual dentro de la plataforma externa
requiere su código o un adaptador acordado con sus administradores.

La interfaz contiene evaluación e historial del mismo agente. Las funciones anteriores de auditoría
SQL, chat y consulta EC1 no se exponen por web ni API. Los registros históricos de otras funciones
se conservan en SQLite, pero no aparecen en el historial de riesgos.

La fórmula P×I coincide con la documentación técnica del profesor (Anexo 04, páginas PDF 6 y 10);
las escalas y bandas se obtienen de su matriz activa. El diseño toma como referencia los alcances
de ISO 27001 y 27005; no contiene sus textos completos ni certifica cumplimiento.

## API

- `GET /api/status`: configuración de IA y GESTITEL.
- `POST /api/agent/runs`: inicia exclusivamente una tarea de riesgos.
- `GET /api/agent/runs/<id>`: actividad, resultado o error.
- `GET /api/risks/contract`: contrato v1.2, fuente fija GESTITEL.
- `GET /api/history` y `/api/history/<id>`: historial de riesgos.

```json
{"tarea":"riesgos","objetivo":"Consulta activos y matriz activa; propone riesgos respaldados por registros."}
```

No se admiten `contexto`, `metodologia`, `sql` ni otras tareas. La API valida este límite y el agente
no tiene otros modos. Los documentos locales aportan respaldo normativo, no contexto operativo.

## Validación y alcance

```bash
.venv/bin/python -m unittest discover -s tests -v
node --check web/static/app.js
node --check web/static/risk.js
```

Servidor local individual sin autenticación multiusuario. En modo IA se envían al proveedor el objetivo
y registros seleccionados. Las credenciales permanecen en el servidor. El historial se guarda en
`data/history.sqlite3`; la carpeta y `.env` están excluidas de Git.

[Guía, relaciones entre módulos y contrato](docs/agente_riesgos.md).
[Verificación y limitaciones](docs/verificacion_riesgos.md).
Las guías EC1 y de exposición anteriores son antecedentes históricos, no instrucciones de la aplicación actual.

## Entrega EC2 — Grupo 1

La [hoja de una página](docs/entrega_ec2/main.pdf) fue preparada con UNSAReport.
El [paquete de entrega](docs/entrega_ec2/README.md) incluye arquitectura, alcance normativo y guion.
El caso EC2-DEMO y el activo ACT-HW-001 fueron registrados en GESTITEL con autorización, sin datos personales.

La evaluación persistida permite descargar PDF y registrar revisiones locales con huella del resultado.
Estas revisiones no aceptan riesgo residual ni escriben en GESTITEL.

Verifica el entorno con `.venv/bin/python scripts/preparar_exposicion.py`.
Cuando estén disponibles, incorpora las ISO autorizadas con `scripts/incorporar_iso.py`;
las instrucciones y el contraste pendiente están en el paquete de entrega.

## Registro en el panel de riesgos

Desde cada propuesta puedes preparar una vista previa para crear o actualizar un riesgo.
El envío exige aprobación y conserva trazabilidad; no acepta riesgos residuales.
Consulta [el flujo de publicación](docs/publicar_riesgos.md) para los campos, límites y recuperación.
