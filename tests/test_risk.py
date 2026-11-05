import json
import os
import unittest
from unittest.mock import patch
from src.priv_audit.agent import RiskAgent, tools_for
from src.priv_audit.risk import Calculation, Methodology, calculate, from_gestitel


def methodology():
    return Methodology(nombre='Matriz remota simulada', version='1', escala=4,
        bandas=[dict(nivel=n,minimo=a,maximo=b) for n,a,b in
                [('BAJO',1,3),('MEDIO',4,7),('ALTO',8,11),('CRITICO',12,16)]])


def seed(agent):
    agent.risk.methodology = methodology()
    agent.risk.reads.append(dict(modulo='assets',pagina=1,total=1,consultado_en='2026-11-05'))
    agent.evidence['asset1'] = dict(id='asset1',modulo='assets',fuente='GESTITEL / assets / 1',
        texto=json.dumps(dict(id=1,name='Servidor ficticio')),consultado_en='2026-11-05')


class RiskTests(unittest.TestCase):
    def agent(self):
        agent = RiskAgent(task='riesgos', objective='Evaluar servidor de prueba',
                             risk_input={})
        agent.execute('cargar_skill', {'motivo': 'Preparar revisión', 'nombre': 'gestion_riesgos'})
        seed(agent)
        return agent

    def item(self):
        return dict(activo='Servidor ficticio', amenaza='Pérdida de información',
            vulnerabilidad='Respaldos no verificados', consecuencia='Interrupción del servicio',
            referencias=['asset1'], supuestos=['Caso ficticio'], informacion_faltante=['Prueba de restauración'],
            estrategia='mitigar', acciones=['Probar restauración'], responsable_propuesto='Operaciones',
            plazo_propuesto='Propuesta: 30 días', evidencia_a_solicitar=['Acta de prueba'], requiere_eipd=False)

    def test_calculation_boundaries(self):
        method = methodology()
        for p, i, level in [(1, 1, 'BAJO'), (2, 2, 'MEDIO'), (2, 4, 'ALTO'), (4, 4, 'CRITICO')]:
            args = Calculation(motivo='Valorar escenario', probabilidad=p, impacto=i,
                justificacion_probabilidad='Estimación de prueba', justificacion_impacto='Impacto de prueba')
            self.assertEqual(calculate(args, method)['nivel'], level)
        with self.assertRaises(ValueError):
            calculate(args.model_copy(update={'probabilidad': 5}), method)
        with self.assertRaises(ValueError):
            Calculation.model_validate(dict(args.model_dump(), probabilidad=True))

    def test_invalid_ranges_and_remote_scales(self):
        method = methodology().model_dump()
        method['bandas'][1]['minimo'] = 3
        with self.assertRaises(ValueError):
            Methodology.model_validate(method)
        with self.assertRaises(ValueError):
            from_gestitel(dict(dimension=4, levels=[]))

    def test_tools_are_isolated(self):
        names = lambda task: {t['function']['name'] for t in tools_for(task)}
        self.assertIn('calcular_riesgo', names('riesgos'))
        for task in ('consulta', 'gestitel', 'auditoria'):
            with self.assertRaises(ValueError):
                names(task)
        self.assertNotIn('validar_informe', names('riesgos'))

    def test_skill_required_and_citations(self):
        agent = RiskAgent(task='riesgos', risk_input={})
        with self.assertRaises(ValueError):
            agent.execute('finalizar_riesgos', dict(motivo='Entregar revisión', estado='evidencia_insuficiente', riesgos=[], limitaciones=['Sin datos']))
        agent = self.agent()
        item = self.item()
        item['referencias'] = ['inventada']
        with self.assertRaises(ValueError):
            agent.execute('finalizar_riesgos', dict(motivo='Entregar revisión', estado='propuesta', riesgos=[item], limitaciones=['Caso ficticio']))

    def test_proposal_resolves_calculation_and_no_residual(self):
        agent = self.agent()
        calc = agent.execute('calcular_riesgo', dict(motivo='Estimar escenario', probabilidad=3, impacto=4,
            justificacion_probabilidad='Hipótesis del ejercicio', justificacion_impacto='Servicio esencial ficticio'))
        item = dict(self.item(), calculo_id=calc['calculo_id'])
        agent.execute('finalizar_riesgos', dict(motivo='Entregar propuesta', estado='propuesta', riesgos=[item], limitaciones=['Ejercicio']))
        risk = agent.result['riesgos'][0]
        self.assertEqual(risk['evaluacion']['puntaje'], 12)
        self.assertIsNone(risk['riesgo_residual'])
        self.assertEqual(risk['estado'], 'pendiente_revision_humana')
        self.assertEqual(risk['referencias'][0]['fragmento_id'], 'asset1')

    def test_no_fake_calculations_or_controls(self):
        for extra in ({'calculo_id':'inventado'}, {'controles_ids':['asset1']}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.agent().execute('finalizar_riesgos', dict(motivo='Entregar revisión', estado='propuesta',
                    riesgos=[dict(self.item(), **extra)], limitaciones=['Prueba']))

    def test_live_source_cannot_invent_assets_or_default_matrix(self):
        agent = RiskAgent(task='riesgos', risk_input={'fuente':'gestitel'})
        agent.execute('cargar_skill', {'motivo':'Preparar revisión', 'nombre':'gestion_riesgos'})
        with self.assertRaises(ValueError):
            agent.execute('calcular_riesgo', dict(motivo='Estimar riesgo', probabilidad=1, impacto=1,
                justificacion_probabilidad='Sin datos para valorar', justificacion_impacto='Sin datos para valorar'))
        result = dict(modulo='assets', pagina=1, total=0, consultado_en='2026-11-05', fragmentos=[])
        with patch('src.priv_audit.gestitel.GestitelClient.read', return_value=result):
            agent.execute('consultar_contexto_riesgos', dict(motivo='Consultar activos', modulo='assets'))
        with self.assertRaises(ValueError):
            agent.execute('finalizar_riesgos', dict(motivo='Entregar revisión', estado='propuesta', riesgos=[self.item()], limitaciones=['Sin activos']))
        agent.execute('finalizar_riesgos', dict(motivo='Informar limitaciones', estado='evidencia_insuficiente', riesgos=[], limitaciones=['No hay activos cargados']))
        self.assertEqual(agent.result['estado_respuesta'], 'evidencia_insuficiente')

    def test_live_matrix_is_used_and_asset_reference_must_match(self):
        agent = RiskAgent(task='riesgos', risk_input={'fuente':'gestitel'})
        agent.execute('cargar_skill', {'motivo':'Preparar revisión', 'nombre':'gestion_riesgos'})
        matrix = dict(id=2, name='Matriz de prueba', dimension=4, status='A', usage='A',
            levels=[dict(axis=a, value=str(v)) for a in ('P','I') for v in range(1,5)],
            risk_ranges=[dict(level=n, min_value=a, max_value=b) for n,a,b in
                         [('L',1,3),('M',4,7),('H',8,11),('C',12,16)]])
        def read(module, page, **kwargs):
            rows = [matrix] if module == 'evaluation-matrices' else [dict(id=1,name='Servidor A'),dict(id=2,name='Servidor B')]
            return dict(modulo=module,pagina=page,total=len(rows),consultado_en='2026-11-05',
                fragmentos=[dict(id=f'{module}-{i}',modulo=module,texto=json.dumps(r),fuente=module) for i,r in enumerate(rows)])
        with patch('src.priv_audit.gestitel.GestitelClient.read', side_effect=read):
            for module in ('assets','evaluation-matrices'):
                agent.execute('consultar_contexto_riesgos', dict(motivo='Recuperar contexto',modulo=module))
        self.assertEqual(agent.risk.methodology.matriz_id, '2')
        item = dict(self.item(), activo='Servidor A', referencias=['assets-1'])
        with self.assertRaises(ValueError):
            agent.execute('finalizar_riesgos', dict(motivo='Entregar propuesta',estado='propuesta',riesgos=[item],limitaciones=['Prueba']))
        item['referencias'] = ['assets-0']
        agent.execute('finalizar_riesgos', dict(motivo='Entregar propuesta',estado='propuesta',riesgos=[item],limitaciones=['Prueba']))
        self.assertEqual(agent.result['riesgos'][0]['activo'], 'Servidor A')

    def test_api_contract_and_validation(self):
        from web_app import app
        client = app.test_client()
        self.assertFalse(client.get('/api/risks/contract').json['escritura_gestitel'])
        with patch.dict(os.environ, {'GROQ_API_KEY':'fake','GESTITEL_USERNAME':'fake','GESTITEL_PASSWORD':'fake'}):
            response = client.post('/api/agent/runs', json={'tarea':'riesgos','objetivo':'Evaluar servidor','riesgos':{'contexto':'No permitido'}})
            self.assertEqual(response.status_code, 400)
            with patch('src.priv_audit.jobs.runs.start', return_value='run1') as start:
                response = client.post('/api/agent/runs', json={'tarea':'riesgos','objetivo':'Evaluar servidor','riesgos':{}})
                self.assertEqual(response.status_code, 202)
                self.assertEqual(start.call_args.args[0]['risk_input']['fuente'], 'gestitel')


class RiskLoopTests(unittest.TestCase):
    def test_model_can_recover_from_invalid_calculation_and_finish(self):
        from test_agent import call, response
        from types import SimpleNamespace
        reason = {'motivo':'Preparar evaluación de prueba'}
        calls = [
            call('cargar_skill', dict(reason, nombre='gestion_riesgos')),
            call('calcular_riesgo', dict(reason, probabilidad=9, impacto=2,
                justificacion_probabilidad='Supuesto de prueba', justificacion_impacto='Impacto de prueba')),
            call('finalizar_riesgos', dict(reason, estado='propuesta', riesgos=[RiskTests().item()], limitaciones=['Caso ficticio']))]
        mock = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: response(calls.pop(0)))))
        agent = RiskAgent(task='riesgos', risk_input={}, client=mock)
        seed(agent)
        with patch('src.priv_audit.rag_loader.diagnostico_documentos', return_value=[]):
            result = agent.run()
        self.assertEqual(result['turnos'], 3)
        self.assertTrue(any(e['estado'] == 'rechazado' for e in result['traza']))
        self.assertEqual(result['tipo'], 'riesgos')
