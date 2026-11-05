import unittest
from unittest.mock import patch
from src.priv_audit.gestitel import GestitelClient

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
