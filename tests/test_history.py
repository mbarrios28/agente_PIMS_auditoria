import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from web_app import app
from src.priv_audit import history
from src.priv_audit.jobs import RunStore


class HistoryTests(TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        environment = patch.dict(os.environ, PIMS_HISTORY_DB=str(Path(folder.name) / 'history.sqlite3'), GROQ_API_KEY='')
        environment.start()
        self.addCleanup(environment.stop)
        self.client = app.test_client()

    def test_only_risk_history_is_visible_without_deleting_legacy_entries(self):
        legacy=history.save('chat','Anterior',{'answer':'Conservado'})
        key=history.save('riesgos','Evaluar activos',{'riesgos':[]})
        page=self.client.get('/api/history').json
        self.assertEqual(page['total'],1)
        self.assertEqual(page['items'][0]['id'],key)
        self.assertEqual(self.client.get('/api/history/'+legacy).status_code,404)
        self.assertEqual(history.get(legacy)['resultado']['answer'],'Conservado')
        self.assertEqual(app.test_client().get('/api/history').json['total'],1)

    def test_async_result_and_error_survive_run_store_expiry(self):
        store = RunStore(ttl=-1)
        self.addCleanup(store.executor.shutdown)
        payload = dict(tarea='riesgos', objetivo='Evaluar activos')
        with patch('src.priv_audit.jobs.RiskAgent') as agent:
            agent.return_value.run.return_value = {'conclusiones':[], 'traza':[]}
            key = store.start(payload)
            store.executor.shutdown(wait=True)
        self.assertIsNone(store.get(key))
        self.assertEqual(history.get(key)['resultado']['conclusiones'], [])
        other = RunStore()
        self.addCleanup(other.executor.shutdown)
        with patch('src.priv_audit.jobs.RiskAgent') as agent:
            agent.return_value.run.side_effect = ValueError('Evidencia insuficiente')
            key = other.start(payload)
            other.executor.shutdown(wait=True)
        self.assertEqual(history.get(key)['estado'], 'error')
        self.assertEqual(history.get(key)['resultado']['error'], 'Evidencia insuficiente')

    def test_invalid_pagination_missing_entry_and_rejected_audit(self):
        for query in ('limit=0', 'limit=101', 'offset=-1', 'limit=texto'):
            self.assertEqual(self.client.get('/api/history?' + query).status_code, 400)
        self.assertEqual(self.client.get('/api/history/missing').status_code, 404)
        self.assertEqual(self.client.post('/api/audit', json={'sql':''}).status_code, 404)
        self.assertEqual(history.list_entries()['total'], 0)
