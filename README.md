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
No escribe ni acepta riesgos en GESTITEL. La integración visual dentro de la plataforma externa
requiere su código o un adaptador acordado con sus administradores.

La interfaz contiene evaluación e historial del mismo agente. Las funciones anteriores de auditoría
SQL, chat y consulta EC1 no se exponen por web ni API. Los registros históricos de otras funciones
se conservan en SQLite, pero no aparecen en el historial de riesgos.

La fórmula P×I es una propuesta explícita pendiente de contrastar con el backend de GESTITEL;
las escalas y bandas se obtienen de su matriz activa. El diseño toma como referencia los alcances
de ISO 27001 y 27005; no contiene sus textos completos ni certifica cumplimiento.

## API

- `GET /api/status`: configuración de IA y GESTITEL.
- `POST /api/agent/runs`: inicia exclusivamente una tarea de riesgos.
- `GET /api/agent/runs/<id>`: actividad, resultado o error.
- `GET /api/risks/contract`: contrato v1.1, fuente fija GESTITEL.
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
