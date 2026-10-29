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

    def test_audit_and_chat_persist_and_can_be_reopened(self):
        audit = self.client.post('/api/audit', json={'sql':'CREATE TABLE persona (email TEXT);'}).json
        chat = self.client.post('/api/chat', json={'question':'hola'}).json
        page = self.client.get('/api/history').json
        self.assertEqual(page['total'], 2)
        entries = {item['tipo']:self.client.get('/api/history/' + item['id']).json for item in page['items']}
        self.assertEqual(entries['auditoria']['resultado'], audit)
        self.assertEqual(entries['chat']['resultado'], chat)
        # New application client and fresh SQLite connections still find the records.
        self.assertEqual(app.test_client().get('/api/history').json['total'], 2)
        self.assertEqual(history.list_entries(1, 1)['total'], 2)
        self.assertEqual(len(history.list_entries(1, 1)['items']), 1)

    def test_async_result_and_error_survive_run_store_expiry(self):
        store = RunStore(ttl=-1)
        self.addCleanup(store.executor.shutdown)
        payload = dict(tarea='consulta', objetivo='Comparar agentes')
        with patch('src.priv_audit.jobs.PrivacyAgent') as agent:
            agent.return_value.run.return_value = {'conclusiones':[], 'traza':[]}
            key = store.start(payload)
            store.executor.shutdown(wait=True)
        self.assertIsNone(store.get(key))
        self.assertEqual(history.get(key)['resultado']['conclusiones'], [])
        other = RunStore()
        self.addCleanup(other.executor.shutdown)
        with patch('src.priv_audit.jobs.PrivacyAgent') as agent:
            agent.return_value.run.side_effect = ValueError('Evidencia insuficiente')
            key = other.start(payload)
            other.executor.shutdown(wait=True)
        self.assertEqual(history.get(key)['estado'], 'error')
        self.assertEqual(history.get(key)['resultado']['error'], 'Evidencia insuficiente')

    def test_invalid_pagination_missing_entry_and_rejected_audit(self):
        for query in ('limit=0', 'limit=101', 'offset=-1', 'limit=texto'):
            self.assertEqual(self.client.get('/api/history?' + query).status_code, 400)
        self.assertEqual(self.client.get('/api/history/missing').status_code, 404)
        self.assertEqual(self.client.post('/api/audit', json={'sql':''}).status_code, 400)
        self.assertEqual(history.list_entries()['total'], 0)
