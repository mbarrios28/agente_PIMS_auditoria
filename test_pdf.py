import sys
sys.path.insert(0,'.')
from pypdf import PdfReader
import warnings
warnings.filterwarnings('ignore')

for pdf in ['ISOS/ISO 27701-2025.pdf', 'ISOS/ISO-42001-2023.pdf']:
    r = PdfReader(pdf)
    texto = ""
    for p in r.pages[:10]:
        t = p.extract_text() or ""
        texto += t
    print(f"=== {pdf} ===")
    print(repr(texto[:500]))
    print()
