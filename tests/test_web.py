import unittest
from unittest.mock import patch
from web_app import app
from src.priv_audit.service import audit, parse_schema

class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_and_status(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertTrue(self.client.get('/api/status').json['documentos'])

    def test_blank_and_invalid_inputs(self):
        for data in ({'sql':''}, {'sql':42}, {'sql':'SELECT 1'}, {'sql':'CREATE TABLE persona (dni INT)', 'dialect':42}):
            self.assertEqual(self.client.post('/api/audit',json=data).status_code,400)

    def test_parse_schema_qualified_names(self):
        tables = parse_schema('CREATE TABLE IF NOT EXISTS `app`.`persona` (`dni` VARCHAR(8), id INT PRIMARY KEY);')
        self.assertEqual(tables[0]['columns'][0]['name'], 'dni')
        self.assertIn('persona', tables[0]['name'])

    def test_local_mode_and_pdf(self):
        with patch.dict('os.environ', {'GROQ_API_KEY':''}):
            report = self.client.post('/api/audit',json={'sql':'CREATE TABLE persona (dni VARCHAR(8), religion TEXT);'}).json
        self.assertEqual(report['conteo']['ALTO'],1)
        self.assertEqual(report['modo'],'local')
        result = self.client.post('/api/report',json=report)
        self.assertEqual(result.status_code,200)
        self.assertTrue(result.data.startswith(b'%PDF'))

    def test_no_findings_is_a_result(self):
        self.assertEqual(audit('CREATE TABLE catalogo (id INT, codigo INT)')['hallazgos'], [])

    def test_cross_origin_write_rejected(self):
        self.assertEqual(self.client.post('/api/audit',json={'sql':'x'},headers={'Origin':'https://otro.example'}).status_code,403)

    def test_local_chat_no_key(self):
        with patch.dict('os.environ',{'GROQ_API_KEY':''}):
            response = self.client.post('/api/chat',json={'question':'consentimiento datos'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['mode'],'local')
        self.assertTrue(response.json['sources'])

    def test_report_escapes_sql(self):
        report = audit('CREATE TABLE persona (email VARCHAR(100));')
        report['hallazgos'][0]['evidencia'] = "CHECK (id < 3 AND email <> '') & <b>texto</b>"
        self.assertEqual(self.client.post('/api/report',json=report).status_code,200)

if __name__ == '__main__':
    unittest.main()
