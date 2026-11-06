"""Publicación aprobada en GESTITEL. El LLM no puede confirmar ni invocar escrituras."""
import hashlib
import json
import secrets
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import Request, build_opener
from . import history
from .gestitel import BASE, NoRedirect, _request
from .risk import from_gestitel


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


class PublicationError(ValueError):
    pass


class UncertainWrite(PublicationError):
    pass


class Gateway:
    def __init__(self):
        from .gestitel import GestitelClient
        client = GestitelClient()
        client.read('assets', risk=True)
        self.token = client.token

    def get(self, path):
        return _request(path, self.token)

    def matching(self, marker):
        matches = []
        for page in range(1, 21):
            data = self.get(f'/api/risk-evaluations/?page_size=100&page={page}')
            matches.extend(r for r in data['results'] if marker in r.get('observations', ''))
            if not data.get('next'):
                return matches
        raise PublicationError('No se pudo completar la comprobación de duplicados. No se envió el riesgo.')

    def write(self, remote_id, payload):
        # Únicas rutas de escritura, generadas en servidor y sin reintentos automáticos.
        path = f'/api/risk-evaluations/{remote_id}/' if remote_id else '/api/risk-evaluations/'
        request = Request(BASE + path, data=json.dumps(payload).encode(),
                          headers={'Authorization': 'Bearer '+self.token, 'Content-Type': 'application/json',
                                   'Accept': 'application/json'}, method='PATCH' if remote_id else 'POST')
        try:
            with build_opener(NoRedirect()).open(request, timeout=20) as response:
                raw = response.read(1_000_001)
                if len(raw) > 1_000_000:
                    raise UncertainWrite('Respuesta incompleta. Comprueba el resultado antes de otro envío.')
                result = json.loads(raw)
                if type(result.get('id')) is not int:
                    raise UncertainWrite('GESTITEL no confirmó el identificador; se requiere conciliación.')
                return result
        except HTTPError as exc:
            if 400 <= exc.code < 500:
                raise PublicationError(f'GESTITEL rechazó el envío (HTTP {exc.code}). Revisa permisos, campos y período.') from None
            raise UncertainWrite('GESTITEL no confirmó el resultado. No se reintentará automáticamente.') from None
        except PublicationError:
            raise
        except Exception:
            raise UncertainWrite('Se perdió la confirmación del envío. Concilia antes de volver a publicar.') from None


def tables(db):
    db.execute('''CREATE TABLE IF NOT EXISTS gestitel_previews (
        id TEXT PRIMARY KEY, entry_id TEXT NOT NULL, risk_index INTEGER NOT NULL,
        mode TEXT NOT NULL, remote_id INTEGER, payload TEXT NOT NULL, payload_hash TEXT NOT NULL,
        snapshot TEXT NOT NULL, marker TEXT NOT NULL, state TEXT NOT NULL, created_at TEXT NOT NULL,
        reviewer TEXT, result TEXT, error TEXT)''')


def load_preview(key):
    with history.connect() as db:
        tables(db)
        row = db.execute('SELECT * FROM gestitel_previews WHERE id=?', (key,)).fetchone()
    if not row:
        raise PublicationError('Vista previa no encontrada.')
    out = dict(row)
    for key in ('payload', 'snapshot', 'result'):
        out[key] = json.loads(out[key]) if out[key] else None
    return out


def publications(entry_id):
    with history.connect() as db:
        tables(db)
        rows = db.execute('SELECT id,risk_index,mode,remote_id,state,created_at,reviewer,result,error FROM gestitel_previews WHERE entry_id=? ORDER BY created_at', (entry_id,)).fetchall()
    return [dict(dict(r), result=json.loads(r['result']) if r['result'] else None) for r in rows]


def _entry(entry_id, index):
    entry = history.get(entry_id)
    if not entry or entry['tipo'] != 'riesgos' or entry['estado'] != 'completado':
        raise PublicationError('Evaluación de riesgos no encontrada o no finalizada.')
    result = entry['resultado']
    if result.get('fuente') != 'gestitel' or result.get('estado_respuesta') != 'propuesta':
        raise PublicationError('Solo se publican propuestas obtenidas de GESTITEL.')
    if type(index) is not int or not 0 <= index < len(result['riesgos']):
        raise PublicationError('Escenario de riesgo inválido.')
    return entry, result['riesgos'][index]


