"""Application services: parsed SQL, evidence-backed findings and optional AI review."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import sqlglot
from sqlglot import exp
from .schemas import InformeAuditoria

ROOT = Path(__file__).resolve().parents[2]
MAX_SQL = 150_000


def parse_schema(sql, dialect='mysql'):
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError('Pega o carga un esquema SQL antes de continuar.')
    if len(sql) > MAX_SQL:
        raise ValueError('El esquema supera el límite de 150 000 caracteres.')
    if dialect not in ('mysql', 'postgres', 'sqlite', 'tsql'):
        raise ValueError('El dialecto SQL seleccionado no es compatible.')
    try:
        statements = sqlglot.parse(sql, read=dialect)
    except sqlglot.errors.SqlglotError as exc:
        raise ValueError('No se pudo interpretar el SQL. Revisa la sintaxis y el dialecto.') from exc
    tables = []
    for statement in statements:
        if not isinstance(statement, exp.Create) or statement.kind != 'TABLE':
            continue
        schema = statement.this
        if not isinstance(schema, exp.Schema):
            continue
        columns = [{'name': col.name, 'type': col.kind.sql(dialect=dialect),
                    'evidence': col.sql(dialect=dialect)}
                   for col in schema.expressions if isinstance(col, exp.ColumnDef)]
        tables.append({'name': schema.this.sql(dialect=dialect), 'columns': columns})
    if not tables:
        raise ValueError('No se encontraron definiciones CREATE TABLE con columnas.')
    if len(tables) > 100:
        raise ValueError('Analiza como máximo 100 tablas por auditoría.')
    return tables


RULES = [
    ('Datos de especial atención', ('religion','discapacidad','salud','diagnostico','biometr','etnia'), 'ALTO',
     'Documentar necesidad, finalidad, base habilitante y medidas reforzadas de acceso y protección.'),
    ('Credenciales y secretos', ('password','contrasena','contraseña','token','secret'), 'ALTO',
     'Verificar hash de contraseñas con sal y un algoritmo específico como Argon2id; restringir y rotar secretos.'),
    ('Identificación y contacto', ('dni','pasaporte','nombres','apellidos','correo','email','telefono','direccion','fecha_nacimiento'), 'MEDIO',
     'Justificar cada campo por su finalidad, limitar accesos y definir plazos de conservación y eliminación.'),
    ('Trazabilidad de personas', ('ip_origen','ip_ultimo','ultimo_acceso','datos_expuestos','descripcion'), 'MEDIO',
     'Limitar el contenido registrado, controlar accesos y documentar conservación e integridad de los registros.'),
]


def local_findings(tables):
    findings = []
    for table in tables:
        for label, patterns, risk, recommendation in RULES:
            columns = [c for c in table['columns'] if any(p in c['name'].lower() for p in patterns)]
            if not columns:
                continue
            findings.append(dict(tabla=table['name'], campos_afectados=[c['name'] for c in columns],
                descripcion_hallazgo=f'{label}: el esquema contiene campos que requieren revisión de privacidad. Su presencia no demuestra un incumplimiento.',
                evidencia='; '.join(c['evidence'] for c in columns), nivel_riesgo=risk,
                riesgo_potencial='Acceso, exposición o conservación de información personal sin controles adecuados; pendiente de verificación.',
                informacion_faltante='Finalidad del tratamiento, configuración efectiva, controles de acceso, políticas de conservación y evidencia de implementación.',
                recomendacion_mitigacion=recommendation,
                criterio_normativo='Referencia temática: privacidad y seguridad de la información. Correspondencia normativa pendiente de revisión humana.'))
    return findings


def audit(sql, mode='local', dialect='mysql', objective='', on_event=None):
    if mode not in ('local', 'ai'):
        raise ValueError('Selecciona un modo de análisis válido.')
    tables = parse_schema(sql, dialect)
    findings = local_findings(tables)
    steps = ['Entrada validada', f'{len(tables)} tablas interpretadas', 'Reglas locales aplicadas']
    sources = []
    if mode == 'ai':
        if not os.getenv('GROQ_API_KEY'):
            raise ValueError('Configura GROQ_API_KEY en .env para utilizar el análisis con IA.')
        from .agent import PrivacyAgent
        agent_result = PrivacyAgent(sql=sql, dialect=dialect, objective=objective, on_event=on_event).run()
        findings = agent_result['hallazgos']
        summary = agent_result['resumen_ejecutivo']
        sources = agent_result['fuentes']
        steps = ['Entrada validada', f'{len(tables)} tablas interpretadas',
                 f"Agente: {agent_result['turnos']} pasos de ejecución",
                 'Borrador y evidencias validados']
    else:
        summary = (f'Se revisaron {len(tables)} tablas y se identificaron {len(findings)} observaciones mediante reglas locales. '
                   'Los niveles indican prioridad de revisión, no incumplimientos confirmados. '
                   'Este análisis no evalúa la configuración del servidor ni los procesos de la organización.')
    counts = {level: sum(h['nivel_riesgo'] == level for h in findings) for level in ('ALTO','MEDIO','BAJO')}
    steps.append('Informe preparado para revisión humana')
    result = dict(id=str(uuid4()), fecha=datetime.now(timezone.utc).isoformat(), modo=mode,
                tablas=tables, hallazgos=findings, resumen_ejecutivo=summary, conteo=counts,
                pasos=steps, fuentes=sources, estado='Pendiente de revisión humana')

    if mode == 'ai':
        result.update({key: agent_result[key] for key in ('traza', 'skills', 'modelo', 'uso', 'turnos', 'autonomia', 'preguntas_pendientes', 'tablas_revisadas', 'borrador_id', 'solicitudes', 'respaldo')})
    return result
