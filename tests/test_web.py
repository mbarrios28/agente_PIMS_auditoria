import os
from unittest import TestCase
from unittest.mock import patch
from web_app import app

class ApplicationTests(TestCase):
    def setUp(self):
        self.client=app.test_client()

    def test_home_has_only_risk_workflow(self):
        page=self.client.get('/').data.decode()
        for expected in ('risk-form','risk-objective','GESTITEL'):
            self.assertIn(expected,page)
        for removed in ('risk-context','risk-source','risk-method','risk-example','page-audit','page-chat','page-agent'):
            self.assertNotIn(removed,page)
        with self.client.get('/static/risk.js') as response:
            self.assertEqual(response.status_code,200)

    def test_removed_endpoints_and_task_types(self):
        for path in ('/api/audit','/api/chat','/api/report'):
            self.assertEqual(self.client.post(path,json={}).status_code,404)
        for task in ('auditoria','consulta','gestitel'):
            self.assertEqual(self.client.post('/api/agent/runs',json={'tarea':task,'objetivo':'Revisar'}).status_code,400)

    def test_manual_context_and_methodology_rejected_at_all_levels(self):
        for extra in ({'contexto':'Texto'}, {'fuente':'manual'}, {'metodologia':{}}, {'fuente':'gestitel','contexto':'Texto'}):
            result=self.client.post('/api/agent/runs',json={'objetivo':'Revisar riesgos','riesgos':extra})
            self.assertEqual(result.status_code,400)
        self.assertEqual(self.client.post('/api/agent/runs',json={'objetivo':'Revisar','contexto':'Texto'}).status_code,400)

    def test_cross_origin_and_configuration(self):
        self.assertEqual(self.client.post('/api/agent/runs',json={},headers={'Origin':'https://otro.example'}).status_code,403)
        with patch.dict(os.environ,{'GROQ_API_KEY':''}):
            self.assertEqual(self.client.post('/api/agent/runs',json={'objetivo':'Revisar riesgos'}).status_code,400)

    def test_status_and_contract(self):
        status=self.client.get('/api/status').json
        self.assertEqual(status['agente'],'riesgos')
        self.assertNotIn('demo',status)
        contract=self.client.get('/api/risks/contract').json
        self.assertEqual(contract['fuente'],'gestitel')
        self.assertNotIn('metodologia_ejemplo',contract)