def _context(gateway, entry, risk, remote_id):
    evaluation = risk.get('evaluacion')
    if not evaluation or evaluation.get('estado') != 'estimacion_propuesta':
        raise PublicationError('El escenario necesita un cálculo validado antes de publicarse.')
    chunks = {c['id']: c for c in entry['resultado']['fuentes']}
    assets = [json.loads(chunks[r['fragmento_id']]['texto']) for r in risk['referencias']
              if r['fragmento_id'] in chunks and chunks[r['fragmento_id']].get('modulo') == 'assets']
    candidates = [r for r in assets if risk['activo'] in (r.get('code'), r.get('name'), str(r.get('id')))]
    if len(candidates) != 1:
        raise PublicationError('No se pudo resolver un único activo de la propuesta.')
    old_asset = candidates[0]
    asset = gateway.get(f"/api/assets/{int(old_asset['id'])}/")
    if asset.get('is_deleted') or asset.get('code') != old_asset.get('code') or asset.get('updated_at') != old_asset.get('updated_at'):
        raise PublicationError('El activo cambió desde la evaluación. Ejecuta una nueva evaluación.')
    if asset.get('risk_eligible') is False:
        raise PublicationError('El activo está fuera del alcance de riesgos configurado en GESTITEL.')
    matrices = gateway.get('/api/evaluation-matrices/?page_size=100')
    active = [r for r in matrices['results'] if r.get('status') == 'A' and r.get('usage') in ('A', 'R')]
    if len(active) != 1 or from_gestitel(active[0]).model_dump() != evaluation['metodologia']:
        raise PublicationError('La matriz cambió o es ambigua. Evalúa nuevamente antes de publicar.')
    catalogs = gateway.get('/api/risk-evaluations/catalogs/')
    period = catalogs.get('current_period')
    if not period or period.get('status') != 'O' or not period.get('is_active'):
        raise PublicationError('GESTITEL no tiene un período activo abierto.')
    codes = {c['code'] for c in catalogs.get('applicable_annex_a_controls', [])}
    controls = []
    for key in risk.get('controles_ids', []):
        chunk = chunks.get(key)
        if not chunk or chunk.get('modulo') != 'annex-a-controls':
            raise PublicationError('Para publicar tratamientos se requiere el registro del catálogo de controles.')
        old = json.loads(chunk['texto'])
        control = gateway.get(f"/api/annex-a-controls/{int(old['id'])}/")
        if control.get('code') != old.get('code') or control.get('description') != old.get('description') or control['code'] not in codes:
            raise PublicationError('Un control cambió o ya no es aplicable. Revisa la propuesta.')
        controls.append(control['code'])
    target = None
    if remote_id:
        target = gateway.get(f'/api/risk-evaluations/{remote_id}/')
        if target.get('is_locked') or target.get('status') == 'C' or target.get('residual_probability') is not None or target.get('residual_impact') is not None or target.get('is_effective') == 'Y':
            raise PublicationError('No se actualizan riesgos cerrados, bloqueados o con evaluación residual.')
        if target.get('period') != period['id']:
            raise PublicationError('El riesgo pertenece a otro período.')
        if asset['code'] not in {str(r.get('asset_code') or r.get('asset')) for r in target.get('assets', [])}:
            raise PublicationError('El riesgo seleccionado no está vinculado al activo de la propuesta.')
    snapshot = dict(asset=digest(asset), matrix=digest(active[0]), period=digest(period),
                    controls=controls, target=digest(target) if target else None)
    return asset, period, controls, target, snapshot


