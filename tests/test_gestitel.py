import unittest
from unittest.mock import patch
from src.priv_audit.gestitel import GestitelClient
from src.priv_audit.agent import PrivacyAgent, tools_for

class GestitelTests(unittest.TestCase):
    @patch.dict('os.environ', {'GESTITEL_USERNAME':'demo', 'GESTITEL_PASSWORD':'secret'})
    @patch('src.priv_audit.gestitel._request')
    def test_allowlist_session_reuse_and_minimization(self, request):
        request.side_effect = [{'access':'token'}, {'count':1,'next':None,'results':[{'id':7,'evidence':'Acta', 'responsible':'Persona','created_by':8}]}, {'count':0,'next':None,'results':[]}]
        client = GestitelClient()
        with self.assertRaises(ValueError):client.read('users')
        request.assert_not_called()
        result = client.read('gap-requirements')
        text = result['fragmentos'][0]['texto']
        self.assertIn('Acta',text)
        self.assertNotIn('Persona',text)
        self.assertNotIn('created_by',text)
        self.assertTrue(result['fragmentos'][0]['consultado_en'])
        client.read('annex-a-controls')
        self.assertEqual(request.call_count,3)

    def test_tool_is_only_available_for_gestitel(self):
        for task in ('consulta','auditoria'):
            self.assertNotIn('consultar_gestitel', [t['function']['name'] for t in tools_for(task)])
        self.assertIn('consultar_gestitel', [t['function']['name'] for t in tools_for('gestitel')])

    @patch('src.priv_audit.gestitel.GestitelClient.read')
    def test_retrieved_records_resolve_to_real_citations(self, read):
        chunk = dict(id='real',texto='Evidencia pendiente',fuente='GESTITEL',url='https://unsa.27k.pe/api/gap-requirements/1/',tipo_fuente='registro_operativo')
        read.return_value = {'fragmentos':[chunk]}
        agent = PrivacyAgent(task='gestitel')
        reason = {'motivo':'Revisar evidencia.'}
        agent.execute('cargar_skill',dict(reason,nombre='consulta_pims'))
        agent.execute('consultar_gestitel',dict(reason,modulo='gap-requirements'))
        agent.searches = 1
        agent.execute('finalizar_consulta',dict(reason,estado='respondida',conclusiones=[{'afirmacion':'Solicitar evidencia para revisión.', 'tipo':'propuesta','referencias':[{'fragmento_id':'real'}]}],limitaciones=['Revisión parcial.']))
        self.assertEqual(agent.result['conclusiones'][0]['referencias'][0]['cita'],'Evidencia pendiente')
        with self.assertRaises(ValueError):agent.citations([__import__('src.priv_audit.agent',fromlist=['Citation']).Citation(fragmento_id='real')],primary=True)
        for _ in range(5):agent.execute('consultar_gestitel',dict(reason,modulo='gap-requirements'))
        with self.assertRaisesRegex(ValueError,'seis'):agent.execute('consultar_gestitel',dict(reason,modulo='gap-requirements'))
