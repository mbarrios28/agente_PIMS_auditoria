import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from pypdf import PdfReader
from src.priv_audit import history
from src.priv_audit.agent import RiskAgent
from src.priv_audit.gestitel import GestitelClient
from web_app import app

class DeliveryTests(TestCase):
    def setUp(self):
        folder=TemporaryDirectory();self.addCleanup(folder.cleanup)
        env=patch.dict(os.environ,PIMS_HISTORY_DB=str(Path(folder.name)/'history.sqlite3'))
        env.start();self.addCleanup(env.stop)
        self.client=app.test_client()
        result=dict(estado_respuesta='evidencia_insuficiente',riesgos=[],metodologia=None,alcance=[],limitaciones=['Sin activos <script>.'])
        self.key=history.save('riesgos','Objetivo <script>',result)

    def test_review_is_append_only_and_preserves_result(self):
        original=history.get(self.key)['resultado']
        body=dict(revisor='Revisor académico',decision='revisado',comentario='Revisar evidencia de restauración.')
        self.assertEqual(self.client.post(f'/api/history/{self.key}/review',json=body).status_code,201)
        body['decision']='requiere_cambios'
        self.assertEqual(self.client.post(f'/api/history/{self.key}/review',json=body).status_code,201)
        entry=self.client.get(f'/api/history/{self.key}').json
        self.assertEqual(len(entry['revisiones']),2)
        self.assertEqual(entry['resultado'],original)
        self.assertEqual(entry['revisiones'][0]['result_hash'],entry['revisiones'][1]['result_hash'])
        body['decision']='aceptar_riesgo'
        self.assertEqual(self.client.post(f'/api/history/{self.key}/review',json=body).status_code,400)

    def test_review_rejects_failed_legacy_and_missing_entries(self):
        keys=[history.save('chat','Anterior',{}),history.save('riesgos','Falló',{},status='error'),'missing']
        for key in keys:
            self.assertEqual(self.client.post(f'/api/history/{key}/review',json=dict(revisor='Persona',decision='revisado',comentario='Observación')).status_code,400)
            self.assertEqual(self.client.get(f'/api/risks/report/{key}').status_code,404)

    def test_pdf_escapes_text_and_contains_review(self):
        history.review(self.key,'Revisor EC2','revisado','Prueba de revisión.')
        with self.client.get(f'/api/risks/report/{self.key}') as response:
            self.assertEqual(response.status_code,200)
            text=' '.join(p.extract_text() for p in PdfReader(io.BytesIO(response.data)).pages)
        self.assertIn('Objetivo <script>',text)
        self.assertIn('Revisor EC2',text)
        self.assertIn('no acepta riesgo residual',text)

    def test_prepare_context_uses_fixed_first_pages(self):
        def read(module,page,**kwargs):
            return dict(modulo=module,pagina=page,total=0,consultado_en='2026-11-05',fragmentos=[])
        agent=RiskAgent()
        agent.execute('cargar_skill',dict(motivo='Preparar revisión',nombre='gestion_riesgos'))
        with patch('src.priv_audit.gestitel.GestitelClient.read',side_effect=read) as mock:
            agent.execute('preparar_contexto_riesgos',dict(motivo='Obtener contexto operativo'))
        self.assertEqual([c.args for c in mock.call_args_list],[('assets',1),('processes',1),('evaluation-matrices',1)])
        self.assertEqual(agent.gestitel_reads,3)

    @patch.dict(os.environ,{'GESTITEL_USERNAME':'fake','GESTITEL_PASSWORD':'fake'})
    @patch('src.priv_audit.gestitel._request')
    def test_detail_is_bounded_and_minimized(self,request):
        request.side_effect=[{'access':'fake-token'},{'id':72,'code':'A.8.13','name':'Copias','responsible':'Privado'}]
        result=GestitelClient().read('annex-a-controls',risk=True,record_id=72)
        self.assertEqual(request.call_args.args[0],'/api/annex-a-controls/72/')
        self.assertEqual(result['total'],1)
        self.assertNotIn('Privado',result['fragmentos'][0]['texto'])
        with self.assertRaises(ValueError):GestitelClient().read('users',risk=True,record_id=1)
        with self.assertRaises(ValueError):GestitelClient().read('assets',risk=True,record_id=-1)

    def test_calculation_advances_to_finalization(self):
        from test_risk import seed
        agent=RiskAgent()
        agent.execute('cargar_skill',dict(motivo='Preparar revisión',nombre='gestion_riesgos'))
        seed(agent)
        agent.execute('calcular_riesgo',dict(motivo='Valorar escenario',probabilidad=3,impacto=4,
            justificacion_probabilidad='Hipótesis explícita de prueba',justificacion_impacto='Consecuencia del ejercicio'))
        names=[t['function']['name'] for t in agent.available_tools()]
        self.assertEqual(names,['finalizar_riesgos'])

    def test_quota_can_be_deferred_without_switching_provider(self):
        from src.priv_audit.providers import ProviderRouter
        from types import SimpleNamespace
        error=RuntimeError('Cuota temporal');error.status_code=429
        primary=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: (_ for _ in ()).throw(error))))
        router=ProviderRouter(primary=primary,defer_quota=True)
        with self.assertRaises(RuntimeError):router.create(messages=[])
        self.assertEqual(router.provider,'groq')

    def test_final_tool_lists_only_retrieved_identifiers(self):
        from test_risk import seed
        agent=RiskAgent();seed(agent)
        tool=next(t for t in agent.available_tools() if t['function']['name']=='cargar_skill')
        agent.execute('cargar_skill',dict(motivo='Preparar revisión',nombre='gestion_riesgos'))
        tool=next(t for t in agent.available_tools() if t['function']['name']=='finalizar_riesgos')
        props=tool['function']['parameters']['properties']['riesgos']['items']['properties']
        self.assertEqual(props['activo']['enum'],['1'])
        self.assertEqual(props['referencias']['items']['enum'],['asset1'])
