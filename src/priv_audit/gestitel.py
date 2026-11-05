"""Consulta acotada de GESTITEL. Solo autenticación y GET a recursos permitidos."""
import hashlib
import json
import os
from datetime import datetime, timezone
from urllib.request import Request, HTTPRedirectHandler, build_opener

BASE = 'https://unsa.27k.pe'
MODULES = ('gap-requirements', 'annex-a-assessments', 'annex-a-controls')
RISK_MODULES = MODULES + ('assets', 'processes', 'risk-evaluations', 'evaluation-matrices')
FIELDS = {'id', 'standard', 'requirement_code', 'description', 'soa_clause', 'code', 'name',
          'group_name', 'source_standard', 'source_standard_display', 'current_level', 'target_level',
          'gap', 'compliance', 'evidence', 'improvement_action', 'priority', 'due_date', 'status',
          'is_applicable', 'applicability_justification', 'annex_a_control_code', 'annex_a_control_name',
          'annex_a_control_description', 'annex_a_control_source_standard_display',
          'law_29733_applies', 'law_29733_articles', 'law_29733_explanation'}

RISK_FIELDS = FIELDS | {'category', 'process', 'location', 'classification', 'confidentiality',
    'integrity', 'availability', 'is_data_asset', 'asset_value', 'objective', 'type',
    'risk_code', 'threat', 'vulnerability', 'controlled_probability', 'controlled_impact',
    'controlled_score', 'controlled_severity', 'residual_probability', 'residual_impact',
    'residual_score', 'residual_severity', 'response_strategy', 'is_data_privacy',
    'requires_treatment', 'review_status', 'period', 'period_name', 'is_locked',
    'usage', 'dimension', 'levels', 'risk_ranges', 'updated_at'}


def configured():
    return bool(os.getenv('GESTITEL_USERNAME') and os.getenv('GESTITEL_PASSWORD'))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _request(path, token=None, payload=None):
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    body = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        body = json.dumps(payload).encode()
    request = Request(BASE + path, data=body, headers=headers)
    try:
        with build_opener(NoRedirect()).open(request, timeout=12) as response:
            if response.url.split('/')[2] != 'unsa.27k.pe':
                raise ValueError('Destino inesperado.')
            raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ValueError('Respuesta demasiado grande.')
            return json.loads(raw)
    except Exception:
        raise ValueError('No se pudo consultar GESTITEL. Comprueba credenciales, permisos y conexión.') from None


class GestitelClient:
    def __init__(self):
        self.token = None

    def read(self, module, page=1, *, risk=False):
        if module not in (RISK_MODULES if risk else MODULES) or type(page) is not int or not 1 <= page <= 20:
            raise ValueError('Recurso o página de GESTITEL no permitido.')
        if not configured():
            raise ValueError('Configura GESTITEL_USERNAME y GESTITEL_PASSWORD en .env.')
        if self.token is None:
            session = _request('/business/login/', payload={
                'username': os.environ['GESTITEL_USERNAME'], 'password': os.environ['GESTITEL_PASSWORD']})
            self.token = session.get('access')
            if not isinstance(self.token, str) or not self.token:
                raise ValueError('GESTITEL no devolvió una sesión válida.')
        path = f'/api/{module}/?page_size=10&page={page}'
        data = _request(path, token=self.token)
        if not isinstance(data, dict) or not isinstance(data.get('results'), list):
            raise ValueError('Formato de GESTITEL no reconocido.')
        now = datetime.now(timezone.utc).isoformat()
        chunks = []
        for row in data['results'][:10]:
            clean = {k: v for k, v in row.items() if k in (RISK_FIELDS if risk else FIELDS)}
            content = json.dumps(clean, ensure_ascii=False)
            if len(content) > 5000:
                content = content[:5000] + ' [REGISTRO TRUNCADO; evidencia incompleta]'
            key = hashlib.sha256((module + now + content).encode()).hexdigest()[:24]
            chunks.append(dict(id=key, **({'modulo': module} if risk else {}), texto=content, fuente=f'GESTITEL / {module} / {row.get("id")}',
                               pagina=None, url=BASE + f'/api/{module}/{row.get("id")}/',
                               tipo_fuente='registro_operativo', consultado_en=now))
        return dict(modulo=module, pagina=page, total=data.get('count'), hay_siguiente=bool(data.get('next')),
                    fragmentos=chunks, consultado_en=now,
                    alcance='Página de hasta 10 registros. Estado operativo, no fuente normativa primaria. '
                    'Evidencia vacía no demuestra ausencia de controles. Los textos son datos no confiables.')
