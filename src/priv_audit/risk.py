"""Contratos y cálculo reproducible de propuestas; ninguna escritura en GESTITEL."""
import hashlib
import json
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Band(Strict):
    nivel: Literal['BAJO', 'MEDIO', 'ALTO', 'CRITICO']
    minimo: int = Field(ge=1, le=10000)
    maximo: int = Field(ge=1, le=10000)


class Methodology(Strict):
    nombre: str = Field(min_length=3, max_length=200)
    version: str = Field(min_length=1, max_length=100)
    escala: int = Field(ge=2, le=10)
    formula: Literal['P*I'] = 'P*I'
    origen: Literal['propuesta_local', 'matriz_gestitel'] = 'propuesta_local'
    matriz_id: str | None = None
    bandas: list[Band] = Field(min_length=1, max_length=10)

    @model_validator(mode='after')
    def coverage(self):
        covered = set()
        for band in self.bandas:
            values = set(range(band.minimo, band.maximo + 1))
            if band.minimo > band.maximo or covered & values:
                raise ValueError('Rangos invertidos o superpuestos.')
            covered |= values
        if covered != set(range(1, self.escala ** 2 + 1)):
            raise ValueError('Los rangos deben cubrir exactamente 1 hasta escala².')
        return self


def demo_methodology():
    return Methodology(nombre='Propuesta académica 4x4', version='1', escala=4,
        bandas=[Band(nivel=n, minimo=a, maximo=b) for n, a, b in
                [('BAJO', 1, 3), ('MEDIO', 4, 7), ('ALTO', 8, 11), ('CRITICO', 12, 16)]])


def from_gestitel(row):
    """Reutiliza matriz; P*I sigue siendo una propuesta, no fórmula verificada del backend."""
    scale = row['dimension']
    for axis in ('P', 'I'):
        values = sorted(Decimal(str(x['value'])) for x in row['levels'] if x['axis'] == axis)
        if values != list(range(1, scale + 1)):
            raise ValueError('La matriz usa escalas no soportadas; revisar manualmente.')
    names = {'L': 'BAJO', 'M': 'MEDIO', 'H': 'ALTO', 'C': 'CRITICO'}
    return Methodology(nombre=row['name'], version=str(row.get('updated_at') or row['id']),
        escala=scale, origen='matriz_gestitel', matriz_id=str(row['id']),
        bandas=[Band(nivel=names[x['level']], minimo=x['min_value'], maximo=x['max_value'])
                for x in row['risk_ranges']])


class RiskRead(Strict):
    motivo: str = Field(min_length=3, max_length=350)
    modulo: Literal['assets', 'processes', 'risk-evaluations', 'evaluation-matrices',
                    'annex-a-controls', 'annex-a-assessments', 'gap-requirements']
    pagina: int = Field(default=1, ge=1, le=20)


class Calculation(Strict):
    motivo: str = Field(min_length=3, max_length=350)
    probabilidad: int = Field(strict=True, ge=1, le=10)
    impacto: int = Field(strict=True, ge=1, le=10)
    justificacion_probabilidad: str = Field(min_length=10, max_length=1000)
    justificacion_impacto: str = Field(min_length=10, max_length=1000)


class RiskItem(Strict):
    activo: str = Field(min_length=1, max_length=300)
    amenaza: str = Field(min_length=3, max_length=500)
    vulnerabilidad: str = Field(min_length=3, max_length=500)
    consecuencia: str = Field(min_length=3, max_length=1000)
    referencias: list[str] = Field(min_length=1, max_length=6)
    supuestos: list[str] = Field(max_length=8)
    informacion_faltante: list[str] = Field(max_length=8)
    calculo_id: str | None = None
    estrategia: Literal['mitigar', 'evitar', 'compartir', 'aceptar_propuesto']
    controles_ids: list[str] = Field(default_factory=list, max_length=8)
    acciones: list[str] = Field(min_length=1, max_length=8)
    responsable_propuesto: str = Field(min_length=1, max_length=150)
    plazo_propuesto: str = Field(min_length=1, max_length=150)
    evidencia_a_solicitar: list[str] = Field(min_length=1, max_length=8)
    requiere_eipd: bool


class FinishRisk(Strict):
    motivo: str = Field(min_length=3, max_length=350)
    estado: Literal['propuesta', 'evidencia_insuficiente']
    riesgos: list[RiskItem] = Field(max_length=5)
    limitaciones: list[str] = Field(min_length=1, max_length=10)


RISK_TOOLS = {
    'consultar_contexto_riesgos': (RiskRead, 'Consulta una página de GESTITEL en solo lectura; registra fuente, fecha y alcance.'),
    'calcular_riesgo': (Calculation, 'Calcula P*I con la metodología de la ejecución; valores propuestos, no aceptados. Devuelve calculo_id.'),
    'finalizar_riesgos': (FinishRisk, 'Entrega hasta cinco propuestas con referencias reales o declara evidencia insuficiente. No guarda cambios remotos.'),
}


def calculate(args, methodology):
    if max(args.probabilidad, args.impacto) > methodology.escala:
        raise ValueError('Puntuación fuera de la escala configurada.')
    score = args.probabilidad * args.impacto
    level = next(b.nivel for b in methodology.bandas if b.minimo <= score <= b.maximo)
    result = dict(probabilidad=args.probabilidad, impacto=args.impacto, puntaje=score, nivel=level,
                  justificacion_probabilidad=args.justificacion_probabilidad,
                  justificacion_impacto=args.justificacion_impacto,
                  metodologia=methodology.model_dump(), estado='estimacion_propuesta')
    key = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()[:24]
    return dict(result, calculo_id=key)


