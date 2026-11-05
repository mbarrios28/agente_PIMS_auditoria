import json
import os
import unittest
from unittest.mock import patch
from src.priv_audit.agent import PrivacyAgent, tools_for
from src.priv_audit.risk import Calculation, Methodology, calculate, demo_methodology, from_gestitel


class RiskTests(unittest.TestCase):
    def agent(self):
        agent = PrivacyAgent(task='riesgos', objective='Evaluar servidor de prueba',
                             risk_input={'contexto': 'Servidor ficticio sin respaldos verificados.'})
        agent.execute('cargar_skill', {'motivo': 'Preparar revisión', 'nombre': 'gestion_riesgos'})
        return agent

    def item(self):
        return dict(activo='Servidor ficticio', amenaza='Pérdida de información',
            vulnerabilidad='Respaldos no verificados', consecuencia='Interrupción del servicio',
            referencias=['contexto_manual'], supuestos=['Caso ficticio'], informacion_faltante=['Prueba de restauración'],
            estrategia='mitigar', acciones=['Probar restauración'], responsable_propuesto='Operaciones',
            plazo_propuesto='Propuesta: 30 días', evidencia_a_solicitar=['Acta de prueba'], requiere_eipd=False)

    def test_calculation_boundaries(self):
        method = demo_methodology()
        for p, i, level in [(1, 1, 'BAJO'), (2, 2, 'MEDIO'), (2, 4, 'ALTO'), (4, 4, 'CRITICO')]:
            args = Calculation(motivo='Valorar escenario', probabilidad=p, impacto=i,
                justificacion_probabilidad='Estimación de prueba', justificacion_impacto='Impacto de prueba')
            self.assertEqual(calculate(args, method)['nivel'], level)
        with self.assertRaises(ValueError):
            calculate(args.model_copy(update={'probabilidad': 5}), method)
        with self.assertRaises(ValueError):
            Calculation.model_validate(dict(args.model_dump(), probabilidad=True))

    def test_invalid_ranges_and_remote_scales(self):
        method = demo_methodology().model_dump()
        method['bandas'][1]['minimo'] = 3
        with self.assertRaises(ValueError):
            Methodology.model_validate(method)
        with self.assertRaises(ValueError):
            from_gestitel(dict(dimension=4, levels=[]))

    def test_tools_are_isolated(self):
        names = lambda task: {t['function']['name'] for t in tools_for(task)}
        self.assertIn('calcular_riesgo', names('riesgos'))
        for task in ('consulta', 'gestitel', 'auditoria'):
            self.assertNotIn('calcular_riesgo', names(task))
        self.assertNotIn('validar_informe', names('riesgos'))

    def test_skill_required_and_citations(self):
        agent = PrivacyAgent(task='riesgos', risk_input={'contexto':'Caso ficticio'})
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
        self.assertEqual(risk['referencias'][0]['fragmento_id'], 'contexto_manual')

    def test_no_fake_calculations_or_controls(self):
        for extra in ({'calculo_id':'inventado'}, {'controles_ids':['contexto_manual']}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                self.agent().execute('finalizar_riesgos', dict(motivo='Entregar revisión', estado='propuesta',
                    riesgos=[dict(self.item(), **extra)], limitaciones=['Prueba']))

    def test_live_source_cannot_invent_assets_or_default_matrix(self):
        agent = PrivacyAgent(task='riesgos', risk_input={'fuente':'gestitel'})
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

    def test_api_contract_and_validation(self):
        from web_app import app
        client = app.test_client()
        self.assertFalse(client.get('/api/risks/contract').json['escritura_gestitel'])
        with patch.dict(os.environ, {'GROQ_API_KEY':'fake'}):
            response = client.post('/api/agent/runs', json={'tarea':'riesgos','objetivo':'Evaluar servidor','riesgos':{'contexto':''}})
            self.assertEqual(response.status_code, 400)
            with patch('src.priv_audit.jobs.runs.start', return_value='run1') as start:
                response = client.post('/api/agent/runs', json={'tarea':'riesgos','objetivo':'Evaluar servidor','riesgos':{'contexto':'Servidor ficticio'}})
                self.assertEqual(response.status_code, 202)
                self.assertEqual(start.call_args.args[0]['risk_input']['fuente'], 'manual')


if __name__ == '__main__':
    unittest.main()


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
        agent = PrivacyAgent(task='riesgos', risk_input={'contexto':'Servidor ficticio'}, client=mock)
        with patch('src.priv_audit.rag_loader.diagnostico_documentos', return_value=[]):
            result = agent.run()
        self.assertEqual(result['turnos'], 3)
        self.assertTrue(any(e['estado'] == 'rechazado' for e in result['traza']))
        self.assertEqual(result['tipo'], 'riesgos')
