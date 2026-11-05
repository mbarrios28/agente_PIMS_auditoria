from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from reportlab.pdfgen import canvas
from scripts import incorporar_iso
import json

class ISOImportTests(TestCase):
    def test_local_copy_is_indexable_but_not_marked_verified(self):
        with TemporaryDirectory() as folder:
            root=Path(folder);(root/'ISOS').mkdir();(root/'ISOS/fuentes.json').write_text('{}')
            source=root/'test.pdf';c=canvas.Canvas(str(source))
            for i in range(20):c.drawString(40,800-i*20,'Documento sintetico de prueba ISO/IEC 27001:2022. No es una norma real.')
            c.save()
            with patch.object(incorporar_iso,'ROOT',root),patch('sys.argv',['incorporar_iso.py','--norma','27001','--archivo',str(source)]):
                incorporar_iso.main()
            manifest=json.loads((root/'ISOS/fuentes.json').read_text())
            record=manifest['ISO-IEC-27001-2022-aportada.pdf']
            self.assertEqual(record['tipo_fuente'],'norma_aportada')
            self.assertIn('Pendiente',record['verificacion'])
            self.assertEqual(len(record['sha256']),64)
