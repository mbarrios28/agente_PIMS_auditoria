"""El chat histórico ya no es una función de la aplicación."""
from unittest import TestCase
from web_app import app

class RemovedChatTests(TestCase):
    def test_chat_is_not_exposed(self):
        self.assertEqual(app.test_client().post('/api/chat',json={'question':'hola'}).status_code,404)
