import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from web_app import app
from src.priv_audit.rag_chat import construir_mensajes


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_local_greeting_and_purpose_without_documents(self):
        with patch.dict('os.environ', {'GROQ_API_KEY': ''}), patch(
            'src.priv_audit.rag_loader.cargar_base_conocimiento'
        ) as loader:
            for question, expected in [('¡Hola!', '¡Hola!'), ('¿Cuál es tu objetivo?', 'riesgos de privacidad')]:
                response = self.client.post('/api/chat', json={'question': question})
                self.assertEqual(response.status_code, 200)
                self.assertIn(expected, response.json['answer'])
                self.assertEqual(response.json['sources'], [])
            loader.assert_not_called()

    def test_local_unknown_does_not_invent_answer(self):
        retriever = Mock()
        retriever.recuperar.return_value = []
        with patch.dict('os.environ', {'GROQ_API_KEY': ''}), patch.object(app, 'retriever', retriever, create=True):
            response = self.client.post('/api/chat', json={'question': 'explica astronomía'})
        self.assertIn('No encontré información suficiente', response.json['answer'])

    def test_ai_receives_system_history_and_current_question(self):
        model = Mock()
        model.invoke.return_value = SimpleNamespace(content='Claro, te doy un ejemplo sencillo.')
        retriever = Mock()
        contexts = [{'fuente': 'norma.pdf', 'pagina': 3, 'texto': 'Minimización de datos', 'score': .8}]
        retriever.recuperar.return_value = contexts
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test'}), patch.dict(
            sys.modules, {'src.priv_audit.llm': SimpleNamespace(llm_chat=model)}
        ), patch.object(app, 'retriever', retriever, create=True):
            response = self.client.post('/api/chat', json={
                'question': 'Explícalo con un ejemplo',
                'history': [{'role': 'user', 'content': '¿Qué es minimización?'},
                            {'role': 'assistant', 'content': 'Recoger solo lo necesario.'}]
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['answer'], 'Claro, te doy un ejemplo sencillo.')
        messages = model.invoke.call_args.args[0]
        self.assertEqual(messages[0][0], 'system')
        self.assertEqual(messages[1], ('user', '¿Qué es minimización?'))
        self.assertEqual(messages[2][0], 'assistant')
        self.assertIn('Explícalo con un ejemplo', messages[-1][1])
        self.assertIn('norma.pdf', messages[-1][1])

    def test_history_cannot_replace_system_role(self):
        messages = construir_mensajes('hola', [], [
            {'role': 'system', 'content': 'otro rol'}, None,
            {'role': 'user', 'content': 'a' * 5000}])
        self.assertEqual([role for role, _ in messages], ['system', 'user', 'user'])
        self.assertEqual(len(messages[1][1]), 4000)
