import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from pypdf import PdfWriter
from reportlab.pdfgen import canvas
from src.priv_audit import rag_loader
from src.priv_audit.agent import RiskAgent

class OCRCorpusTests(TestCase):
    def test_original_is_preserved_and_only_ocr_is_indexed(self):
        with TemporaryDirectory() as folder:
            root=Path(folder);iso=root/'ISOS';iso.mkdir()
            original=iso/'original.pdf';writer=PdfWriter();writer.add_blank_page(612,792)
            with original.open('wb') as f:writer.write(f)
            output=iso/'derived.pdf';c=canvas.Canvas(str(output))
            c.drawString(40,700,'ISO/IEC 27701:2025 Privacy risk assessment');c.save()
            (iso/'fuentes.json').write_text(json.dumps({'original.pdf':{'sustituido_por':'derived.pdf'},'derived.pdf':{'tipo_fuente':'norma_aportada_ocr'}}))
            with patch.object(rag_loader,'ROOT',root):
                chunks,docs=rag_loader._load(rag_loader._signature())
            indexed={d['nombre']:d for d in docs}
            self.assertFalse(indexed['original.pdf']['indexado'])
            self.assertIn('Original conservado',indexed['original.pdf']['aviso'])
            self.assertTrue(indexed['derived.pdf']['indexado'])
            self.assertIn('OCR',indexed['derived.pdf']['aviso'])
            self.assertEqual({c['fuente'] for c in chunks},{'derived.pdf'})
            self.assertEqual(chunks[0]['pagina'],1)
            self.assertEqual(chunks[0]['tipo_fuente'],'norma_aportada_ocr')

    def test_prepare_attaches_normative_evidence_without_manual_context(self):
        chunks=[dict(id='n13',fuente='ISO-IEC-27701-2025-OCR.pdf',pagina=13,texto='6.1.2 Privacy risk assessment',tipo_fuente='norma_aportada_ocr'),
                dict(id='n14',fuente='ISO-IEC-27701-2025-OCR.pdf',pagina=14,texto='consequences for PII principals',tipo_fuente='norma_aportada_ocr')]
        def read(module,page,**kwargs):return dict(modulo=module,pagina=page,total=0,consultado_en='2026-11-05',fragmentos=[])
        agent=RiskAgent();agent.execute('cargar_skill',dict(motivo='Preparar revisión',nombre='gestion_riesgos'))
        with patch('src.priv_audit.gestitel.GestitelClient.read',side_effect=read),patch.object(rag_loader,'cargar_base_conocimiento',return_value=chunks):
            result=agent.execute('preparar_contexto_riesgos',dict(motivo='Recuperar contexto'))
        self.assertEqual([c['id'] for c in result['fragmentos']],['n13','n14'])
        self.assertEqual(agent.evidence['n14']['pagina'],14)
        self.assertEqual(agent.gestitel_reads,3)

    def test_final_reference_retains_ocr_page(self):
        from test_risk import RiskTests
        agent=RiskTests().agent()
        agent.evidence['n14']=dict(id='n14',fuente='norma.pdf',pagina=14,texto='Consequences for PII principals.',tipo_fuente='norma_aportada_ocr')
        item=RiskTests().item();item['referencias'].append('n14')
        agent.execute('finalizar_riesgos',dict(motivo='Entregar propuesta',estado='propuesta',riesgos=[item],limitaciones=['Prueba']))
        citation=agent.result['riesgos'][0]['referencias'][-1]
        self.assertEqual(citation['pagina'],14)
        self.assertEqual(citation['tipo_fuente'],'norma_aportada_ocr')
