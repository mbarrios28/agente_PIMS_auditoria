"""La recuperación normativa de riesgos no puede salir de ISO 27701:2025."""
from unittest import TestCase
from unittest.mock import patch

from src.priv_audit import rag_loader
from src.priv_audit.agent import RiskAgent


class RiskNormativeScopeTests(TestCase):
    def agent(self):
        agent = RiskAgent()
        agent.execute('cargar_skill', {'motivo': 'Preparar revisión', 'nombre': 'gestion_riesgos'})
        return agent

    def test_explicit_foreign_source_is_rejected(self):
        for source in ('iso_27005_alcance.md', 'ISO-42001-2023.pdf', 'ley_29733_peru.md'):
            with self.subTest(source=source), patch('src.priv_audit.agent.obtener_retriever') as retrieve:
                with self.assertRaisesRegex(ValueError, 'única fuente normativa'):
                    self.agent().execute('buscar_documentos', {
                        'motivo': 'Buscar criterios', 'consulta': 'privacy risk', 'fuente': source})
                retrieve.assert_not_called()

    def test_unfiltered_search_cannot_return_foreign_norms(self):
        source = rag_loader.RISK_NORMATIVE_SOURCE
        chunks = [dict(id='iso', fuente=source, texto='privacy risk assessment', pagina=13),
                  dict(id='foreign', fuente='iso_27005_alcance.md', texto='privacy risk assessment')]
        with patch.object(rag_loader, '_signature', return_value=()), \
             patch.object(rag_loader, '_load', return_value=(chunks, [])):
            rag_loader._retriever.cache_clear()
            try:
                result = self.agent().execute('buscar_documentos', {
                    'motivo': 'Buscar criterios', 'consulta': 'privacy risk assessment'})
            finally:
                rag_loader._retriever.cache_clear()
        self.assertEqual({c['id'] for c in result['fragmentos']}, {'iso'})
        self.assertEqual(result['fragmentos'][0]['pagina'], 13)
