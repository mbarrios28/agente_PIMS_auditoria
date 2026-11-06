"""Comprueba integridad local y cobertura de la copia aportada, no autenticidad editorial."""
import hashlib
import json
from pathlib import Path
import re

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'ISO-IEC-27701-2025-OCR.pdf'
ANNEXES = {'A': 21, 'B': 27, 'C': 57, 'D': 59, 'E': 62, 'F': 64}


def verify(root=ROOT):
    folder = root / 'ISOS'
    manifest = json.loads((folder / 'fuentes.json').read_text(encoding='utf-8'))
    info = manifest[SOURCE]
    original = info['archivo_original']
    checks = {}
    for name in (original, SOURCE):
        checks['sha256 ' + name] = (
            hashlib.sha256((folder / name).read_bytes()).hexdigest() == manifest[name]['sha256'])
    scan = PdfReader(folder / original)
    reader = PdfReader(folder / SOURCE)
    pages = [p.extract_text() or '' for p in reader.pages]
    checks['72 páginas original y OCR'] = len(scan.pages) == len(pages) == info['paginas'] == 72
    checks['edición 2025'] = '27701:2025' in pages[0] and '2025-10' in pages[0]
    checks['cuerpo completo páginas PDF 7–70'] = (
        len(pages) >= 70 and all(len(p.strip()) > 100 for p in pages[6:70]))
    for letter, page in ANNEXES.items():
        checks['anexo ' + letter] = bool(re.search(r'Annex\s+' + letter + r'\s*\(', pages[page - 1]))
    checks['bibliografía final'] = 'Bibliography' in pages[69]
    checks['única página sin texto: PDF 71'] = [i for i, p in enumerate(pages, 1) if not p.strip()] == [71]
    return dict(correcto=all(checks.values()), comprobaciones=checks,
                alcance='Integridad local y cobertura estructural; no autentica la copia ni corrige errores OCR.')


if __name__ == '__main__':
    result = verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['correcto'] else 1)