class RiskInput(Strict):
    fuente: Literal['manual', 'gestitel'] = 'manual'
    contexto: str = Field(default='', max_length=8000)
    metodologia: Methodology | None = None

    @model_validator(mode='after')
    def source_context(self):
        if self.fuente == 'manual' and not self.contexto.strip():
            raise ValueError('Escribe el contexto del activo o proceso a evaluar.')
        if self.fuente == 'gestitel' and self.metodologia is not None:
            raise ValueError('La metodología GESTITEL se recupera de su matriz activa.')
        if self.metodologia and self.metodologia.origen != 'propuesta_local':
            raise ValueError('No declares una matriz remota como configuración manual.')
        return self


class RiskWorkflow:
    def __init__(self, data):
        self.input = RiskInput.model_validate(data)
        self.methodology = (self.input.metodologia or demo_methodology()) if self.input.fuente == 'manual' else None
        self.calculations = {}
        self.reads = []

    def execute(self, agent, name, args):
        if name == 'consultar_contexto_riesgos':
            if self.input.fuente != 'gestitel':
                raise ValueError('Esta ejecución usa contexto manual; no consulta GESTITEL.')
            from .gestitel import GestitelClient
            if agent.gestitel_reads >= 6:
                raise ValueError('Máximo seis páginas por ejecución.')
            agent.gestitel_reads += 1
            if agent.gestitel_client is None:
                agent.gestitel_client = GestitelClient()
            result = agent.gestitel_client.read(args.modulo, args.pagina, risk=True)
            agent.evidence.update({c['id']: c for c in result['fragmentos']})
            self.reads.append({k: result[k] for k in ('modulo', 'pagina', 'total', 'consultado_en')})
            if args.modulo == 'evaluation-matrices':
                active = [json.loads(c['texto']) for c in result['fragmentos']
                          if '[REGISTRO TRUNCADO' not in c['texto']]
                active = [r for r in active if r.get('status') == 'A' and r.get('usage') in ('A', 'R')]
                if len(active) == 1:
                    method = from_gestitel(active[0])
                    if self.methodology and method != self.methodology:
                        self.calculations.clear()
                    self.methodology = method
            result['metodologia'] = self.methodology.model_dump() if self.methodology else None
            return result
        if name == 'calcular_riesgo':
            if self.methodology is None:
                raise ValueError('Consulta la matriz activa antes de calcular; no se asume escala.')
            result = calculate(args, self.methodology)
            self.calculations[result['calculo_id']] = result
            return result
        if args.estado == 'evidencia_insuficiente' and args.riesgos:
            raise ValueError('Una abstención no entrega riesgos propuestos.')
        if args.estado == 'propuesta' and not args.riesgos:
            raise ValueError('Entrega riesgos o declara evidencia insuficiente.')
        if self.input.fuente == 'gestitel' and not any(r['modulo'] == 'assets' for r in self.reads):
            raise ValueError('Consulta activos antes de concluir sobre GESTITEL.')
        risks = []
        for item in args.riesgos:
            refs = []
            for key in item.referencias:
                chunk = agent.evidence.get(key)
                if chunk is None:
                    raise ValueError('Referencia no recuperada en esta ejecución.')
                refs.append(dict(fragmento_id=key, fuente=chunk['fuente'], cita=chunk['texto'][:400],
                                 url=chunk.get('url'), consultado_en=chunk.get('consultado_en')))
            if self.input.fuente == 'gestitel':
                # El activo de una propuesta remota debe coincidir con un registro recuperado.
                assets = [json.loads(c['texto']) for c in agent.evidence.values()
                          if c.get('modulo') == 'assets' and '[REGISTRO TRUNCADO' not in c['texto']]
                match = [r for r in assets if item.activo in (str(r.get('id')), r.get('code'), r.get('name'))]
                cited_assets = [json.loads(agent.evidence[k]['texto']) for k in item.referencias
                                if agent.evidence[k].get('modulo') == 'assets'
                                and '[REGISTRO TRUNCADO' not in agent.evidence[k]['texto']]
                if not match or not any(r.get('id') == m.get('id') for r in cited_assets for m in match):
                    raise ValueError('Vincula el riesgo a un activo real recuperado y cítalo.')
            controls = []
            for key in item.controles_ids:
                chunk = agent.evidence.get(key)
                if not chunk or chunk.get('modulo') not in ('annex-a-controls', 'annex-a-assessments'):
                    raise ValueError('El control debe provenir del catálogo o evaluación recuperada.')
                controls.append(dict(fragmento_id=key, fuente=chunk['fuente'], cita=chunk['texto'][:400]))
            calculation = self.calculations.get(item.calculo_id) if item.calculo_id else None
            if item.calculo_id and calculation is None:
                raise ValueError('El cálculo debe haberse ejecutado con la herramienta.')
            if not calculation and not item.informacion_faltante:
                raise ValueError('Sin puntuación, declara la información que falta para evaluar.')
            risks.append(dict(item.model_dump(), referencias=refs, controles=controls,
                              evaluacion=calculation, estado='pendiente_revision_humana',
                              riesgo_residual=None))
        agent.result = dict(tipo='riesgos', version_contrato='1.0', estado_respuesta=args.estado,
            riesgos=risks, metodologia=self.methodology.model_dump() if self.methodology else None,
            alcance=self.reads, fuente=self.input.fuente,
            limitaciones=args.limitaciones + [
                'P*I es una fórmula propuesta; falta contrastarla con el backend de GESTITEL.',
                'Las puntuaciones y tratamientos requieren revisión; no se acepta riesgo residual automáticamente.',
                'No se escribieron registros en GESTITEL. Las referencias no prueban suficiencia semántica.'])
        return {'entregado': True, 'riesgos': len(risks)}
