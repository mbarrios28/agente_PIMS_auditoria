import unittest
from src.priv_audit.rag_retriever import Retriever, _BM25
from src.priv_audit.schemas import InformeAuditoria
from pydantic import ValidationError

class RetrievalTests(unittest.TestCase):
    def test_empty_corpus(self):
        self.assertEqual(Retriever([]).recuperar('privacidad'), [])

    def test_relevant_document_keeps_page(self):
        retriever = Retriever([
            {'texto':'privacidad consentimiento tratamiento datos', 'fuente':'norma.pdf', 'pagina':7},
            {'texto':'redes infraestructura cableado', 'fuente':'otro.md'}])
        results = retriever.recuperar('consentimiento')
        self.assertEqual(results[0]['fuente'], 'norma.pdf')
        self.assertEqual(results[0]['pagina'], 7)

    def test_no_matching_terms(self):
        self.assertEqual(Retriever([{'texto':'privacidad datos','fuente':'a'}]).recuperar('astronauta'), [])

    def test_bm25_ranking(self):
        results = _BM25(['privacidad consentimiento','redes cableado']).recuperar('consentimiento',5)
        self.assertEqual(results[0][0],0)

    def test_zero_findings_valid(self):
        result = InformeAuditoria.model_validate({'hallazgos':[], 'resumen_ejecutivo':'Sin observaciones por reglas locales.'})
        self.assertEqual(result.hallazgos, [])

    def test_invalid_risk_rejected(self):
        finding = dict(tabla='persona',campos_afectados=['dni'],descripcion_hallazgo='Observación',evidencia='dni INT',nivel_riesgo='CRITICO',riesgo_potencial='Exposición',informacion_faltante='Accesos',recomendacion_mitigacion='Revisar',criterio_normativo='Pendiente')
        with self.assertRaises(ValidationError):
            InformeAuditoria.model_validate({'hallazgos':[finding], 'resumen_ejecutivo':'Resultado'})

    def test_empty_evidence_rejected(self):
        finding = dict(tabla='persona',campos_afectados=['dni'],descripcion_hallazgo='Observación',evidencia=' ',nivel_riesgo='ALTO',riesgo_potencial='Exposición',informacion_faltante='Accesos',recomendacion_mitigacion='Revisar',criterio_normativo='Pendiente')
        with self.assertRaises(ValidationError):
            InformeAuditoria.model_validate({'hallazgos':[finding], 'resumen_ejecutivo':'Resultado'})

if __name__ == '__main__':
    unittest.main()