def preview(entry_id, index, remote_id=None, gateway=None):
    if remote_id is not None and (type(remote_id) is not int or remote_id < 1):
        raise PublicationError('Identificador de riesgo inválido.')
    entry, risk = _entry(entry_id, index)
    if risk['estrategia'] == 'aceptar_propuesto':
        raise PublicationError('La aceptación de riesgos debe gestionarse por el responsable en GESTITEL.')
    gateway = gateway or Gateway()
    asset, period, controls, target, snapshot = _context(gateway, entry, risk, remote_id)
    marker = 'PIMS-RISK:' + digest([entry_id, index])[:24]
    notes = '\n'.join([marker, 'Propuesta del agente aprobada únicamente para registro; no prueba implementación.',
        'Supuestos: ' + '; '.join(risk['supuestos']),
        'Información faltante: ' + '; '.join(risk['informacion_faltante']),
        'Evidencia a solicitar: ' + '; '.join(risk['evidencia_a_solicitar']),
        'Acciones propuestas: ' + '; '.join(risk['acciones']), 'Plazo propuesto: ' + risk['plazo_propuesto'],
        'Impacto sobre personas: ' + risk.get('impacto_personas','No determinado en esta evaluación.'),
        'Rol del tratamiento: ' + risk.get('rol_tratamiento','no_determinado')])
    payload = dict(risk_owner=risk['responsable_propuesto'], threat=risk['amenaza'],
        vulnerability=risk['vulnerabilidad'], description=risk['consecuencia'],
        controlled_probability=risk['evaluacion']['probabilidad'], controlled_impact=risk['evaluacion']['impacto'],
        response_strategy={'mitigar':'M', 'evitar':'E', 'compartir':'T'}[risk['estrategia']],
        observations=(target.get('observations', '') + '\n' if target else '') + notes)
    if not target:
        payload.update(period=period['id'], status='O', assets=[{'asset':asset['code']}],
            treatments=[dict(annex_a_control=code, description='Plan propuesto: ' + risk['amenaza'],
                activities=[dict(description=action, responsible=risk['responsable_propuesto'],
                                 estimated_time=risk['plazo_propuesto'][:100]) for action in risk['acciones']]) for code in controls])
    key = secrets.token_urlsafe(24)
    with history.connect() as db:
        tables(db)
        db.execute('INSERT INTO gestitel_previews VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (key, entry_id, index, 'actualizar' if remote_id else 'crear', remote_id,
             json.dumps(payload, ensure_ascii=False), digest(payload), json.dumps(snapshot), marker, 'preview', now(), None, None, None))
    return public_preview(load_preview(key), target)


def public_preview(item, target=None):
    return dict(id=item['id'], accion=item['mode'], riesgo_remoto=item['remote_id'],
        datos=item['payload'], huella=item['payload_hash'], estado=item['state'],
        actual={k:target.get(k) for k in item['payload']} if target else None,
        aviso='Se guardará una propuesta en GESTITEL. No se acepta riesgo residual ni se marcan controles implementados. ' +
              ('La actualización conserva vínculos y planes existentes.' if item['mode']=='actualizar' else 'Se creará el riesgo abierto vinculado al activo. Los planes con control recuperado se registran como tratamientos; las demás acciones se conservan en observaciones.'))


def _finish(key, state, result=None, error=None):
    with history.connect() as db:
        tables(db)
        db.execute('UPDATE gestitel_previews SET state=?,result=?,error=? WHERE id=?',
                   (state, json.dumps(result, ensure_ascii=False) if result else None, error, key))


def _receipt(remote):
    return dict(id=remote['id'], codigo=remote.get('risk_code'), puntaje=remote.get('controlled_score'),
                estado=remote.get('status'), url=BASE+'/risks', verificado_en=now())


def verify_remote(item, remote):
    if item['marker'] not in remote.get('observations', ''):
        raise UncertainWrite('El registro no confirmó la referencia de publicación.')
    for field in ('description','threat','vulnerability','controlled_probability','controlled_impact','response_strategy'):
        if remote.get(field) != item['payload'][field]:
            raise UncertainWrite('El registro no coincide con los datos aprobados. Requiere conciliación.')
    if not item['remote_id']:
        codes={str(r.get('asset_code') or r.get('asset')) for r in remote.get('assets',[])}
        if not {r['asset'] for r in item['payload']['assets']} <= codes:
            raise UncertainWrite('No se confirmó el vínculo con el activo.')
    for planned in item['payload'].get('treatments', []):
        actual = next((p for p in remote.get('treatments', []) if p.get('description') == planned['description']), None)
        if not actual or not {a['description'] for a in planned['activities']} <= {a.get('description') for a in actual.get('activities', [])}:
            raise UncertainWrite('No se confirmaron los planes y actividades propuestos.')
    return _receipt(remote)


def confirm(key, reviewer, fingerprint, approved, gateway=None):
    if approved is not True or not isinstance(reviewer, str) or not 3 <= len(reviewer.strip()) <= 150:
        raise PublicationError('Confirma explícitamente el envío e identifica al revisor.')
    item = load_preview(key)
    if fingerprint != item['payload_hash'] or digest(item['payload']) != fingerprint:
        raise PublicationError('La vista previa no coincide con la aprobación.')
    if item['state'] == 'published':
        return item['result']
    if item['state'] != 'preview':
        raise PublicationError('Esta vista previa ya fue usada o requiere conciliación. No se repetirá el envío.')
    if (datetime.now(timezone.utc)-datetime.fromisoformat(item['created_at'])).total_seconds() > 600:
        raise PublicationError('La vista previa caducó. Genera una nueva.')
    gateway = gateway or Gateway()
    entry, risk = _entry(item['entry_id'], item['risk_index'])
    _, _, _, _, snapshot = _context(gateway, entry, risk, item['remote_id'])
    if snapshot != item['snapshot']:
        raise PublicationError('Los datos remotos cambiaron desde la vista previa. Genera otra.')
    # Reserva atómica y duradera: ninguna segunda solicitud envía el mismo escenario.
    with history.connect() as db:
        tables(db)
        db.execute('BEGIN IMMEDIATE')
        other = db.execute("SELECT state,result FROM gestitel_previews WHERE entry_id=? AND risk_index=? AND mode=? AND remote_id IS ? AND state IN ('sending','uncertain','published')", (item['entry_id'],item['risk_index'],item['mode'],item['remote_id'])).fetchone()
        if other:
            if other['state']=='published':
                db.execute("UPDATE gestitel_previews SET state='published',reviewer=?,result=? WHERE id=?", (reviewer.strip(),other['result'],key))
                return json.loads(other['result'])
            raise PublicationError('Hay un envío pendiente de confirmar. Usa la conciliación.')
        if db.execute("UPDATE gestitel_previews SET state='sending',reviewer=? WHERE id=? AND state='preview'", (reviewer.strip(),key)).rowcount != 1:
            raise PublicationError('La vista previa ya fue utilizada.')
    sent = False
    try:
        if not item['remote_id']:
            duplicates = gateway.matching(item['marker'])
            if duplicates:
                if len(duplicates) != 1:
                    raise UncertainWrite('Hay varios riesgos con el marcador. Requiere revisión.')
                result = verify_remote(item, duplicates[0]);_finish(key,'published',result);return result
        sent = True
        remote = gateway.write(item['remote_id'], item['payload'])
        # El GET confirma el registro visible después del envío.
        saved = gateway.get(f"/api/risk-evaluations/{remote['id']}/")
        result = verify_remote(item, saved)
        _finish(key,'published',result)
        return result
    except UncertainWrite as exc:
        _finish(key,'uncertain',error=str(exc));raise
    except PublicationError as exc:
        _finish(key,'failed',error=str(exc));raise
    except Exception:
        error='No se pudo verificar el resultado. Concilia antes de otro envío.'
        _finish(key,'uncertain' if sent else 'failed',error=error)
        raise PublicationError(error) from None


def reconcile(key, gateway=None):
    item = load_preview(key)
    if item['state']=='published':return item['result']
    if item['state'] not in ('sending','uncertain'):
        raise PublicationError('No hay un envío incierto que conciliar.')
    gateway = gateway or Gateway()
    matches = gateway.matching(item['marker'])
    if len(matches)!=1:
        raise PublicationError('Aún no se pudo confirmar un único registro. No vuelvas a enviarlo.')
    result=verify_remote(item,matches[0]);_finish(key,'published',result)
    return result
